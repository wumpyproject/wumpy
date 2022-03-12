import dataclasses

from discord_typings import (
    ApplicationCommandInteractionData, ComponentInteractionData
)
from typing_extensions import Self
from wumpy.models import ApplicationCommandOption
from wumpy.models import CommandInteraction as CommandInteractionModel
from wumpy.models import CommandInteractionOption
from wumpy.models import ComponentInteraction as ComponentInteractionModel
from wumpy.models import ComponentType
from wumpy.models import Interaction as InteractionModel
from wumpy.models import (
    InteractionType, Member, Message, ResolvedInteractionData,
    SelectInteractionValue, Snowflake, User
)

from .compat import Request

# This is a subclass of the wumpy.models representations for interactions that
# use the Request classes to make the responses.


@dataclasses.dataclass(frozen=True, eq=False)
class Interaction(InteractionModel):
    _request: Request

    async def respond(
        self,
        content: str,
    ) -> None:
        await self._request.respond({
            'type': 4,
            'data': {
                'content': content
            }
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

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),

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

        return cls(
            id=int(data['id']),
            application_id=Snowflake(int(data['application_id'])),
            type=InteractionType(data['type']),

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
        content: str,
    ) -> None:
        await self._request.respond({
            'type': 7,
            'data': {
                'content': content
            }
        })
