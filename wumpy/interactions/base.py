import enum
from typing import Any, Dict, Optional

from ..models import InteractionUser, Object
from .rest import InteractionRequester


class InteractionType(enum.Enum):
    ping = 1
    application_command = 2
    message_component = 3


class ComponentType(enum.Enum):
    action_row = 1
    button = 2
    select_menu = 3


class Interaction(Object):
    """Base for all interaction objects."""

    _rest: InteractionRequester
    application_id: int
    type: InteractionType

    guild_id: Optional[int]
    channel_id: Optional[int]

    __slots__ = (
        '_rest', 'application_id', 'type', 'guild_id', 'channel_id',
        'member', 'user', 'token', 'version'
    )

    def __init__(self, rest: InteractionRequester, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self._rest = rest

        self.application_id = data['application_id']
        self.type = data['type']

        self.channel_id = data.get('channel_id')
        self.guild_id = data.get('guild_id')

        member = data.get('member')
        if member:
            self.user = InteractionUser(rest, member['user'])
        else:
            self.user = InteractionUser(rest, data['user'])

        self.token = data['token']
        self.version = data['version']


class CommandInteraction(Interaction):
    """Interaction for a Discord command (slash)."""

    def __init__(self, rest: InteractionRequester, data: Dict[str, Any]) -> None:
        super().__init__(rest, data)

        self.options = data['data']['options']

        self.name = data['data']['name']


class MessageComponentInteraction(Interaction):
    """Interaction for a message component."""

    def __init__(self, rest: InteractionRequester, data: Dict[str, Any]) -> None:
        super().__init__(rest, data)

        self.message = data['data']

        self.custom_id = data['data']['custom_id']
        self.component_type = ComponentType(data['data']['component_type'])


class SelectMenuInteraction(MessageComponentInteraction):
    """Interaction for a selection menu message component."""

    def __init__(self, rest: InteractionRequester, data: Dict[str, Any]) -> None:
        super().__init__(rest, data)

        self.values = data['data']['values']
