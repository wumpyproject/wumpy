import enum
from types import MappingProxyType
from typing import Any, List, Optional, Union

import attrs
from discord_typings import (
    ApplicationCommandInteractionData, ComponentInteractionData,
    ResolvedInteractionDataData
)
from typing_extensions import Self

from .._raw import (
    ApplicationCommandOption, ComponentType, InteractionChannel,
    InteractionType, Permissions, RawAutocompleteInteraction,
    RawCommandInteraction, RawComponentInteraction, RawInteraction,
    SelectInteractionValue
)
from .._utils import Snowflake, _get_as_snowflake
from . import _member, _message, _role, _user


def _proxy_field():
    """Helper to create a mapping proxy field.

    This function is only used by `ResolvedInteractionData` to simplify the
    code and reduce line-length.

    It is assumed that `attrs` expects each field object to only be used for
    one attribute, therefore this should be called for each attribute.
    """
    return attrs.field(default=MappingProxyType({}), converter=MappingProxyType)


@attrs.define(frozen=True, kw_only=True)
class ResolvedInteractionData:

    users: 'MappingProxyType[int, _user.User]' = _proxy_field()
    members: 'MappingProxyType[int, _member.InteractionMember]' = _proxy_field()

    roles: 'MappingProxyType[int, _role.Role]' = _proxy_field()
    channels: 'MappingProxyType[int, InteractionChannel]' = _proxy_field()

    messages: 'MappingProxyType[int, _message.Message]' = _proxy_field()

    @classmethod
    def from_data(cls, data: ResolvedInteractionDataData) -> Self:
        return cls(
            users=MappingProxyType({
                int(k): _user.User.from_data(v) for k, v in data.get('users', {}).items()
            }),
            members=MappingProxyType({
                int(k): _member.InteractionMember.from_data(v, data.get('users', {}).get(k))
                for k, v in data.get('members', {}).items()
                if data.get('users', {}).get(k)
            }),

            roles=MappingProxyType({
                int(k): _role.Role.from_data(v) for k, v in data.get('roles', {}).items()
            }),
            channels=MappingProxyType({
                int(k): InteractionChannel.from_data(v)
                for k, v in data.get('channels', {}).items()
            }),

            messages=MappingProxyType({
                int(k): _message.Message.from_data(v)
                for k, v in data.get('messages', {}).items()
            }),
        )


@attrs.define(eq=False, kw_only=True)
class Interaction(RawInteraction):
    author: Union['_user.User', '_member.Member', None]


@attrs.define(eq=False)
class AutocompleteInteraction(RawAutocompleteInteraction, Interaction):
    ...


@attrs.define(eq=False, kw_only=True)
class CommandInteraction(RawCommandInteraction, Interaction):
    author: Union['_user.User', '_member.Member']

    resolved: ResolvedInteractionData


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

            author = _member.Member.from_data(member, user)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = _user.User.from_data(user)

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

            resolved=ResolvedInteractionData.from_data(data['data'].get('resolved', {})),
            target_id=target_id,

            options=[
                CommandInteractionOption.from_data(option)
                for option in data['data'].get('options', [])
            ]
        )


@attrs.define(eq=False, kw_only=True)
class ComponentInteraction(RawComponentInteraction, Interaction):

    author: Union['_user.User', '_member.Member']
    message: '_message.Message'

    @classmethod
    def from_data(cls, data: ComponentInteractionData) -> Self:
        user = data.get('user')

        if 'member' in data:
            member = data['member']
            if user is None:
                user = member.get('user')
            if user is None:
                raise ValueError('Sufficient author information missing from interaction')

            author = _member.Member.from_data(member, user)
        elif user is None:
            raise ValueError('Author information missing from interaction')
        else:
            author = _user.User.from_data(user)

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

            message=_message.Message.from_data(data['message']),

            custom_id=data['data']['custom_id'],
            component_type=ComponentType(data['data']['component_type']),

            values=[
                SelectInteractionValue.from_data(value)
                for value in data['data'].get('values', [])
            ]
        )
