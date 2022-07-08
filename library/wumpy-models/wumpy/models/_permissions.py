import dataclasses
from enum import Enum
from typing import Any, Callable, Optional, SupportsInt, Union, overload

from discord_typings import PermissionOverwriteData
from typing_extensions import Self

from ._base import Model
from ._flags import DiscordFlags, flag
from ._utils import backport_slots

__all__ = (
    'Permissions',
    'PermissionTarget',
    'PermissionOverwrite',
)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class Permissions(DiscordFlags):
    """A bitfield for wrapping Discord permissions."""

    @overload
    @classmethod
    def build(  # type: ignore  # @overload *should* have multiple signatures
        cls,
        *,
        create_instant_invite: bool = ...,
        kick_members: bool = ...,
        ban_members: bool = ...,
        administrator: bool = ...,
        manage_channels: bool = ...,
        manage_guild: bool = ...,
        add_reactions: bool = ...,
        view_audit_log: bool = ...,
        priority_speaker: bool = ...,
        stream: bool = ...,
        view_channel: bool = ...,
        send_messages: bool = ...,
        send_tts_messages: bool = ...,
        manage_messages: bool = ...,
        embed_links: bool = ...,
        attach_files: bool = ...,
        read_message_history: bool = ...,
        mention_everyone: bool = ...,
        use_external_emojis: bool = ...,
        view_guild_insights: bool = ...,
        connect: bool = ...,
        speak: bool = ...,
        mute_members: bool = ...,
        deafen_members: bool = ...,
        move_members: bool = ...,
        use_voice_activity: bool = ...,
        change_nickname: bool = ...,
        manage_nicknames: bool = ...,
        manage_roles: bool = ...,
        manage_webhooks: bool = ...,
        manage_emojis_and_stickers: bool = ...,
        use_application_commands: bool = ...,
        request_to_speak: bool = ...,
        manage_events: bool = ...,
        manage_threads: bool = ...,
        create_public_threads: bool = ...,
        create_private_threads: bool = ...,
        send_messages_in_threads: bool = ...,
        use_external_stickers: bool = ...,
        use_embedded_activities: bool = ...,
        moderate_members: bool = ...,
    ) -> Self:
        ...

    @classmethod
    def build(cls, **kwargs: bool) -> Self:
        perms = 0

        for option, value in [(k, v) for (k, v) in kwargs.items() if isinstance(v, bool)]:
            flag = getattr(cls, option)
            if value is True:
                perms |= flag

        return cls(perms)

    @overload
    def replace(  # type: ignore  # @overload *should* have multiple signatures
        self,
        *,
        create_instant_invite: bool = ...,
        kick_members: bool = ...,
        ban_members: bool = ...,
        administrator: bool = ...,
        manage_channels: bool = ...,
        manage_guild: bool = ...,
        add_reactions: bool = ...,
        view_audit_log: bool = ...,
        priority_speaker: bool = ...,
        stream: bool = ...,
        view_channel: bool = ...,
        send_messages: bool = ...,
        send_tts_messages: bool = ...,
        manage_messages: bool = ...,
        embed_links: bool = ...,
        attach_files: bool = ...,
        read_message_history: bool = ...,
        mention_everyone: bool = ...,
        use_external_emojis: bool = ...,
        view_guild_insights: bool = ...,
        connect: bool = ...,
        speak: bool = ...,
        mute_members: bool = ...,
        deafen_members: bool = ...,
        move_members: bool = ...,
        use_voice_activity: bool = ...,
        change_nickname: bool = ...,
        manage_nicknames: bool = ...,
        manage_roles: bool = ...,
        manage_webhooks: bool = ...,
        manage_emojis_and_stickers: bool = ...,
        use_application_commands: bool = ...,
        request_to_speak: bool = ...,
        manage_events: bool = ...,
        manage_threads: bool = ...,
        create_public_threads: bool = ...,
        create_private_threads: bool = ...,
        send_messages_in_threads: bool = ...,
        use_external_stickers: bool = ...,
        use_embedded_activities: bool = ...,
        moderate_members: bool = ...,
    ) -> Self:
        ...

    def replace(self, **kwargs: bool) -> Self:
        cls = self.__class__
        perms = self.value

        for option, value in [(k, v) for (k, v) in kwargs.items() if isinstance(v, bool)]:
            flag = getattr(cls, option)
            if value is True:
                perms |= flag
            else:
                perms &= ~flag

        return cls(perms)

    @flag
    def create_instant_invite() -> int:
        """Whether the permission allows creating instant invites."""
        return 1 << 0

    @flag
    def kick_members() -> int:
        """Whether the permission allows kicking members from the guild."""
        return 1 << 1

    @flag
    def ban_members() -> int:
        """Whether the permission allows banning members from the guild."""
        return 1 << 2

    @flag
    def administrator() -> int:
        """Whether the permisson gives the user administrator permissions.

        An administrator gets all other permissions, and
        channel-specific overrides do not apply.
        """
        return 1 << 3

    @flag
    def manage_channels() -> int:
        """Whether the permission allows managing channels."""
        return 1 << 4

    @flag
    def manage_guild() -> int:
        """Whether the permission allows managing guild settings."""
        return 1 << 5

    @flag
    def add_reactions() -> int:
        """Whether the permission allows adding new reactions to a message."""
        return 1 << 6

    @flag
    def view_audit_log() -> int:
        """Whether the permission allows viewing the audit log entries."""
        return 1 << 7

    @flag
    def priority_speaker() -> int:
        """Whether the permission allows using priority speaker in a voice channel."""
        return 1 << 8

    @flag
    def stream() -> int:
        """Whether the permission allows streaming in voice channels."""
        return 1 << 9

    @flag
    def view_channel() -> int:
        """Whether the permission allows viewing the channel."""
        return 1 << 10

    @flag
    def send_messages() -> int:
        """Whether the permission allows sending messages in that channel."""
        return 1 << 11

    @flag
    def send_tts_messages() -> int:
        """Whether the permission allows sending text-to-speech messages."""
        return 1 << 12

    @flag
    def manage_messages() -> int:
        """Whether the permission allows managing messages."""
        return 1 << 13

    @flag
    def embed_links() -> int:
        """Whether the permission allows embedding links."""
        return 1 << 14

    @flag
    def attach_files() -> int:
        """Whether the permission allows attaching files to messages."""
        return 1 << 15

    @flag
    def read_message_history() -> int:
        """Whether the permission allows reading the message history."""
        return 1 << 16

    @flag
    def mention_everyone() -> int:
        """Whether the permission allows mentioning @everyone and @here roles.

        Members with this permission can mention roles with
        "Allow anyone to @mention this role" disabled.
        """
        return 1 << 17

    @flag
    def use_external_emojis() -> int:
        """Whether the permission allows sending external emojis."""
        return 1 << 18

    @flag
    def view_guild_insights() -> int:
        """Whether the permission allows viewing guild insights."""
        return 1 << 19

    @flag
    def connect() -> int:
        """Whether the permission allows connecting to voice channels."""
        return 1 << 20

    @flag
    def speak() -> int:
        """Whether the permission allows speaking in voice channels."""
        return 1 << 21

    @flag
    def mute_members() -> int:
        """Whether the permission allows server muting members."""
        return 1 << 22

    @flag
    def deafen_members() -> int:
        """Whether the permission allows server deafening members."""
        return 1 << 23

    @flag
    def move_members() -> int:
        """Whether the permission allows moving members to different voice channels."""
        return 1 << 24

    @flag
    def use_voice_activity() -> int:
        """Whether the permission allows using voice activity detection."""
        return 1 << 25

    @flag
    def change_nickname() -> int:
        """Whether the permission allows changing own nickname."""
        return 1 << 26

    @flag
    def manage_nicknames() -> int:
        """Whether the permission allows managing others' nicknames."""
        return 1 << 27

    @flag
    def manage_roles() -> int:
        """Whether the permission allows managing roles and permissions."""
        return 1 << 28

    @flag
    def manage_webhooks() -> int:
        """Whether the permission allows managing webhooks and integrations."""
        return 1 << 29

    @flag
    def manage_emojis_and_stickers() -> int:
        """Whether the permission allows managing emojis and stickers."""
        return 1 << 30

    @flag
    def use_application_commands() -> int:
        """Whether the permission allows using slash commands."""
        return 1 << 31

    @flag
    def request_to_speak() -> int:
        """Whether the permission allows requesting to speak in stage channels."""
        return 1 << 32

    @flag
    def manage_events() -> int:
        """Whether the permission allows managing scheduled events."""
        return 1 << 33

    @flag
    def manage_threads() -> int:
        """Whether the permission allows managing threads."""
        return 1 << 34

    @flag
    def create_public_threads() -> int:
        """Whether the permission allows creating in public threads."""
        return 1 << 35

    @flag
    def create_private_threads() -> int:
        """Whether the permission allows creating private threads."""
        return 1 << 36

    @flag
    def use_external_stickers() -> int:
        """Whether the permission allows using external stickers."""
        return 1 << 37

    @flag
    def send_messages_in_threads() -> int:
        """Whether the permission allows participating in threads."""
        return 1 << 38

    @flag
    def use_embedded_activities() -> int:
        """Whether the permission allows using embedded activities."""
        return 1 << 39

    @flag
    def moderate_members() -> int:
        """Whether the permission allows timing out other members."""
        return 1 << 40


