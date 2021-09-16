from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List, Optional, Union

if TYPE_CHECKING:
    from ..base import MessageComponentInteraction


class SelectOption:
    """Option for an interactive select menu."""

    label: str
    value: str
    description: Optional[str]
    # emoji: ...
    default: bool

    def __init__(
        self,
        *,
        label: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        # emoji: ... = ...,
        default: bool = False
    ) -> None:
        self.label = label
        self.value = value or label

        self.description = description
        self.default = default

    def to_json(self) -> Dict[str, Any]:
        data = {
            'label': self.label,
            'value': self.value,
            'description': self.description,
            'default': self.default
        }
        return {k: v for k, v in data.items() if v is not None}


class SelectMenu:
    """Interactive drop-down select menu on messages."""

    options: List[SelectOption]
    custom_id: str
    placeholder: Optional[str]

    min: int
    max: int

    disabled: bool

    callback: Optional[Callable[['MessageComponentInteraction'], Awaitable[None]]]

    def __init__(
        self,
        options: Union[List[SelectOption], List[str]],
        *,
        custom_id: str,
        placeholder: Optional[str] = None,
        min: int = 1,
        max: int = 1,
        disabled: bool = False,
        callback: Optional[Callable[['MessageComponentInteraction'], Awaitable[None]]] = None
    ) -> None:
        self.options = [SelectOption(label=option) if isinstance(option, str)
                        else option for option in options]

        self.custom_id = custom_id
        self.placeholder = placeholder

        self.min = min
        self.max = max

        self.disabled = disabled

        self.callback = callback

    def handle_interaction(self, interaction: 'MessageComponentInteraction', *, tg) -> None:
        if self.callback is not None:
            tg.start_soon(self.callback, interaction)

    def to_json(self) -> Dict[str, Any]:
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
