import inspect
from enum import Enum
from typing import (
    Any, AnyStr, Callable, ClassVar, Dict, List, Optional, Tuple, Type,
    TypeVar, Union
)

from typing_extensions import Annotated, Literal, get_args, get_origin
from wumpy.models import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption,
    InteractionChannel, InteractionMember, User
)

from .._errors import CommandSetupError
from . import _slash  # Circular dependency

__all__ = (
    'CommandType',
    'Option',
    'option',
    'OptionClass'
)


T = TypeVar('T', bound='_slash.Command')


class CommandType(Enum):
    chat_input = 1
    user = 2
    message = 3


class OptionType:
    """Base class for all option types.

    Instances of this class hold no special behaviour and the value is just
    passed through.

    Attributes:
        enum: The ApplicationCommandOption value of this type.
    """

    enum: ApplicationCommandOption

    __slots__ = ('enum',)

    def __init__(self, enum: ApplicationCommandOption) -> None:
        self.enum = enum

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ApplicationCommandOption):
            return self.enum == other
        elif isinstance(other, self.__class__):
            return self.enum == other.enum

        return False


class MemberUserUnion(OptionType):
    """Option type marker for Union[InteractionUser, InteractionMember].

    This is used to mark special behaviour that will first attempt to grab the
    member object, if not found it will grab the user object.
    """

    enum = ApplicationCommandOption.user

    __slots__ = ()

    def __init__(self) -> None:
        return


class FloatType(OptionType):
    """Strict float type.

    This is because Discord's equivalent `number` type includes both integers
    and floats, which can cause unexpected user behaviour when just `float` is
    used.
    """

    enum = ApplicationCommandOption.number

    __slots__ = ()

    def __init__(self) -> None:
        return


# This is sentinel value used for one particular purpose - the option default
#    @(lambda cls: cls())
#    class _MISSING_DEFAULT:
#        pass
class _MISSING_DEFAULT_TYPE:
    pass


_MISSING_DEFAULT = _MISSING_DEFAULT_TYPE()
del _MISSING_DEFAULT_TYPE


# The reason for this function is because we need the "return type" to be Any.
# If we'd use the class directly then the following would break type checking
# def command(number: int = Option(description='A number'))
# 'int' and 'Option' is incompatible. This function avoids that
def Option(
    default: Any = _MISSING_DEFAULT,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    required: Optional[bool] = None,
    choices: Union[List[Union[str, int, float]], Dict[str, Union[str, int, float]], None] = None,
    min: Optional[int] = None,
    max: Optional[int] = None,
    type: Optional[Any] = None,
    cls: Optional[Type[Any]] = None
) -> Any:
    """Interaction option, should be set as a default to a parameter.

    The `cls` parameter can be used if you want to use a custom Option
    class, you can use `functools.partial()` as to not repeat the kwarg.

    Parameters:
        default:
            Default value when the option is not passed, makes the option
            optional so that it can be omitted.
        name:
            Name of the option in the Discord client. By default it uses
            the name of the parameter.
        description: Description of the option.
        required:
            Whether the option can be omitted. If a default is passed this is
            automatically set implicitly.
        choices: Set choices that the user can pick from in the Discord client.
        min: Smallest number that can be entered for number types.
        max: Biggest number that can be entered for number types.
        type:
            The type of the option, overriding the annotation. This can be
            a `ApplicationCommandOption` value or any type.
        cls: The class to use, defaults to `OptionClass`.

    Returns:
        The `cls` parameter (`OptionClass` by default) disguised as
        `typing.Any`. This way this function can be used as a default without
        violating static type checkers.
    """
    return (cls or OptionClass)(
        default, name=name, description=description,
        required=required, choices=choices,
        min=min, max=max, type=type
    )


