from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from .base import Object
from .flags import BaseFlags, flag

__all__ = ('Permissions', 'PermissionOverwrite')


class Permissions(BaseFlags):
    """A bitfield for wrapping Discord permissions."""

    __slots__ = ()

    @flag
    def create_instant_invite(_) -> int:
        """Whether the permission allows creating instant invites."""
        return 1 << 0

    # All other permissions use plural, but this one is weirdly singular
    # so we alias it
    create_instant_invites = create_instant_invite

    @flag
    def kick_members(_) -> int:
        """Whether the permission allows kicking members from the guild."""
        return 1 << 1

    @flag
    def ban_members(_) -> int:
        """Whether the permission allows banning members from the guild."""
        return 1 << 2

    @flag
    def administrator(_) -> int:
        """Whether the permisson gives the user administrator permissions.

        An administrator gets all other permissions, and
        channel-specific overrides do not apply.
        """
        return 1 << 3

    @flag
    def manage_channels(_) -> int:
        """Whether the permission allows managing channels."""
        return 1 << 4

    @flag
    def manage_guild(_) -> int:
        """Whether the permission allows managing guild settings."""
        return 1 << 5

    @flag
    def add_reactions(_) -> int:
        """Whether the permission allows adding new reactions to a message."""
        return 1 << 6

    @flag
    def view_audit_log(_) -> int:
        """Whether the permission allows viewing the audit log entries."""
        return 1 << 7

    @flag
    def priority_speaker(_) -> int:
        """Whether the permission allows using priority speaker in a voce channel."""
        return 1 << 8

    @flag
    def stream(_) -> int:
        """Whether the permission allows streaming in voice channels."""
        return 1 << 9

    @flag
    def view_channel(_) -> int:
        """Whether the permission allows viewing the channel."""
        return 1 << 10

    # Another singular permission
    view_channels = view_channel

    @flag
    def send_messages(_) -> int:
        """Whether the permission allows sending messages in that channel."""
        return 1 << 11

    @flag
    def send_tts_messages(_) -> int:
        """Whether the permission allows sending text-to-speech messages."""
        return 1 << 12

    @flag
    def manage_messages(_) -> int:
        """Whether the permission allows managing messages."""
        return 1 << 13

    @flag
    def embed_links(_) -> int:
        """Whether the permission allows embedding links."""
        return 1 << 14

    @flag
    def attach_files(_) -> int:
        """Whether the permission allows attaching files to messages."""
        return 1 << 15

    @flag
    def read_message_history(_) -> int:
        """Whether the permission allows reading the message history."""
        return 1 << 16

    @flag
    def mention_everyone(_) -> int:
        """Whether the permission allows mentioning @everyone and @here roles.

        Members with this permission can mention roles with
        "Allow anyone to @mention this role" disabled.
        """
        return 1 << 17

    @flag
    def use_external_emojis(_) -> int:
        """Whether the permission allows sending external emojis."""
        return 1 << 18

    @flag
    def view_guild_insights(_) -> int:
        """Whether the permission allows viewing guild insights."""
        return 1 << 19

    @flag
    def connect(_) -> int:
        """Whether the permission allows connecting to voice channels."""
        return 1 << 20

    @flag
    def speak(_) -> int:
        """Whether the permission allows speaking in voice channels."""
        return 1 << 21

    @flag
    def mute_members(_) -> int:
        """Whether the permission allows server muting members."""
        return 1 << 22

    @flag
    def deafen_members(_) -> int:
        """Whether the permission allows server deafening members."""
        return 1 << 23

    @flag
    def move_members(_) -> int:
        """Whether the permission allows moving members to different voice channels."""
        return 1 << 24

    @flag
    def use_vad(_) -> int:
        """Whether the permission allows using voice activity."""
        return 1 << 25

    @flag
    def change_nickname(_) -> int:
        """Whether the permission allows changing own nickname."""
        return 1 << 26

    @flag
    def manage_nicknames(_) -> int:
        """Whether the permission allows managing others' nicknames."""
        return 1 << 27

    @flag
    def manage_roles(_) -> int:
        """Whether the permission allows managing roles and permissions."""
        return 1 << 28

    @flag
    def manage_webhooks(_) -> int:
        """Whether the permission allows managing webhooks and integrations."""
        return 1 << 29

    @flag
    def manage_emojis_and_stickers(_) -> int:
        """Whether the permission allows managing emojis and stickers."""
        return 1 << 30

    @flag
    def use_slash_commands(_) -> int:
        """Whether the permission allows using slash commands."""
        return 1 << 31

    @flag
    def request_to_speak(_) -> int:
        """Whether the permission allows requesting to speak in stage channels."""
        return 1 << 32

    @flag
    def manage_threads(_) -> int:
        """Whether the permission allows managing threads."""
        return 1 << 33

    @flag
    def use_public_threads(_) -> int:
        """Whether the permission allows creating and participating in public threads."""
        return 1 << 34

    @flag
    def use_private_threads(_) -> int:
        """Whether the permission allows creating and being invited to private threads."""
        return 1 << 35

    @flag
    def use_external_stickers(_) -> int:
        """Whether the permission allows using external stickers."""
        return 1 << 36


