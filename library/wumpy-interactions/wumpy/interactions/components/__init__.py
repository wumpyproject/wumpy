from typing import TYPE_CHECKING, Callable, Coroutine, Optional, Union

from .button import *
from .component import *
from .containers import *
from .handler import *
from .select import *

if TYPE_CHECKING:
    from wumpy.models import ComponentInteraction


def button(
    *,
    style: ButtonStyle,
    custom_id: str,
    label: Optional[str] = None,
    emoji: Optional[Union[ComponentEmoji, str]] = None,
    disabled: bool = False,
) -> Callable[[Callable[['ComponentInteraction'], Coroutine]], Button]:
    """Decorator that creates a Button from a function.

    The Button instance's callback will be setup to use the decorated function.

    Examples:

        ```python
        @button(
            style=ButtonStyle.primary, custom_id='PRESSME',
            label='Press me!', emoji='🖱'
        )
        async def callback(interaction: ComponentInteraction) -> None:
            await interaction.respond('*click*')  # Very satisfying click
        ```

    Parameters:
        style: The style of the button
        custom_id: The custom ID of the button, needs to be unique
        label: The label to display to the user
        emoji: An optional emoji next to the label
        disabled:
            Whether the button will be greyed out and unabled to be pressed for
            the user

    Returns:
        Function that will create a Button from the received callback, this
        means that this decorator needs to be called with parenthesis.
    """
    def inner(callback: Callable[['ComponentInteraction'], Coroutine]) -> Button:
        return Button(
            style=style,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            callback=callback
        )

    return inner


# Clean up so that it can't be imported
del TYPE_CHECKING, Callable, Coroutine, Optional, Union  # type: ignore
