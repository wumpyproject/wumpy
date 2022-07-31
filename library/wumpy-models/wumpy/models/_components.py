import dataclasses
from typing import Any, Dict, Optional, Tuple, Union

from discord_typings import (
    ActionRowData, ButtonComponentData, ComponentData, SelectMenuComponentData,
    SelectMenuOptionData, TextInputComponentData
)
from typing_extensions import Literal, Self

from ._emoji import Emoji
from ._utils import backport_slots

__all__ = (
    'ActionRow',
    'Button',
    'LinkButton',
    'SelectMenu',
    'SelectMenuOption',
    'TextInput',
    'component_data',
)


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

    type: Literal[1] = 1

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

    type: Literal[2] = 2

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

    type: Literal[2] = 2
    style: Literal[5] = 5

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

    type: Literal[3] = 3

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

    type: Literal[4] = 4

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


def _select_option_data(option: SelectMenuOption) -> SelectMenuOptionData:
    data: Dict[str, Any] = {
        'label': option.label,
        'value': option.value,
        'default': option.default,
    }

    if option.description is not None:
        data['description'] = option.description

    if option.emoji is not None:
        data['emoji'] = option.emoji

    return data


def component_data(
        component: Union[ActionRow, LinkButton, Button, SelectMenu, TextInput]
) -> ComponentData:
    """Utility function to transform a component model into a dictionary.

    Parameters:
        component: The component to transform into its dictionary data.

    Returns:
        The created dictionary with the data.
    """
    data: Dict[str, Any]

    if component.type == 1:
        data = {
            'type': 1,
            'components': [component_data(item) for item in component.components],
        }

    elif component.type == 2:
        data = {
            'type': 2,
            'style': component.style,
            'disabled': component.disabled,
        }

        if isinstance(component, Button):
            data['custom_id'] = component.custom_id

        if component.emoji is not None:
            data['emoji'] = component.emoji

        if component.label is not None:
            data['label'] = component.label

    elif component.type == 3:
        data = {
            'type': 3,
            'custom_id': component.custom_id,
            'options': [_select_option_data(option) for option in component.options],
            'min_values': component.min_values,
            'max_values': component.max_values,
            'disabled': component.disabled,
        }
    elif component.type == 4:
        data = {
            'type': component.type,
            'style': component.style,
            'custom_id': component.custom_id,
            'label': component.label,
            'min_length': component.min_length,
            'max_length': component.max_length,
            'required': component.required,
        }

        if component.value is not None:
            data['value'] = component.value

        if component.placeholder is not None:
            data['placeholder'] = component.placeholder

    else:
        raise ValueError("Unknown component type of 'component' parameter")

    return data
