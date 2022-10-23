from enum import Enum
from typing import Iterable, Optional, Sequence, SupportsInt, Tuple, Union

import attrs
from discord_typings import (
    AllowedMentionsData, AttachmentData, MessageCreateData, MessageData,
    MessageUpdateData
)
from typing_extensions import Self

from .._utils import Model, Snowflake, _get_as_snowflake
from ._channels import ChannelMention
from ._embed import Embed
from ._emoji import RawMessageReaction
from ._member import RawMember
from ._user import RawUser

__all__ = (
    'AllowedMentions',
    'Attachment',
    'RawMessageMentions',
    'MessageType',
    'RawMessage',
)


class AllowedMentions:
    """Allowed mentions configuration for a message.

    As with all other Wumpy models this is immutable for security reasons. To
    "mutate" the allowed mentions you should create a new instance. Allowed
    mentions objects can be bitwise-OR:d together to create a new object with
    the settings of the right object taking precedence.

    For convenience you can use the `replace()` method which will create an
    object and OR it with the current object to create the final return.

    Parameters:
        everyone: Whether to allow @everyone pings.
        users:
            Whether to allow user-pings. Set to `True` to allow all users,
            `False` to disallow all users, or an iterable of user IDs to
            only allow specific users to be pinged.
        roles:
            Whether to allow role-pings. Set to `True` to allow all roles,
            `False` to disallow all roles, or an iterable of role IDs to
            only allow specific roles to be pinged.
        replied_user: Whether to ping the user in a reply.
    """

    __slots__ = ('_everyone', '_users', '_roles', '_replied_user')

    def __init__(
        self,
        *,
        everyone: Optional[bool] = None,
        users: Union[bool, Iterable[SupportsInt], None] = None,
        roles: Union[bool, Iterable[SupportsInt], None] = None,
        replied_user: Optional[bool] = None,
    ) -> None:
        self._everyone = everyone

        if users is True or users is False or users is None:
            self._users = users
        else:
            self._users = tuple(int(u) for u in users)

        if roles is True or roles is False or roles is None:
            self._roles = roles
        else:
            self._roles = tuple(int(r) for r in roles)

        self._replied_user = replied_user

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            data = other.data()
        elif isinstance(other, dict):
            data = other
        else:
            return NotImplemented

        return self.data() == data

    def __or__(self, other: object) -> Self:
        if not isinstance(other, self.__class__):
            return NotImplemented

        everyone = self._everyone if other._everyone is None else other._everyone
        users = self._users if other._users is None else other._users
        roles = self._roles if other._roles is None else other._roles
        reply = self._replied_user if other._replied_user is None else other._replied_user

        return self.__class__(
            everyone=everyone,
            users=users,
            roles=roles,
            replied_user=reply
        )

    @property
    def everyone(self) -> Optional[bool]:
        return self._everyone

    @property
    def users(self) -> Union[bool, Sequence[int], None]:
        return self._users

    @property
    def roles(self) -> Union[bool, Sequence[int], None]:
        return self._roles

    @property
    def replied_user(self) -> Optional[bool]:
        return self._replied_user

    def data(self) -> AllowedMentionsData:
        data: AllowedMentionsData = {
            'parse': []
        }

        if self._everyone:
            data['parse'].append('everyone')

        if self._users:
            if isinstance(self._users, tuple):
                data['users'] = list(self._users)
            else:
                data['parse'].append('users')

        if self._roles:
            if isinstance(self._roles, tuple):
                data['roles'] = list(self._roles)
            else:
                data['parse'].append('roles')

        if self._replied_user is not None:
            data['replied_user'] = self._replied_user

        return data

    def replace(
        self,
        *,
        everyone: Optional[bool] = None,
        users: Union[bool, Iterable[SupportsInt], None] = None,
        roles: Union[bool, Iterable[SupportsInt], None] = None,
        replied_user: Optional[bool] = None,
    ) -> Self:
        """Replace a particular value, returning a new copy.

        This is the same as creating a new object with those configurations and
        bitwise-ORing it with the current object.

        Parameters:
            everyone: Whether to allow @everyone pings.
            users:
                Whether to allow user-pings. Set to `True` to allow all users,
                `False` to disallow all users, or an iterable of user IDs to
                only allow specific users to be pinged.
            roles:
                Whether to allow role-pings. Set to `True` to allow all roles,
                `False` to disallow all roles, or an iterable of role IDs to
                only allow specific roles to be pinged.
            replied_user: Whether to ping the user in a reply.
        """
        other = self.__class__(
            everyone=everyone,
            users=users,
            roles=roles,
            replied_user=replied_user
        )
        return self | other

    @classmethod
    def none(cls) -> Self:
        return cls(everyone=False, users=False, roles=False, replied_user=False)

    @classmethod
    def all(cls) -> Self:
        return cls(everyone=True, users=True, roles=True, replied_user=True)


