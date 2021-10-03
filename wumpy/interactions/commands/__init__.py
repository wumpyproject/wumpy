from typing import Any, Dict, Type, Union

from ...utils import MISSING
from . import option as __option
from .base import *
from .context import *
from .registrar import *
from .slash import *


# The reason for this function is because we need the "return type" to be Any.
# If we'd use the class directly then the following would break type checking
# def command(number: int = Option(description='A number'))
# 'int' and 'Option' is incompatible. This function avoids that
def Option(
    default: Any = MISSING,
    *,
    name: str = MISSING,
    description: str = MISSING,
    required: bool = MISSING,
    choices: Dict[str, Union[str, int, float]] = MISSING,
    type: Type[Any] = MISSING,
    cls: Type[Any] = __option.OptionClass
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
        type:
            The type of the option, overriding the annotation. This can be
            a `ApplicationCommandOption` value or any type.
        cls: The class to use, defaults to `OptionClass`.

    Returns:
        The `cls` parameter (`OptionClass` by default) disguised as
        `typing.Any`. This way this function can be used as a default without
        violating static type checkers.
    """
    return cls(
        default, name=name, description=description,
        required=required, choices=choices, type=type
    )


# Clean up as we don't want users importing these from here
del Any, Dict, Type, Union
del MISSING, __option
