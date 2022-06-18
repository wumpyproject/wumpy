import dataclasses
from typing import Optional, Tuple, Union

from discord_typings import (
    ActionRowData, ButtonComponentData, ComponentData, SelectMenuComponentData,
    SelectMenuOptionData, TextInputComponentData
)
from typing_extensions import Literal, Self

from .emoji import Emoji
from .utils import backport_slots

__all__ = ['Button', 'LinkButton', 'SelectMenu', 'SelectMenuOption']


def _create_component(
        data: ComponentData
) -> Union['Button', 'LinkButton', 'SelectMenu', 'TextInput']:
    if data['type'] == 2:
        if data['style'] == 5:
            return LinkButton.from_data(data)
        else:
            return Button.from_data(data)
    elif data['type'] == 3:
        return SelectMenu.from_data(data)
    elif data['type'] == 4:
        return TextInput.from_data(data)

    raise ValueError(f"Unknown component type {data['type']} for data: {data}")


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ActionRow:
    components: Tuple[Union['Button', 'LinkButton', 'SelectMenu', 'TextInput'], ...]

    type = 1

    @classmethod
    def from_data(cls, data: ActionRowData) -> Self:
        return cls(
            tuple(_create_component(component) for component in data['components'])
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class Button:

    style: Literal[1, 2, 3, 4]

    custom_id: str

    emoji: Optional[Emoji] = None
    label: Optional[str] = None

    disabled: bool = False

    type = 2

    @classmethod
    def from_data(cls, data: ButtonComponentData) -> Self:
        if data['style'] == 5:
            raise ValueError('Cannot create Button from link button data')

        emoji = data.get('emoji')
        if emoji is not None:
            emoji = Emoji.from_data(emoji)

        return cls(
            style=data['style'],
            custom_id=data['custom_id'],

            emoji=emoji,
            label=data.get('label'),
            disabled=data.get('disabled', False),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class LinkButton:

    url: str

    emoji: Optional[Emoji] = None
    label: Optional[str] = None

    disabled: bool = False

    type = 2
    style = 5

    @classmethod
    def from_data(cls, data: ButtonComponentData) -> Self:
        if data['style'] != 5:
            raise ValueError('Non-link button style in data for link button')

        emoji = data.get('emoji')
        if emoji is not None:
            emoji = Emoji.from_data(emoji)

        return cls(
            url=data['url'],
            emoji=emoji,
            label=data.get('label'),
            disabled=data.get('disabled', False),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class SelectMenu:

    custom_id: str
    options: Tuple['SelectMenuOption', ...]

    placeholder: Optional[str] = None
    min_values: int = 1
    max_values: int = 1

    disabled: bool = False

    type = 3

    @classmethod
    def from_data(cls, data: SelectMenuComponentData) -> Self:
        return cls(
            custom_id=data['custom_id'],
            options=tuple(
                SelectMenuOption.from_data(d) for d in data['options']
            ),

            placeholder=data.get('placeholder'),
            min_values=data.get('min_values', 1),
            max_values=data.get('max_values', 1),
            disabled=data.get('disabled', False),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class SelectMenuOption:
    label: str
    value: str

    description: Optional[str] = None
    emoji: Optional[Emoji] = None

    default: bool = False

    @classmethod
    def from_data(cls, data: SelectMenuOptionData) -> Self:
        emoji = data.get('emoji')
        if emoji is not None:
            emoji = Emoji.from_data(emoji)

        return cls(
            label=data['label'],
            value=data['value'],

            description=data.get('description'),
            emoji=emoji,

            default=data.get('default', False),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class TextInput:

    style: Literal[1, 2]
    custom_id: str
    label: str

    min_length: int = 0
    max_length: int = 4000

    required: bool = True
    value: Optional[str] = None
    placeholder: Optional[str] = None

    type = 4

    @classmethod
    def from_data(cls, data: TextInputComponentData) -> Self:
        return cls(
            style=data['style'],
            custom_id=data['custom_id'],
            label=data['label'],

            min_length=data.get('min_length', 0),
            max_length=data.get('max_length', 4000),

            required=data.get('required', True),
            value=data.get('value'),
            placeholder=data.get('placeholder'),
        )