class TriBitMask:
    """Representing one bit of two bitfields similar to BitMask.

    This has the potential to return None if neither the `allow` or `deny`
    bits are set.
    """

    mask: int

    __slots__ = ('mask',)

    def __init__(self, mask: int) -> None:
        self.mask = mask

    def __get__(self, instance: 'PermissionOverwrite', _: Optional[type]) -> Union[bool, None, int]:
        if instance is None:
            return self.mask

        if (instance.allow & self.mask) == self.mask:
            return True
        elif (instance.deny & self.mask) == self.mask:
            return False
        else:
            return None

    def __set__(self, instance: 'PermissionOverwrite', value: bool) -> None:
        # This isn't the prettiest, but there's no better way to do it. When we
        # set one to True, we need to set the other to False. In the case of None
        # we set both to False.

        if value is True:
            instance.allow |= self.mask
            instance.deny &= ~self.mask
        elif value is False:
            instance.allow &= ~self.mask
            instance.deny |= self.mask
        elif value is None:
            instance.allow &= ~self.mask
            instance.deny &= ~self.mask
        else:
            raise TypeError(f'Expected type bool or None but got {type(value).__name__}.')


def triflag(func: Callable[[Any], int]) -> TriBitMask:
    """The equivalent of the normal `flag` decorator, but for TriBitMask."""
    return TriBitMask(func(None))


class PermissionTarget(Enum):
    role = 0
    member = 1


SELF = TypeVar('SELF', bound='PermissionOverwrite')


