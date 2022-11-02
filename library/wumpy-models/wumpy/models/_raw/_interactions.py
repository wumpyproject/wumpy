import enum
from types import MappingProxyType
from typing import Any, List, Optional, Union

import attrs
from discord_typings import (
    ApplicationCommandInteractionData, ApplicationCommandOptionInteractionData, AutocompleteInteractionData,
    ComponentInteractionData, ResolvedInteractionDataData, SelectMenuOptionData
)
from typing_extensions import Self

from .._utils import Model, Snowflake, _get_as_snowflake
from ._channels import InteractionChannel
from ._emoji import RawEmoji
from ._member import RawInteractionMember, RawMember
from ._message import RawMessage
from ._permissions import Permissions
from ._role import RawRole
from ._user import RawUser

__all__ = (
    'InteractionType',
    'ComponentType',
    'ApplicationCommandOption',
    'RawResolvedInteractionData',
    'CommandInteractionOption',
    'RawInteraction',
    'RawAutocompleteInteraction',
    'RawCommandInteraction',
    'RawComponentInteraction',
    'SelectInteractionValue',
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


def _proxy_field():
    """Helper to create a mapping proxy field.

    This function is only used by `ResolvedInteractionData` to simplify the
    code and reduce line-length.

    It is assumed that `attrs` expects each field object to only be used for
    one attribute, therefore this should be called for each attribute.
    """
    return attrs.field(default=MappingProxyType({}), converter=MappingProxyType)


@attrs.define(frozen=True, kw_only=True)
class RawResolvedInteractionData:

    users: 'MappingProxyType[int, RawUser]' = _proxy_field()
    members: 'MappingProxyType[int, RawInteractionMember]' = _proxy_field()

    roles: 'MappingProxyType[int, RawRole]' = _proxy_field()
    channels: 'MappingProxyType[int, InteractionChannel]' = _proxy_field()

    messages: 'MappingProxyType[int, RawMessage]' = _proxy_field()

    @classmethod
    def from_data(cls, data: ResolvedInteractionDataData) -> Self:
        return cls(
            users=MappingProxyType({
                int(k): RawUser.from_data(v) for k, v in data.get('users', {}).items()
            }),
            members=MappingProxyType({
                int(k): RawInteractionMember.from_data(v, data.get('users', {}).get(k))
                for k, v in data.get('members', {}).items()
                if data.get('users', {}).get(k)
            }),

            roles=MappingProxyType({
                int(k): RawRole.from_data(v) for k, v in data.get('roles', {}).items()
            }),
            channels=MappingProxyType({
                int(k): InteractionChannel.from_data(v)
                for k, v in data.get('channels', {}).items()
            }),

            messages=MappingProxyType({
                int(k): RawMessage.from_data(v)
                for k, v in data.get('messages', {}).items()
            }),
        )


@attrs.define(frozen=True)
class CommandInteractionOption:
    """Application Command option received from Discord.

    `value` and `options` are mutually exclusive, the latter is only sent
    when `type` is a subcommand, or subcommand group.
    """

    name: str
    type: ApplicationCommandOption

    value: Optional[Any] = attrs.field(default=None, kw_only=True)

    options: List['CommandInteractionOption'] = attrs.field(factory=list, kw_only=True)
    focused: bool = attrs.field(default=False, kw_only=True)

    @classmethod
    def from_data(cls, data: ApplicationCommandOptionInteractionData) -> Self:
        return cls(
            name=data['name'],
            type=ApplicationCommandOption(data['type']),

            value=data.get('value'),
            focused=data.get('focused', False),
            options=[cls.from_data(option) for option in data.get('options', [])]
        )


@attrs.define(frozen=True)
class SelectInteractionValue:
    """One of the values for a select option."""

    label: str
    value: str
    description: Optional[str] = attrs.field(default=None, kw_only=True)

    emoji: Optional[RawEmoji] = attrs.field(default=None, kw_only=True)
    default: Optional[bool] = attrs.field(default=None, kw_only=True)

    @classmethod
    def from_data(cls, data: SelectMenuOptionData) -> Self:
        emoji = data.get('emoji')
        if emoji is not None:
            emoji = RawEmoji.from_data(emoji)

        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),

            emoji=emoji,
            default=data.get('default')
        )


