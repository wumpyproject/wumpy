from enum import Enum
from typing import (
    TYPE_CHECKING, Any, Callable, Coroutine, Dict, Optional, Union, overload
)

from .component import Component, ComponentEmoji

if TYPE_CHECKING:
    from wumpy.models import ComponentInteraction


__all__ = ('ButtonStyle', 'Button')


class ButtonStyle(Enum):
    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5


class Button(Component):
    """Interactive message component that can be clicked by users.

    Attributes:
        style: The style and appearance of the button.
        label: The label displayed to the user.
        emoji: Emoji displayed next to the label.
        custom_id: Unique custom ID for this button
        url:
            URL to open when the user presses the button, this cannot be used
            together with a custom ID.
        disabled: Whether the button should appear greyed out for the user.
    """

    style: ButtonStyle
    label: Optional[str]
    emoji: Optional[ComponentEmoji]

    custom_id: Optional[str]
    url: Optional[str]

    disabled: bool

    __slots__ = ('style', 'label', 'emoji', 'custom_id', 'url', 'disabled')

    @overload
    def __init__(
        self,
        *,
        style: ButtonStyle,
        custom_id: str,
        label: Optional[str] = None,
        emoji: Optional[Union[ComponentEmoji, str]] = None,
        disabled: bool = False,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        url: str,
        label: Optional[str] = None,
        emoji: Optional[Union[ComponentEmoji, str]] = None,
        disabled: bool = False
    ) -> None:
        ...

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.link,
        label: Optional[str] = None,
        emoji: Optional[Union[ComponentEmoji, str]] = None,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        disabled: bool = False,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None
    ) -> None:
        super().__init__(callback=callback)

        if custom_id is not None and url is not None:
            raise TypeError("cannot pass 'custom_id' and 'url' at the same time")

        elif style is ButtonStyle.link and custom_id is not None:
            raise TypeError("__init__() missing keyword-only argument: 'style'")

        elif style is not ButtonStyle.link and url is not None:
            raise ValueError('Only link buttons can be link button styled')

        self.style = style
        self.label = label

        if isinstance(emoji, str):
            emoji = ComponentEmoji.from_string(emoji)

        self.emoji = emoji

        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled

    def to_dict(self) -> Dict[str, Any]:
        """Turn the button into a dict that can be serialized to JSON."""
        data = {
            'type': 2,
            'style': self.style.value,
            'label': self.label,
            # `self.emoji` may be None, and None doesn't have a to_dict() method
            'emoji': self.emoji.to_dict() if self.emoji else None,
            'custom_id': self.custom_id,
            'url': self.url,
            'disabled': self.disabled
        }
        # We should clean it for None values
        return {k: v for k, v in data.items() if v is not None}