class PermissionOverwrite(Object):
    """"Discord permission overwrite object.

    Compared to many other Wumpy models, this one will often be initialized
    by users and as such a special `from_data()` classmethod is used by the
    library.
    """

    type: Optional[PermissionTarget]
    allow: Permissions
    deny: Permissions

    __slots__ = ('type', 'allow', 'deny')

    def __init__(self, target: int, **options: bool) -> None:
        super().__init__(int(target))

        self.allow = Permissions(0)
        self.deny = Permissions(0)

        for name, value in options.items():
            setattr(self, name, value)

    @classmethod
    def from_data(cls: Type[SELF], data: Dict) -> SELF:
        """Initialize a permission overwrite object from Discord data.

        This is used because a PermissionOverwrite object is often initialized by users.
        """
        self = cls.__new__(cls)

        self.type = PermissionTarget(data['type'])

        self.allow = Permissions(int(data['allow']))
        self.deny = Permissions(int(data['deny']))

        return self

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return super().__eq__(other) and self.allow == other.allow and self.deny == other.deny

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return True

        return super().__ne__(other) or self.allow != other.allow or self.deny != other.deny

    # As painful as it may be, it is necessary to play nice with documentation
    # and auto-completion. This is a copy from the Permissions class above, with
    # the decorator changed to be the tribool version.

    @triflag
    def create_instant_invite(_) -> int:
        """Whether the permission allows creating instant invites."""
        return 1 << 0

    # Alias in plural
    create_instant_invites = create_instant_invite

    @triflag
    def kick_members(_) -> int:
        """Whether the permission allows kicking members from the guild."""
        return 1 << 1

    @triflag
    def ban_members(_) -> int:
        """Whether the permission allows banning members from the guild."""
        return 1 << 2

    @triflag
    def administrator(_) -> int:
        """Whether the permisson gives the user administrator permissions.

        An administrator gets all other permissions, and
        channel-specific overrides do not apply.
        """
        return 1 << 3

    @triflag
    def manage_channels(_) -> int:
        """Whether the permission allows managing channels."""
        return 1 << 4

    @triflag
    def manage_guild(_) -> int:
        """Whether the permission allows managing guild settings."""
        return 1 << 5

    @triflag
    def add_reactions(_) -> int:
        """Whether the permission allows adding new reactions to a message."""
        return 1 << 6

    @triflag
    def view_audit_log(_) -> int:
        """Whether the permission allows viewing the audit log entries."""
        return 1 << 7

    @triflag
    def priority_speaker(_) -> int:
        """Whether the permission allows using priority speaker in a voce channel."""
        return 1 << 8

    @triflag
    def stream(_) -> int:
        """Whether the permission allows streaming in voice channels."""
        return 1 << 9

    @triflag
    def view_channel(_) -> int:
        """Whether the permission allows viewing the channel."""
        return 1 << 10

    view_channels = view_channel  # Alias

    @triflag
    def send_messages(_) -> int:
        """Whether the permission allows sending messages in that channel."""
        return 1 << 11

    @triflag
    def send_tts_messages(_) -> int:
        """Whether the permission allows sending text-to-speech messages."""
        return 1 << 12

    @triflag
    def manage_messages(_) -> int:
        """Whether the permission allows managing messages."""
        return 1 << 13

    @triflag
    def embed_links(_) -> int:
        """Whether the permission allows embedding links."""
        return 1 << 14

    @triflag
    def attach_files(_) -> int:
        """Whether the permission allows attaching files to messages."""
        return 1 << 15

    @triflag
    def read_message_history(_) -> int:
        """Whether the permission allows reading the message history."""
        return 1 << 16

    @triflag
    def mention_everyone(_) -> int:
        """Whether the permission allows mentioning @everyone and @here roles.

        Members with this permission can mention roles with
        "Allow anyone to @mention this role" disabled.
        """
        return 1 << 17

    @triflag
    def use_external_emojis(_) -> int:
        """Whether the permission allows sending external emojis."""
        return 1 << 18

    @triflag
    def view_guild_insights(_) -> int:
        """Whether the permission allows viewing guild insights."""
        return 1 << 19

    @triflag
    def connect(_) -> int:
        """Whether the permission allows connecting to voice channels."""
        return 1 << 20

    @triflag
    def speak(_) -> int:
        """Whether the permission allows speaking in voice channels."""
        return 1 << 21

    @triflag
    def mute_members(_) -> int:
        """Whether the permission allows server muting members."""
        return 1 << 22

    @triflag
    def deafen_members(_) -> int:
        """Whether the permission allows server deafening members."""
        return 1 << 23

    @triflag
    def move_members(_) -> int:
        """Whether the permission allows moving members to different voice channels."""
        return 1 << 24

    @triflag
    def use_vad(_) -> int:
        """Whether the permission allows using voice activity."""
        return 1 << 25

    @triflag
    def change_nickname(_) -> int:
        """Whether the permission allows changing own nickname."""
        return 1 << 26

    @triflag
    def manage_nicknames(_) -> int:
        """Whether the permission allows managing others' nicknames."""
        return 1 << 27

    @triflag
    def manage_roles(_) -> int:
        """Whether the permission allows managing roles and permissions."""
        return 1 << 28

    @triflag
    def manage_webhooks(_) -> int:
        """Whether the permission allows managing webhooks and integrations."""
        return 1 << 29

    @triflag
    def manage_emojis_and_stickers(_) -> int:
        """Whether the permission allows managing emojis and stickers."""
        return 1 << 30

    @triflag
    def use_slash_commands(_) -> int:
        """Whether the permission allows using slash commands."""
        return 1 << 31

    @triflag
    def request_to_speak(_) -> int:
        """Whether the permission allows requesting to speak in stage channels."""
        return 1 << 32

    @triflag
    def manage_threads(_) -> int:
        """Whether the permission allows managing threads."""
        return 1 << 33

    @triflag
    def use_public_threads(_) -> int:
        """Whether the permission allows creating and participating in public threads."""
        return 1 << 34

    @triflag
    def use_private_threads(_) -> int:
        """Whether the permission allows creating and being invited to private threads."""
        return 1 << 35

    @triflag
    def use_external_stickers(_) -> int:
        """Whether the permission allows using external stickers."""
        return 1 << 36
