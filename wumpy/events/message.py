from typing import Any, Dict, Optional

from ..models import Snowflake
from ..utils import Event

__all__ = (
    'ReactionAddEvent', 'ReactionRemoveEvent',
    'ReactionClearEvent', 'ReactionEmojiClearEvent'
)


class ReactionAddEvent(Event):
    """Dispatched when a user adds a reaction to a message."""

    message_id: Snowflake
    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Dict
    member: Dict

    NAME = "MESSAGE_REACTION_ADD"

    __slots__ = ('message_id', 'user_id', 'channel_id', 'guild_id', 'emoji', 'member')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.message_id = Snowflake(data['d']['message_id'])
        self.user_id = Snowflake(data['d']['user_id'])
        self.channel_id = Snowflake(data['d']['channel_id'])

        guild_id = data['d'].get('guild_id')
        self.guild_id = Snowflake(guild_id) if guild_id is not None else None

        self.emoji = data['d']['emoji']
        self.member = data['d'].get('member')


class ReactionRemoveEvent(Event):
    """Dispatched when a reaction is removed from a message."""

    message_id: Snowflake
    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Dict

    NAME = "MESSAGE_REACTION_REMOVE"

    __slots__ = ('message_id', 'user_id', 'channel_id', 'guild_id', 'emoji')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.message_id = Snowflake(data['d']['message_id'])
        self.user_id = Snowflake(data['d']['user_id'])
        self.channel_id = Snowflake(data['d']['channel_id'])

        guild_id = data['d'].get('guild_id')
        self.guild_id = Snowflake(guild_id) if guild_id is not None else None

        self.emoji = data['d']['emoji']


class ReactionClearEvent(Event):
    """Dispatched when all reactions is removed from a message."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    NAME = "MESSAGE_REACTION_REMOVE_ALL"

    __slots__ = ('message_id', 'channel_id', 'guild_id')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.message_id = Snowflake(data['d']['message_id'])
        self.channel_id = Snowflake(data['d']['channel_id'])

        guild_id = data['d'].get('guild_id')
        self.guild_id = Snowflake(guild_id) if guild_id is not None else None


class ReactionEmojiClearEvent(Event):
    """Dispatched when only a specific emoji's reactions are cleared."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Dict

    NAME = "MESSAGE_REACTION_REMOVE_EMOJI"

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'emoji')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.message_id = Snowflake(data['d']['message_id'])
        self.channel_id = Snowflake(data['d']['channel_id'])

        guild_id = data['d'].get('guild_id')
        self.guild_id = Snowflake(guild_id) if guild_id is not None else None

        self.emoji = data['d']['emoji']