@attrs.define(eq=False, kw_only=True)
class Attachment(Model):
    filename: str

    size: int
    url: str
    proxy_url: str

    content_type: Optional[str] = None
    description: Optional[str] = None

    height: Optional[int] = None
    width: Optional[int] = None
    ephemeral: bool = False

    @classmethod
    def from_data(cls, data: AttachmentData) -> Self:
        return cls(
            id=int(data['id']),
            filename=data['filename'],

            size=int(data['size']),
            url=data['url'],
            proxy_url=data['proxy_url'],

            content_type=data.get('content_type'),
            description=data.get('description'),

            height=data.get('height'),
            width=data.get('width'),
            ephemeral=data.get('ephemeral', False)
        )


@attrs.define(frozen=True, kw_only=True)
class RawMessageMentions:
    users: Union[Tuple[RawUser, ...], Tuple[RawMember, ...]] = ()
    channels: Tuple[ChannelMention, ...] = ()
    roles: Tuple[Snowflake, ...] = ()

    @classmethod
    def from_message(
            cls,
            data: Union[MessageData, MessageCreateData, MessageUpdateData]
    ) -> Self:
        if data['mentions'] and 'member' in data['mentions'][0]:
            # Pyright doesn't understand that the type has narrowed down to
            # List[UserMentionData] with the 'member' key.
            users = tuple(RawMember.from_data(m['member'], m) for m in data['mentions'])  # type: ignore
        else:
            users = tuple(RawUser.from_data(u) for u in data['mentions'])

        return cls(
            users=users,
            channels=tuple(
                ChannelMention.from_data(c)
                for c in data.get('mention_channels', [])
            ),
            roles=tuple(Snowflake(int(r)) for r in data['mention_roles']),
        )


class MessageType(Enum):
    default = 0
    recipient_add = 1
    recipient_remove = 2
    call = 3
    channel_name_change = 4
    channel_icon_change = 5
    pins_add = 6
    new_member = 7
    premium_guild_subscription = 8
    premium_guild_tier_1 = 9
    premium_guild_tier_2 = 10
    premium_guild_tier_3 = 11
    channel_follow_add = 12
    guild_discovery_disqualified = 14
    guild_discovery_requalified = 15
    guild_discovery_grace_period_initial_warning = 16
    guild_discovery_grace_period_final_warning = 17
    thread_created = 18
    reply = 19
    application_command = 20
    guild_invite_reminder = 21
    thread_starter_message = 22


@attrs.define(eq=False, kw_only=True)
class RawMessage(Model):
    type: MessageType

    author: Union[RawUser, RawMember]

    channel_id: Snowflake
    guild_id: Optional[Snowflake] = None

    content: str = ''
    tts: bool = False
    attachments: Tuple[Attachment, ...] = ()
    embeds: Tuple[Embed, ...] = ()
    reactions: Tuple[RawMessageReaction, ...] = ()
    mentions: RawMessageMentions = RawMessageMentions()

    pinned: bool = False

    @classmethod
    def from_data(
            cls,
            data: Union[MessageData, MessageCreateData, MessageUpdateData]
    ) -> Self:
        if 'member' in data:
            author = RawMember.from_data(data['member'], data['author'])
        else:
            author = RawUser.from_data(data['author'])

        return cls(
            id=int(data['id']),
            type=MessageType(data['type']),
            author=author,

            channel_id=Snowflake(int(data['channel_id'])),
            guild_id=_get_as_snowflake(data, 'guild_id'),

            content=data['content'],
            tts=data['tts'],
            attachments=tuple(Attachment.from_data(a) for a in data['attachments']),
            embeds=tuple(Embed.from_data(e) for e in data['embeds']),
            reactions=tuple(RawMessageReaction.from_data(r) for r in data.get('reactions', [])),
            mentions=RawMessageMentions.from_message(data),

            pinned=data['pinned'],
        )
