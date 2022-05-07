import dataclasses
import enum
from typing import Any, Dict, List, Optional, Union

from discord_typings import (
    ApplicationCommandInteractionData, ApplicationCommandOptionInteractionData,
    ComponentInteractionData, ResolvedInteractionDataData, SelectMenuOptionData
)
from typing_extensions import Self
from wumpy.models.emoji import Emoji

from .base import Model, Snowflake
from .channels import InteractionChannel
from .member import InteractionMember, Member
from .message import Message
from .role import Role
from .user import User
from .utils import _get_as_snowflake

__all__ = (
    'InteractionType', 'ComponentType', 'ApplicationCommandOption',
    'ResolvedInteractionData', 'CommandInteractionOption', 'Interaction',
    'CommandInteraction', 'ComponentInteraction', 'SelectInteractionValue',
)


class InteractionType(enum.Enum):
    ping = 1
    application_command = 2
    message_component = 3


class ComponentType(enum.Enum):
    action_row = 1
    button = 2
    select_menu = 3
    text_input = 4


class ApplicationCommandOption(enum.Enum):
    subcommand = 1
    subcommand_group = 2
    string = 3
    integer = 4
    boolean = 5
    user = 6
    channel = 7
    role = 8
    mentionable = 9
    number = 10  # Includes decimals


@dataclasses.dataclass(frozen=True)
class ResolvedInteractionData:

    users: Dict[int, User]
    members: Dict[int, InteractionMember]

    roles: Dict[int, Role]
    channels: Dict[int, InteractionChannel]

    messages: Dict[int, Message]

    __slots__ = ('users', 'members', 'roles', 'channels', 'messages')

    @classmethod
    def from_data(cls, data: ResolvedInteractionDataData) -> Self:
        return cls(
            users={int(k): User.from_data(v) for k, v in data.get('users', {}).items()},
            members={
                int(k): InteractionMember.from_data(v, data.get('users', {}).get(k))
                for k, v in data.get('members', {}).items()
                if data.get('users', {}).get(k)
            },

            roles={int(k): Role.from_data(v) for k, v in data.get('roles', {}).items()},
            channels={
                int(k): InteractionChannel.from_data(v)
                for k, v in data.get('channels', {}).items()
            },

            messages={
                int(k): Message.from_data(v)
                for k, v in data.get('messages', {}).items()
            },
        )


@dataclasses.dataclass(frozen=True)
class CommandInteractionOption:
    """Application Command option received from Discord.

    `value` and `options` are mutually exclusive, the latter is only sent
    when `type` is a subcommand, or subcommand group.
    """

    name: str
    type: ApplicationCommandOption

    value: Optional[Any]
    options: List['CommandInteractionOption']

    __slots__ = ('name', 'type', 'value', 'options')

    @classmethod
    def from_data(cls, data: ApplicationCommandOptionInteractionData) -> Self:
        return cls(
            name=data['name'],
            type=ApplicationCommandOption(data['type']),

            value=data.get('value'),
            options=[cls.from_data(option) for option in data.get('options', [])]
        )


@dataclasses.dataclass(frozen=True)
class SelectInteractionValue:
    """One of the values for a select option."""

    label: str
    value: str
    description: Optional[str]

    emoji: Optional[Emoji]
    default: Optional[bool]

    __slots__ = ('label', 'value', 'description', 'emoji', 'default')

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
            default=data.get('default')
        )


@dataclasses.dataclass(frozen=True, eq=False)
class Interaction(Model):

    application_id: Snowflake
    type: InteractionType

    guild_id: Optional[Snowflake]
    channel_id: Optional[Snowflake]

    author: Union[User, Member]
    token: str
    version: int

    __slots__ = (
        'application_id', 'type', 'guild_id', 'channel_id', 'author', 'token', 'version'
    )


@dataclasses.dataclass(frozen=True, eq=False)
class CommandInteraction(Interaction):

    name: str
    invoked: Snowflake
    invoked_type: ApplicationCommandOption

    resolved: ResolvedInteractionData
    target_id: Optional[int]
    options: List[CommandInteractionOption]

    __slots__ = ('name', 'invoked', 'invoked_type', 'resolved', 'target_id', 'options')

    @classmethod
    def from_data(cls, data: ApplicationCommandInteractionData) -> Self:
        target_id = data['data'].get('target_id')
        if target_id is not None:
            target_id = int(target_id)

        user = data.get('user')

        if 'member' in data:
            member = data['member']
            if user is None:
                user = member.get('user')
            if user is None:
                raise ValueError('Sufficient author information missing from interaction')

            author = Member.from_user(User.from_data(user), member)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = User.from_data(user)

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),

            channel_id=_get_as_snowflake(data, 'channel_id'),
            guild_id=_get_as_snowflake(data, 'guild_id'),
            author=author,
            token=data['token'],
            version=data['version'],

            name=data['data']['name'],
            invoked=Snowflake(int(data['data']['id'])),
            invoked_type=ApplicationCommandOption(data['data']['type']),

            resolved=ResolvedInteractionData.from_data(data['data'].get('resolved', {})),
            target_id=target_id,

            options=[
                CommandInteractionOption.from_data(option)
                for option in data['data'].get('options', [])
            ]
        )


@dataclasses.dataclass(frozen=True, eq=False)
class ComponentInteraction(Interaction):

    message: Message

    custom_id: str
    component_type: ComponentType

    values: List[SelectInteractionValue]

    __slots__ = ('message', 'custom_id', 'component_type', 'values')

    @classmethod
    def from_data(cls, data: ComponentInteractionData) -> Self:
        user = data.get('user')

        if 'member' in data:
            member = data['member']
            if user is None:
                user = member.get('user')
            if user is None:
                raise ValueError('Sufficient author information missing from interaction')

            author = Member.from_user(User.from_data(user), member)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = User.from_data(user)

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),

            channel_id=_get_as_snowflake(data, 'channel_id'),
            guild_id=_get_as_snowflake(data, 'guild_id'),
            author=author,
            token=data['token'],
            version=data['version'],

            message=Message.from_data(data['message']),

            custom_id=data['data']['custom_id'],
            component_type=ComponentType(data['data']['component_type']),

            values=[
                SelectInteractionValue.from_data(value)
                for value in data['data'].get('values', [])
            ]
        )
