from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, overload

if TYPE_CHECKING:
    from ..base import MessageComponentInteraction


class ButtonStyle(Enum):
    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5


class Button:
    """Interactive message component that can be clicked by users."""

    style: ButtonStyle
    label: Optional[str]

    custom_id: Optional[str]
    url: Optional[str]

    disabled: bool

    callback: Optional[Callable[['MessageComponentInteraction'], Awaitable[None]]]

    __slots__ = ('style', 'label', 'custom_id', 'url', 'disabled', 'callback')

    @overload
    def __init__(
        self,
        *,
        style: ButtonStyle,
        custom_id: str,
        label: Optional[str] = None,
        # emoji: ... = ...,
        disabled: bool = False
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        style: ButtonStyle,
        url: str,
        label: Optional[str] = None,
        # emoji: ... = ...,
        disabled: bool = False
    ) -> None:
        ...

    def __init__(
        self,
        *,
        style: ButtonStyle,
        label: Optional[str] = None,
        # emoji: ... = ...,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        disabled: bool = False,
        callback: Optional[Callable[['MessageComponentInteraction'], Awaitable[None]]] = None
    ) -> None:
        if custom_id is not None and url is not None:
            raise TypeError("cannot pass 'custom_id' and 'url' at the same time")

        self.style = style
        self.label = label
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled

        self.callback = callback

    def handle_interaction(self, interaction: 'MessageComponentInteraction', *, tg) -> None:
        if self.callback is not None:
            tg.start_soon(self.callback, interaction)

    def to_json(self) -> Dict[str, Any]:
        data = {
            'type': 2,
            'style': self.style.value,
            'label': self.label,
            'custom_id': self.custom_id,
            'url': self.url,
            'disabled': self.disabled
        }
        # We should clean it for None
        return {k: v for k, v in data.items() if v is not None}
