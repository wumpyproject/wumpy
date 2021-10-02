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
    class, you can use `functools.partial()` as to not repeat the option.
    """
    return cls(
        default, name=name, description=description,
        required=required, choices=choices, type=type
    )


# Clean up as we don't want users importing these from here
del Any, Dict, Type, Union
del MISSING, __option