@attrs.define(eq=False, kw_only=True)
class RawInteraction(Model):
    application_id: Snowflake
    type: InteractionType
    token: str
    version: int = 1

    author: Union[RawUser, RawMember, None] = None
    guild_id: Optional[Snowflake] = None
    channel_id: Optional[Snowflake] = None
    app_permissions: Optional[Permissions] = None


@attrs.define(eq=False, kw_only=True)
class RawAutocompleteInteraction(RawInteraction):

    name: str
    invoked: Snowflake
    invoked_type: ApplicationCommandOption

    author: None
    app_permissions: None

    options: List[CommandInteractionOption]

    @classmethod
    def from_data(cls, data: AutocompleteInteractionData) -> Self:
        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),
            token=data['token'],
            version=data['version'],

            guild_id=_get_as_snowflake(data, 'guild_id'),
            channel_id=_get_as_snowflake(data, 'channel_id'),

            name=data['data']['name'],
            invoked=Snowflake(int(data['data']['id'])),
            invoked_type=ApplicationCommandOption(data['data']['type']),

            options=[
                CommandInteractionOption.from_data(option)
                for option in data['data'].get('options', [])
            ]
        )


@attrs.define(eq=False, kw_only=True)
class RawCommandInteraction(RawInteraction):

    name: str
    invoked: Snowflake
    invoked_type: ApplicationCommandOption

    author: Union[RawUser, RawMember]

    resolved: RawResolvedInteractionData
    target_id: Optional[int] = None
    options: List[CommandInteractionOption]

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

            author = RawMember.from_data(member, user)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = RawUser.from_data(user)

        app_permissions = data.get('app_permissions')
        if app_permissions is not None:
            app_permissions = Permissions(int(app_permissions))

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),
            app_permissions=app_permissions,

            channel_id=_get_as_snowflake(data, 'channel_id'),
            guild_id=_get_as_snowflake(data, 'guild_id'),
            author=author,
            token=data['token'],
            version=data['version'],

            name=data['data']['name'],
            invoked=Snowflake(int(data['data']['id'])),
            invoked_type=ApplicationCommandOption(data['data']['type']),

            resolved=RawResolvedInteractionData.from_data(data['data'].get('resolved', {})),
            target_id=target_id,

            options=[
                CommandInteractionOption.from_data(option)
                for option in data['data'].get('options', [])
            ]
        )


@attrs.define(eq=False, kw_only=True)
class RawComponentInteraction(RawInteraction):

    author: Union[RawUser, RawMember]
    message: RawMessage

    custom_id: str
    component_type: ComponentType

    values: List[SelectInteractionValue]

    @classmethod
    def from_data(cls, data: ComponentInteractionData) -> Self:
        user = data.get('user')

        if 'member' in data:
            member = data['member']
            if user is None:
                user = member.get('user')
            if user is None:
                raise ValueError('Sufficient author information missing from interaction')

            author = RawMember.from_data(member, user)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = RawUser.from_data(user)

        app_permissions = data.get('app_permissions')
        if app_permissions is not None:
            app_permissions = Permissions(int(app_permissions))

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),
            app_permissions=app_permissions,

            channel_id=_get_as_snowflake(data, 'channel_id'),
            guild_id=_get_as_snowflake(data, 'guild_id'),
            author=author,
            token=data['token'],
            version=data['version'],

            message=RawMessage.from_data(data['message']),

            custom_id=data['data']['custom_id'],
            component_type=ComponentType(data['data']['component_type']),

            values=[
                SelectInteractionValue.from_data(value)
                for value in data['data'].get('values', [])
            ]
        )
