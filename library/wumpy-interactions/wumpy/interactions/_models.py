import dataclasses
from typing import Sequence

from discord_typings import (
    ApplicationCommandInteractionData, ComponentInteractionData
)
from typing_extensions import Self
from wumpy.models import (
    ActionRow, AllowedMentions, ApplicationCommandOption,
    CommandInteraction as CommandInteractionModel, CommandInteractionOption,
    ComponentInteraction as ComponentInteractionModel, ComponentType, Embed,
    Interaction as InteractionModel, InteractionType, Member, Message,
    Permissions, ResolvedInteractionData, SelectInteractionValue, Snowflake,
    User, component_data, embed_data
)
from wumpy.rest import MISSING

from ._compat import Request

__all__ = (
    'Interaction',
    'CommandInteraction',
    'ComponentInteraction',
)

# This is a subclass of the wumpy.models representations for interactions that
# use the Request classes to make the responses.


@dataclasses.dataclass(frozen=True, eq=False)
class Interaction(InteractionModel):
    _request: Request

    async def respond(
        self,
        content: str = MISSING,
        *,
        tts: bool = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        components: Sequence[ActionRow] = MISSING,
        ephemeral: bool = MISSING,
    ) -> None:
        data = {
            'content': content,
            'tts': tts,
        }

        if embeds is not MISSING:
            data['embeds'] = [embed_data(emb) for emb in embeds]

        if allowed_mentions is not MISSING:
            data['allowed_mentions'] = allowed_mentions.data()

        if components is not MISSING:
            data['components'] = [component_data(comp) for comp in components]

        if ephemeral is True:
            data['flags'] = 1 << 6

        await self._request.respond({
            'type': 4,
            'data': {k: v for k, v in data.items() if v is not MISSING}
        })

    async def defer(self) -> None:
        await self._request.respond({'type': 5})


@dataclasses.dataclass(frozen=True, eq=False)
class CommandInteraction(CommandInteractionModel, Interaction):

    @classmethod
    def from_data(cls, data: ApplicationCommandInteractionData, request: Request) -> Self:
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

        channel_id = data.get('channel_id')
        if channel_id is not None:
            channel_id = Snowflake(int(channel_id))

        guild_id = data.get('guild_id')
        if guild_id is not None:
            guild_id = Snowflake(int(guild_id))

        app_permissions = data.get('app_permissions')
        if app_permissions is not None:
            app_permissions = Permissions(int(app_permissions))

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),
            app_permissions=app_permissions,

            channel_id=channel_id,
            guild_id=guild_id,
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
            ],

            _request=request
        )


@dataclasses.dataclass(frozen=True, eq=False)
class ComponentInteraction(ComponentInteractionModel, Interaction):

    @classmethod
    def from_data(cls, data: ComponentInteractionData, request: Request) -> Self:
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

        channel_id = data.get('channel_id')
        if channel_id is not None:
            channel_id = Snowflake(int(channel_id))

        guild_id = data.get('guild_id')
        if guild_id is not None:
            guild_id = Snowflake(int(guild_id))

        app_permissions = data.get('app_permissions')
        if app_permissions is not None:
            app_permissions = Permissions(int(app_permissions))

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),
            app_permissions=app_permissions,

            channel_id=channel_id,
            guild_id=guild_id,
            author=author,
            token=data['token'],
            version=data['version'],

            message=Message.from_data(data['message']),

            custom_id=data['data']['custom_id'],
            component_type=ComponentType(data['data']['component_type']),

            values=[
                SelectInteractionValue.from_data(value)
                for value in data['data'].get('values', [])
            ],

            _request=request
        )

    async def defer_update(self) -> None:
        await self._request.respond({'type': 6})

    async def update(
        self,
        content: str = MISSING,
        *,
        tts: bool = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        components: Sequence[ActionRow] = MISSING,
        ephemeral: bool = MISSING,
    ) -> None:
        data = {
            'content': content,
            'tts': tts,
        }

        if embeds is not MISSING:
            data['embeds'] = [embed_data(emb) for emb in embeds]

        if allowed_mentions is not MISSING:
            data['allowed_mentions'] = allowed_mentions.data()

        if components is not MISSING:
            data['components'] = [component_data(comp) for comp in components]

        if ephemeral is True:
            data['flags'] = 1 << 6

        await self._request.respond({
            'type': 7,
            'data': {k: v for k, v in data.items() if v is not MISSING}
        })
