import inspect
from enum import Enum
from typing import (
    Any, AnyStr, ClassVar, Dict, List, Literal, Optional, Type, Union,
    get_args, get_origin
)

from typing_extensions import Annotated

from ...errors import CommandSetupError
from ...utils import MISSING
from ..base import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption
)

__all__ = ('CommandType', 'OptionClass')


class CommandType(Enum):
    chat_input = 1
    user = 2
    message = 3


class OptionClass:
    """A user-constructed option to an application command.

    For most cases the `Option` helper function should be used.

    The OptionClass uses the `MISSING` sentinel for missing values. This can be
    tricky to work with and in general users should not play around with this
    class unless it is for the purpose of extending it.

    Attributes:
        type: Application command option type to send to Discord.
        name: The name of the option in the Discord client.
        description: A description of the option.
        required: Whether the option can be omitted.
        choices: Strict choices that the user can pick from.
        default: Default the library will use when the option is omitted.
        converter: Simple callable mainly used for enums.
        param: The name of the parameter in the callback.
        kind: The kind of the parameter in the callback.
        type_mapping:
            Mapping of primitive types (ie. `int`, `str`) to the application
            command option type it will get. This is looked up by
            `determine_type()` when the parameter annotation is read.
    """

    type: ApplicationCommandOption

    name: str
    description: str
    required: bool
    choices: Dict[str, Union[str, int, float]]  # Name of the choice to the value

    default: Any
    converter: Any  # Simple callable, used for enums to convert the argument

    param: str
    kind: inspect._ParameterKind

    __slots__ = (
        'default', 'name', 'description', 'required',
        'choices', 'type', 'converter', 'param', 'kind'
    )

    # Mapping of primitive types to their equivalent ApplicationCommandOption
    # enum values, placed in the class so that it can be overwritten.
    type_mapping: ClassVar[Dict[Type, ApplicationCommandOption]] = {
        str: ApplicationCommandOption.string,
        int: ApplicationCommandOption.integer,
        bool: ApplicationCommandOption.boolean,
        float: ApplicationCommandOption.number,
    }

    def __init__(
        self,
        default: Any = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
        required: bool = True,
        # This isn't very readable, but it means a list or dictionary of
        # strings, integers or floats.
        choices: Union[List[Union[str, int, float]], Dict[str, Union[str, int, float]]] = MISSING,
        type: Type[Any] = MISSING
    ) -> None:
        self.name = name
        self.description = description

        if default is not MISSING and required is MISSING:
            # If required hasn't been set and there's a default we
            # should assume the user wants the option to be optional
            required = False

        self.required = True if required is MISSING else required

        if isinstance(choices, list):
            choices = {str(value): value for value in choices}

        self.choices = choices

        self.default = default
        self.converter = MISSING

        self.param = MISSING
        self.kind = MISSING
        self.type = MISSING

        if type is not MISSING:
            self.determine_type(type)

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
            self.type = annotation
            return True

        try:
            self.type = self.type_mapping[annotation]
            return True
        except KeyError:
            # It wasn't a primitive type we have in the mapping, continue down
            # and try resolving the type
            pass

        if issubclass(annotation, Enum):
            # If the enum is a subclass of another type, such as an IntEnum we
            # can infer the type from that.
            if self.type is MISSING:
                for primitive in self.type_mapping:
                    if not issubclass(annotation, primitive):
                        continue

                    self.type = self.type_mapping[primitive]
                    break

            # We can use an enum's members as choices.
            if self.choices is MISSING:
                self.converter = annotation
                self.choices = {name: val.value for name, val in annotation.__members__.items()}

            return True

        elif annotation is AnyStr:  # Simple alias
            return self.determine_type(str)

        origin = get_origin(annotation)
        args = get_args(annotation)

        # Optional[X] becomes Union[X, NoneType]. Flake8 thinks we should use
        # isinstance() but that won't work (hence the noqa)
        if origin is Union and len(args) == 2 and args[-1] == type(None):  # noqa: E721
            self.required = False if self.required is MISSING else self.required

            # Find the typing of X in Optional[X]
            return self.determine_type(args[0])

        elif origin is Annotated:
            # Attempt to convert each argument until it is successful,
            # excluding the first argument (which is meant for editors).
            return any(self.determine_type(attempt) for attempt in args[1:])

        elif origin is Literal and self.choices is MISSING:
            # Discord wants a name and a value, for Literal we simply have to
            # use the arguments for both
            self.choices = {str(value): value for value in args}
            return True

        # This does not yet handle ForwardRefs, because it requires eval() with
        # locals() and globals() of the function
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
        self.name = param.name if self.name is MISSING else self.name

        if param.default is not param.empty and not isinstance(param.default, self.__class__):
            # If the parameter has a default other than an Option class we can
            # use it for the option default
            self.default = param.default if self.default is MISSING else self.default
            self.required = False if self.required is MISSING else self.required

        self.kind = param.kind

        if param.annotation is not param.empty and self.type is MISSING:
            self.determine_type(param.annotation)

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
            CommandSetupError:
                There is no data and there is no default or the data is of the
                wrong option type.
        """
        if data is None:
            if self.default is MISSING:
                raise CommandSetupError(
                    "Missing data for option '{self.param}' of command '{interaction.name}'"
                )

            return self.default

        if data.type is not self.type:
            raise CommandSetupError(
                f"'{self.param}' of '{interaction.name}' received option with wrong type"
            )

        value = data.value
        if self.converter is not MISSING:
            try:
                value = self.converter(value)
            except Exception as exc:
                raise CommandSetupError('Could not convert argument:', value) from exc

        return value

    def to_dict(self) -> Dict[str, Any]:
        """Turn the option into a dictionary to send to Discord."""
        data = {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'required': self.required,
        }

        if self.choices is not MISSING:
            # We store choices with the name as the key and value being the
            # value but Discord expects a payload with explicit name and value
            # keys so we need to convert it.
            choices = [{'name': k, 'value': v} for k, v in self.choices.items()]
            data['choices'] = choices

        return data
