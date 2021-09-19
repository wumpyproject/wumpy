from typing import (
    TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, Dict, List, Optional,
    Union
)

from .component import Component, ComponentEmoji

if TYPE_CHECKING:
    from ..base import ComponentInteraction


class SelectOption:
    """Option for an interactive select menu."""

    label: str
    value: str
    description: Optional[str]
    emoji: Optional[ComponentEmoji]
    default: bool

    def __init__(
        self,
        *,
        label: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[Union[ComponentEmoji, str]] = None,
        default: bool = False
    ) -> None:
        self.label = label
        self.value = value or label

        if isinstance(emoji, str):
            emoji = ComponentEmoji.from_string(emoji)

        self.emoji = emoji
        self.description = description
        self.default = default

    def to_json(self) -> Dict[str, Any]:
        data = {
            'label': self.label,
            'value': self.value,
            'description': self.description,
            'emoji': self.emoji.to_dict() if self.emoji else None,
            'default': self.default
        }
        return {k: v for k, v in data.items() if v is not None}


class SelectMenu(Component):
    """Interactive drop-down select menu on messages."""

    options: List[SelectOption]
    custom_id: str
    placeholder: Optional[str]

    min: int
    max: int

    disabled: bool

    def __init__(
        self,
        options: Union[List[SelectOption], List[str]],
        *,
        custom_id: str,
        placeholder: Optional[str] = None,
        min: int = 1,
        max: int = 1,
        disabled: bool = False,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None
    ) -> None:
        super().__init__(callback)

        self.options = [SelectOption(label=option) if isinstance(option, str)
                        else option for option in options]

        self.custom_id = custom_id
        self.placeholder = placeholder

        self.min = min
        self.max = max

        self.disabled = disabled

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'type': 3,
            'custom_id': self.custom_id,
            'options': [option.to_json() for option in self.options],
            'placeholder': self.placeholder,
            'min_values': self.min,
            'max_values': self.max,
            'disabled': self.disabled
        }
        return {k: v for k, v in data.items() if v is not None}