# This is different from the above function as this is a decorator meant
# to be used on command instances.
def option(
    param: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    required: Optional[bool] = None,
    choices: Union[List[Union[str, int, float]], Dict[str, Union[str, int, float]], None] = None,
    min: Optional[int] = None,
    max: Optional[int] = None,
    type: Optional[Any] = None
) -> Callable[[T], T]:
    """Option decorator for updating an option.

    This decorator needs to be placed outside of the command decorator.

    Parameters:
        param: The name of the parameter for this option.
        name: The new name of the option.
        description: The new description of the option.
        required: Whether the option should be able to be omitted.
        choices: Set choices that the user needs to pick from.
        min: Smallest number that can be entered for number types.
        max: Biggest number that can be entered for number types.
        type: New type of the option, overriding the annotation.

    Exceptions:
        ValueError: This decorator was not used on a command.
    """
    # Because of the fact that we delete the type variable below, it won't be
    # available when this function is created.
    def decorator(command: 'T') -> 'T':
        if not isinstance(command, _slash.Command):
            raise TypeError(
                "The 'option' decorator can only be used on commands."
            )

        command.update_option(
            param, name=name, description=description,
            required=required, choices=choices, min=min, max=max, type=type
        )

        # Return the command again for chaining.
        return command
    return decorator


