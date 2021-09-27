import inspect
from enum import Enum
from typing import (
    Annotated, Any, AnyStr, Dict, Literal, Type, Union, get_args, get_origin
)

from ...errors import CommandSetupError
from ...utils import MISSING
from ..base import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption
)


class CommandType(Enum):
    chat_input = 1
    user = 2
    message = 3


class OptionClass:
    """A user-constructed option to an application command.

    Although it is user-constructed it isn't meant to be used by users because
    of quirks with attributes being the MISSING sentinel.

    This is inspected by the library as a default to a command parameter.
    There is also a decorator on a command that can be used if preferred.
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
    type_mapping = {
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
        required: bool = MISSING,
        choices: Dict[str, Union[str, int, float]] = MISSING,
        type: Type[Any] = MISSING
    ) -> None:
        self.name = name
        self.description = description

        if default is not MISSING and required is MISSING:
            # If required hasn't been set and there's a default we
            # should assume the user wants the option to be optional
            required = False

        self.required = required
        self.choices = choices

        self.default = default
        self.converter = MISSING

        self.param = MISSING
        self.kind = MISSING
        self.type = MISSING

        if type is not MISSING:
            self.determine_type(type)

    def determine_type(self, annotation: Any) -> bool:
        """Determine the Discord API type for the explicit type or annotation.

        By having this in the Option itself, it's very easy for a user to
        override this method if need-be for custom behaviour.

        This should modify the Option instance in-place.
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
            # Grab the last item, with normal usage this should be the 2nd item
            return self.determine_type(args[-1])

        elif origin is Literal and self.choices is MISSING:
            # Discord wants a name and a value, for Literal we simply have to
            # use the arguments for both
            self.choices = {value: value for value in args}
            return True

        # This does not yet handle ForwardRefs, because it requires eval() with
        # locals() and globals() of the function
        return False

    def update(self, param: inspect.Parameter) -> None:
        """Update with new information from the parameter it was defined in.

        We don't know anything about the parameter when the Option class is
        initialized so this is used to later update values.
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

    async def resolve(self, interaction: CommandInteraction, data: CommandInteractionOption) -> Any:
        """Resolve a value from Discord option data."""
        if data.type is not self.type:
            raise CommandSetupError(f'Received option with wrong type, expected {self.type}')

        return data.value

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'required': self.required,
        }

        if self.choices is not MISSING:
            data['choices'] = self.choices

        return data