@backport_slots(weakref_slot=False)
@dataclasses.dataclass(frozen=True)
class TriBitMask:
    """Representing one bit of two bitfields similar to BitMask.

    This has the potential to return None if neither the `allow` or `deny`
    bits are set.
    """

    mask: int

    def __get__(self, instance: 'PermissionOverwrite', _: Optional[type]) -> Union[bool, None, int]:
        if instance is None:
            return self.mask

        if (instance.allow & self.mask) == self.mask:
            return True
        elif (instance.deny & self.mask) == self.mask:
            return False
        else:
            return None


def triflag(func: Callable[[], int]) -> TriBitMask:
    """The equivalent of the normal `flag` decorator, but for TriBitMask."""
    return TriBitMask(func())


class PermissionTarget(Enum):
    role = 0
    member = 1


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class PermissionOverwrite(Model):
    """"Discord permission overwrite object.

    Compared to many other Wumpy models, this one will often be initialized
    by users and as such a special `from_data()` classmethod is used by the
    library.
    """

    allow: Permissions
    deny: Permissions
    type: Optional[PermissionTarget] = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.id == other.id and self.allow == other.allow and self.deny == other.deny

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.id != other.id or self.allow != other.allow or self.deny != other.deny

    @classmethod
    def from_data(cls, data: PermissionOverwriteData) -> Self:
        return cls(
            id=int(data['id']),
            type=PermissionTarget(int(data['type'])),
            allow=Permissions(int(data['allow'])),
            deny=Permissions(int(data['deny'])),
        )

    @overload
    @classmethod
    def build(  # type: ignore  # @overload *should* have multiple signatures
        cls,
        id: SupportsInt,
        type: PermissionTarget,
        *,
        # This is a copy of each permission of a permission overwrite, since
        # you can build a permission with any of those options.
        create_instant_invite: Optional[bool] = ...,
        kick_members: Optional[bool] = ...,
        ban_members: Optional[bool] = ...,
        administrator: Optional[bool] = ...,
        manage_channels: Optional[bool] = ...,
        manage_guild: Optional[bool] = ...,
        add_reactions: Optional[bool] = ...,
        view_audit_log: Optional[bool] = ...,
        priority_speaker: Optional[bool] = ...,
        stream: Optional[bool] = ...,
        view_channel: Optional[bool] = ...,
        send_messages: Optional[bool] = ...,
        send_tts_messages: Optional[bool] = ...,
        manage_messages: Optional[bool] = ...,
        embed_links: Optional[bool] = ...,
        attach_files: Optional[bool] = ...,
        read_message_history: Optional[bool] = ...,
        mention_everyone: Optional[bool] = ...,
        use_external_emojis: Optional[bool] = ...,
        view_guild_insights: Optional[bool] = ...,
        connect: Optional[bool] = ...,
        speak: Optional[bool] = ...,
        mute_members: Optional[bool] = ...,
        deafen_members: Optional[bool] = ...,
        move_members: Optional[bool] = ...,
        use_voice_activity: Optional[bool] = ...,
        change_nickname: Optional[bool] = ...,
        manage_nicknames: Optional[bool] = ...,
        manage_roles: Optional[bool] = ...,
        manage_webhooks: Optional[bool] = ...,
        manage_emojis_and_stickers: Optional[bool] = ...,
        use_application_commands: Optional[bool] = ...,
        request_to_speak: Optional[bool] = ...,
        manage_events: Optional[bool] = ...,
        manage_threads: Optional[bool] = ...,
        create_public_threads: Optional[bool] = ...,
        create_private_threads: Optional[bool] = ...,
        use_external_stickers: Optional[bool] = ...,
        send_messages_in_threads: Optional[bool] = ...,
        use_embedded_activities: Optional[bool] = ...,
        moderate_members: Optional[bool] = ...,
    ) -> Self:
        ...

    @classmethod
    def build(cls, id: SupportsInt, type: PermissionTarget, **kwargs: Optional[bool]) -> Self:
        allow, deny = 0, 0

        for option, value in [(k, v) for (k, v) in kwargs.items() if isinstance(v, bool)]:
            flag = getattr(cls, option)
            if value is True:
                allow |= flag
                deny &= ~flag
            else:
                allow &= ~flag
                deny |= flag

        return cls(
            id=int(id),
            type=type,
            allow=Permissions(allow),
            deny=Permissions(deny),
        )

    @overload
    def replace(  # type: ignore  # @overload *should* have multiple signatures
        self,
        *,
        # This is a copy of each permission of a permission overwrite, since
        # you can build a permission
        create_instant_invite: Optional[bool] = ...,
        kick_members: Optional[bool] = ...,
        ban_members: Optional[bool] = ...,
        administrator: Optional[bool] = ...,
        manage_channels: Optional[bool] = ...,
        manage_guild: Optional[bool] = ...,
        add_reactions: Optional[bool] = ...,
        view_audit_log: Optional[bool] = ...,
        priority_speaker: Optional[bool] = ...,
        stream: Optional[bool] = ...,
        view_channel: Optional[bool] = ...,
        send_messages: Optional[bool] = ...,
        send_tts_messages: Optional[bool] = ...,
        manage_messages: Optional[bool] = ...,
        embed_links: Optional[bool] = ...,
        attach_files: Optional[bool] = ...,
        read_message_history: Optional[bool] = ...,
        mention_everyone: Optional[bool] = ...,
        use_external_emojis: Optional[bool] = ...,
        view_guild_insights: Optional[bool] = ...,
        connect: Optional[bool] = ...,
        speak: Optional[bool] = ...,
        mute_members: Optional[bool] = ...,
        deafen_members: Optional[bool] = ...,
        move_members: Optional[bool] = ...,
        use_voice_activity: Optional[bool] = ...,
        change_nickname: Optional[bool] = ...,
        manage_nicknames: Optional[bool] = ...,
        manage_roles: Optional[bool] = ...,
        manage_webhooks: Optional[bool] = ...,
        manage_emojis_and_stickers: Optional[bool] = ...,
        use_application_commands: Optional[bool] = ...,
        request_to_speak: Optional[bool] = ...,
        manage_events: Optional[bool] = ...,
        manage_threads: Optional[bool] = ...,
        create_public_threads: Optional[bool] = ...,
        create_private_threads: Optional[bool] = ...,
        use_external_stickers: Optional[bool] = ...,
        send_messages_in_threads: Optional[bool] = ...,
        use_embedded_activities: Optional[bool] = ...,
        moderate_members: Optional[bool] = ...,
    ) -> Self:
        ...

    def replace(self, **kwargs: Optional[bool]) -> Self:
        cls = self.__class__
        allow, deny = self.allow.value, self.deny.value

        for option, value in kwargs.items():
            flag = getattr(cls, option)
            if value is True:
                allow |= flag
                deny &= ~flag
            elif value is False:
                allow &= ~flag
                deny |= flag
            else:
                allow &= ~flag
                deny &= ~flag

        return cls(
            id=self.id,
            type=self.type,
            allow=Permissions(allow),
            deny=Permissions(deny),
        )

    # As painful as it may be, it is necessary to play nice with documentation
    # and auto-completion. This is a copy from the Permissions class above,
    # with the decorator changed to be the tribool version.

    @triflag
    def create_instant_invite() -> int:
        """Whether the permission allows creating instant invites."""
        return 1 << 0

    @triflag
    def kick_members() -> int:
        """Whether the permission allows kicking members from the guild."""
        return 1 << 1

    @triflag
    def ban_members() -> int:
        """Whether the permission allows banning members from the guild."""
        return 1 << 2

    @triflag
    def administrator() -> int:
        """Whether the permisson gives the user administrator permissions.

        An administrator gets all other permissions, and
        channel-specific overrides do not apply.
        """
        return 1 << 3

    @triflag
    def manage_channels() -> int:
        """Whether the permission allows managing channels."""
        return 1 << 4

    @triflag
    def manage_guild() -> int:
        """Whether the permission allows managing guild settings."""
        return 1 << 5

    @triflag
    def add_reactions() -> int:
        """Whether the permission allows adding new reactions to a message."""
        return 1 << 6

    @triflag
    def view_audit_log() -> int:
        """Whether the permission allows viewing the audit log entries."""
        return 1 << 7

    @triflag
    def priority_speaker() -> int:
        """Whether the permission allows using priority speaker in a voce channel."""
        return 1 << 8

    @triflag
    def stream() -> int:
        """Whether the permission allows streaming in voice channels."""
        return 1 << 9

    @triflag
    def view_channel() -> int:
        """Whether the permission allows viewing the channel."""
        return 1 << 10

    @triflag
    def send_messages() -> int:
        """Whether the permission allows sending messages in that channel."""
        return 1 << 11

    @triflag
    def send_tts_messages() -> int:
        """Whether the permission allows sending text-to-speech messages."""
        return 1 << 12

    @triflag
    def manage_messages() -> int:
        """Whether the permission allows managing messages."""
        return 1 << 13

    @triflag
    def embed_links() -> int:
        """Whether the permission allows embedding links."""
        return 1 << 14

    @triflag
    def attach_files() -> int:
        """Whether the permission allows attaching files to messages."""
        return 1 << 15

    @triflag
    def read_message_history() -> int:
        """Whether the permission allows reading the message history."""
        return 1 << 16

    @triflag
    def mention_everyone() -> int:
        """Whether the permission allows mentioning @everyone and @here roles.

        Members with this permission can mention roles with
        "Allow anyone to @mention this role" disabled.
        """
        return 1 << 17

    @triflag
    def use_external_emojis() -> int:
        """Whether the permission allows sending external emojis."""
        return 1 << 18

    @triflag
    def view_guild_insights() -> int:
        """Whether the permission allows viewing guild insights."""
        return 1 << 19

    @triflag
    def connect() -> int:
        """Whether the permission allows connecting to voice channels."""
        return 1 << 20

    @triflag
    def speak() -> int:
        """Whether the permission allows speaking in voice channels."""
        return 1 << 21

    @triflag
    def mute_members() -> int:
        """Whether the permission allows server muting members."""
        return 1 << 22

    @triflag
    def deafen_members() -> int:
        """Whether the permission allows server deafening members."""
        return 1 << 23

    @triflag
    def move_members() -> int:
        """Whether the permission allows moving members to different voice channels."""
        return 1 << 24

    @triflag
    def use_voice_activity() -> int:
        """Whether the permission allows using voice activity."""
        return 1 << 25

    @triflag
    def change_nickname() -> int:
        """Whether the permission allows changing own nickname."""
        return 1 << 26

    @triflag
    def manage_nicknames() -> int:
        """Whether the permission allows managing others' nicknames."""
        return 1 << 27

    @triflag
    def manage_roles() -> int:
        """Whether the permission allows managing roles and permissions."""
        return 1 << 28

    @triflag
    def manage_webhooks() -> int:
        """Whether the permission allows managing webhooks and integrations."""
        return 1 << 29

    @triflag
    def manage_emojis_and_stickers() -> int:
        """Whether the permission allows managing emojis and stickers."""
        return 1 << 30

    @triflag
    def use_application_commands() -> int:
        """Whether the permission allows using slash commands."""
        return 1 << 31

    @triflag
    def request_to_speak() -> int:
        """Whether the permission allows requesting to speak in stage channels."""
        return 1 << 32

    @triflag
    def manage_events() -> int:
        """Whether the permission allows managing scheduled events."""
        return 1 << 33

    @triflag
    def manage_threads() -> int:
        """Whether the permission allows managing threads."""
        return 1 << 34

    @triflag
    def create_public_threads() -> int:
        """Whether the permission allows creating in public threads."""
        return 1 << 35

    @triflag
    def create_private_threads() -> int:
        """Whether the permission allows creating private threads."""
        return 1 << 36

    @triflag
    def use_external_stickers() -> int:
        """Whether the permission allows using external stickers."""
        return 1 << 37

    @triflag
    def send_messages_in_threads() -> int:
        """Whether the permission allows participating in threads."""
        return 1 << 38

    @triflag
    def use_embedded_activities() -> int:
        """Whether the permission allows using embedded activities."""
        return 1 << 39

    @triflag
    def moderate_members() -> int:
        """Whether the permission allows timing out other members."""
        return 1 << 40