class OptionClass:
    """A user-constructed option to an application command.

    For most cases the `Option` helper function should be used.

    Attributes:
        type: Application command option type to send to Discord.
        name: The name of the option in the Discord client.
        description: A description of the option.
        required: Whether the option can be omitted.
        choices: Strict choices that the user can pick from.
        min: Smallest number that can be entered for number types
        max: Biggest number that can be entered for number types
        default: Default the library will use when the option is omitted.
        converter: Simple callable mainly used for enums.
        param: The name of the parameter in the callback.
        kind: The kind of the parameter in the callback.
        type_mapping:
            Mapping of primitive types (ie. `int`, `str`) to the application
            command option type it will get. This is looked up by
            `determine_type()` when the parameter annotation is read.
    """

    type: Optional[OptionType]

    name: Optional[str]
    description: Optional[str]
    required: Optional[bool]
    choices: Optional[Dict[str, Union[str, int, float]]]  # Name of the choice to the value

    min: Optional[int]
    max: Optional[int]

    default: Any
    converter: Optional[Any]  # Simple callable, used for enums to convert the argument

    param: Optional[str]
    kind: Optional[inspect._ParameterKind]

    __slots__ = (
        'default', 'name', 'description', 'required',
        'choices', 'type', 'converter', 'param', 'kind',
        'min', 'max'
    )

    # Mapping of primitive types to their equivalent ApplicationCommandOption
    # enum values, placed in the class so that it can be overwritten.
    type_mapping: ClassVar[Dict[Type[Any], ApplicationCommandOption]] = {
        str: ApplicationCommandOption.string,
        int: ApplicationCommandOption.integer,
        bool: ApplicationCommandOption.boolean,
        float: ApplicationCommandOption.number,
        User: ApplicationCommandOption.user,
        InteractionChannel: ApplicationCommandOption.channel,
        InteractionMember: ApplicationCommandOption.user,
    }

    def __init__(
        self,
        default: Any = _MISSING_DEFAULT,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        # This isn't very readable, but it means a list or dictionary of
        # strings, integers or floats.
        choices: Union[List[Union[str, int, float]], Dict[str, Union[str, int, float]], None] = None,
        min: Optional[int] = None,
        max: Optional[int] = None,
        type: Optional[Any] = None
    ) -> None:
        self.name = name
        self.description = description

        if default is not _MISSING_DEFAULT and required is None:
            # If required hasn't been set and there's a default we
            # should assume the user wants the option to be optional
            required = False

        self.required = required

        if isinstance(choices, list):
            choices = {str(value): value for value in choices}

        self.choices = choices

        self.min = min
        self.max = max

        self.default = default
        self.converter = None

        self.param = None
        self.kind = None
        self.type = None

        if type is not None:
            self.determine_type(type)

    @property
    def has_default(self) -> bool:
        """Whether the option has a default value.

        This is used to determine whether the `default` attribute can be
        correctly interpreted as the default value.
        """
        return self.default is not _MISSING_DEFAULT

    def determine_union(self, args: Tuple[Any, ...]) -> bool:
        """Determine the option type for a union.

        This is called by `determine_type` when it receives a union type
        because of the extra logic involved.

        Args:
            args: The arguments that the Union was given.

        Returns:
            Whether the method could determine a type from the union.
        """
        # Optional[X] becomes Union[X, NoneType]. Flake8 thinks we should use
        # isinstance() but that won't work (hence the noqa)
        if len(args) == 2 and args[-1] == type(None):  # noqa: E721
            self.required = False if self.required is None else self.required

            # Find the typing of X in Optional[X]
            return self.determine_type(args[0])

        elif len(args) == 2 and int in args and float in args:
            # A union with int and float can just be interpreted as a float
            # because a float doesn't need decimals.
            self.type = OptionType(ApplicationCommandOption.number)
            return True

        elif len(args) == 2 and User in args and InteractionMember in args:
            self.type = MemberUserUnion()
            return True

        return False

    def determine_type(self, annotation: Any) -> bool:
        """Determine the application command option type from an annotation.

        This method is exposed for the purpose of extending it with advanced
        custom behaviour. For simpler cases the `type_mapping` class variable
        can be overriden with more values.

        Args:
            annotation: The annotation of the parameter.

        Returns:
            Whether an application command type was able to be determined.
        """
        if isinstance(annotation, ApplicationCommandOption):
            self.type = OptionType(annotation)
            return True

        try:
            self.type = OptionType(self.type_mapping[annotation])
            return True
        except KeyError:
            # It wasn't a primitive type we have in the mapping, continue down
            # and try resolving the type
            pass

        if isinstance(annotation, type) and issubclass(annotation, Enum):
            # If the enum is a subclass of another type, such as an IntEnum we
            # can infer the type from that.
            if self.type is None:
                for primitive in self.type_mapping:
                    if not issubclass(annotation, primitive):
                        continue

                    # The enum is a subclass of some other type
                    self.determine_type(primitive)

            # We can use an enum's members as choices.
            if self.choices is None:
                self.converter = annotation
                self.choices = {name: val.value for name, val in annotation.__members__.items()}

            return True

        elif annotation is AnyStr:  # Simple alias
            return self.determine_type(str)

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is Union:
            # The union type has a lot of different and special behaviour
            # that has been seperated into another method for readability.
            return self.determine_union(args)

        elif origin is Annotated:
            # Attempt to convert each argument until it is successful,
            # excluding the first argument (which is meant for editors).
            return any(self.determine_type(attempt) for attempt in args[1:])

        elif origin is Literal and args:  # Make sure it isn't empty
            if self.type is None:
                type_ = type(args[0])
                for value in args:
                    if not isinstance(value, type_):
                        raise TypeError(
                            f"Literal contains mixed types; expected '{type_}' not '{type(value)}'"
                        )

                self.determine_type(type_)

            if self.choices is None:
                # Discord wants a name and a value, for Literal we simply have
                # to use the arguments for both
                self.choices = {str(value): value for value in args}

            return True

        return False

    def update(self, param: inspect.Parameter) -> None:
        """Update the option with new information about the parameter.

        The class has no idea about the parameter it is being defined in so it
        has to be made aware by the library after the fact. This is called when
        the command is being created.

        Args:
            param: The parameter that this instance was defined in.
        """
        self.param = param.name

        # Generally the Option instance has priority, unless it is MISSING
        self.name = param.name if self.name is None else self.name

        if param.default is not param.empty and not isinstance(param.default, self.__class__):
            # If the parameter has a default other than an Option class we can
            # use it for the option default
            self.default = param.default if self.default is _MISSING_DEFAULT else self.default
            self.required = False if self.required is None else self.required

        self.kind = param.kind

        if param.annotation is not param.empty and self.type is None:
            self.determine_type(param.annotation)

    def _update_values(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        choices: Union[
            List[Union[str, int, float]],
            Dict[str, Union[str, int, float]],
            None
        ] = None,
        min: Optional[int] = None,
        max: Optional[int] = None,
        type: Any = None
    ) -> None:
        """Update internal values of the option.

        This is different from `update()`, which is only meant to let the
        OptionClass instance aware of the parameter is has been defined in.
        """

        if type is not None:
            self.determine_type(type)

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if required is not None:
            self.required = required

        if choices is not None:
            if isinstance(choices, list):
                choices = {str(value): value for value in choices}

            self.choices = choices

        if min is not None:
            self.min = min

        if max is not None:
            self.max = max

    def resolve(
        self,
        interaction: CommandInteraction,
        data: Optional[CommandInteractionOption]
    ) -> Any:
        """Resolve the value to pass to the callback.

        The value that this returns is passed directly to the callback in the
        option's place.

        Args:
            interaction: The interaction received from Discord.
            data: The option received from Discord or None if it wasn't passed.

        Returns:
            The resolved value from the interaction and option.

        Exceptions:
            CommandSetupError: There is no data and a default is missing.
            CommandSetupError: The data is of an unexpected type.
            CommandSetupError: The data failed to be converted to an enum.
        """
        if data is None:
            if self.default is None:
                raise CommandSetupError(
                    f"Missing data for option '{self.param}' of command '{interaction.name}'"
                )

            return self.default

        assert self.type is not None

        if data.type is not self.type.enum:
            raise CommandSetupError(
                f"'{self.param}' of '{interaction.name}' received option with wrong type"
            )

        value = data.value

        if value is None:
            raise CommandSetupError(
                f"Expected command option value for '{self.param}' of '{interaction.name}'"
            )

        if self.converter is not None:
            try:
                value = self.converter(value)
            except Exception as exc:
                raise CommandSetupError('Could not convert argument:', value) from exc

        if isinstance(self.type, FloatType):
            # We need to make sure it really is a float
            value = float(value)

        # Some options only pass IDs because Discord asynchronously resolves
        # the data for them, these are then passed in a special `resolved`
        # field that we need to look them up by.
        elif isinstance(self.type, MemberUserUnion):
            # This has some special behaviour, we want to attempt to first get
            # a member and fall back to a user.
            resolved = interaction.resolved.members.get(int(value))
            if not resolved:
                resolved = interaction.resolved.users.get(int(value))

            value = resolved

        elif self.type.enum is ApplicationCommandOption.user:
            value = interaction.resolved.users.get(int(value))
        elif self.type.enum is ApplicationCommandOption.channel:
            value = interaction.resolved.channels.get(int(value))
        elif self.type is ApplicationCommandOption.user:
            value = interaction.resolved.members.get(int(value))

        # At this point `value` may be None from our lookups of the resolved
        # data
        if value is None:
            raise CommandSetupError(
                "Didn't receive resolved data for command '{interaction.name}'"
            )

        return value

    def to_dict(self) -> Dict[str, Any]:
        """Turn the option into a dictionary to send to Discord."""
        if self.name is None or self.type is None or self.description is None:
            raise CommandSetupError('Missing required option values')

        data = {
            'name': self.name,
            'type': self.type.enum.value,
            'description': self.description,
            'required': True if self.required is None else self.required,
        }

        if self.choices is not None:
            # We store choices with the name as the key and value being the
            # value but Discord expects a payload with explicit name and value
            # keys so we need to convert it.
            choices = [{'name': k, 'value': v} for k, v in self.choices.items()]
            data['choices'] = choices

        if self.min is not None:
            data['min_value'] = self.min

        if self.max is not None:
            data['max_value'] = self.max

        return data
