import enum
from typing import Any, Awaitable, Callable, Dict, List, Sequence, Optional

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


class ResolvedInteractionData:
    """Asynchronously resolved data from Discord."""

    users: Dict[int, Dict[str, Any]]
    members: Dict[int, Dict[str, Any]]

    roles: Dict[int, Dict[str, Any]]
    channels: Dict[int, Dict[str, Any]]

    messages: Dict[int, Dict[str, Any]]

    __slots__ = ('users', 'members', 'roles', 'channels', 'messages')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.users = {int(k): v for k, v in data.get('users', {}).items()}
        self.members = {int(k): v for k, v in data.get('members', {}).items()}

        self.roles = {int(k): v for k, v in data.get('roles', {}).items()}
        self.channels = {int(k): v for k, v in data.get('channels', {}).items()}

        self.messages = {int(k): v for k, v in data.get('messages', {}).items()}


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

    def __init__(self, data: Dict[str, Any]) -> None:
        self.name = data['name']
        self.type = ApplicationCommandOption(data['type'])

        self.value = data.get('value')
        self.options = [CommandInteractionOption(option) for option in data.get('options', [])]


class Interaction(Object):
    """Base for all interaction objects."""

    _send: Callable[[Dict[str, Any]], Awaitable[None]]
    _rest: InteractionRequester

    application_id: int
    type: InteractionType

    guild_id: Optional[int]
    channel_id: Optional[int]

    user: InteractionUser
    token: str

    __slots__ = (
        'app', '_send', '_rest', 'application_id', 'type', 'guild_id',
        'channel_id', 'member', 'user', 'token', 'version'
    )

    def __init__(
        self,
        app: Any,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        rest: InteractionRequester,
        data: Dict[str, Any]
    ) -> None:
        super().__init__(int(data['id']))

        self.app = app

        self._send = send
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

    name: str
    invoked: int
    invoked_type: ApplicationCommandOption

    resolved: ResolvedInteractionData
    options: List[CommandInteractionOption]

    __slots__ = ('name', 'invoked', 'invoked_type', 'resolved', 'options')

    def __init__(
        self,
        app: Any,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        rest: InteractionRequester,
        data: Dict[str, Any]
    ) -> None:
        super().__init__(app, send, rest, data)

        self.name = data['data']['name']
        self.invoked = data['data']['id']
        self.invoked_type = ApplicationCommandOption(data['data']['type'])

        self.resolved = ResolvedInteractionData(data['data'].get('resolved', {}))
        self.options = [CommandInteractionOption(option) for option in data['data']['options']]


class MessageComponentInteraction(Interaction):
    """Interaction for a message component."""

    message: Dict[str, Any]

    custom_id: str
    component_type: ComponentType

    __slots__ = ('message', 'custom_id', 'component_type')

    def __init__(
        self,
        app: Any,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        rest: InteractionRequester,
        data: Dict[str, Any]
    ) -> None:
        super().__init__(app, send, rest, data)

        self.message = data['data']

        self.custom_id = data['data']['custom_id']
        self.component_type = ComponentType(data['data']['component_type'])


class SelectInteractionValue:
    """One of the values for a select option."""

    label: str
    value: str
    description: Optional[str]
    emoji: Optional[Dict[str, Any]]
    default: Optional[bool]

    __slots__ = ('label', 'value', 'description', 'emoji', 'default')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.label = data['label']
        self.value = data['value']

        self.description = data.get('description')
        self.emoji = data.get('emoji')
        self.emoji = data.get('default')


class SelectMenuInteraction(MessageComponentInteraction):
    """Interaction for a selection menu message component."""

    values: List[SelectInteractionValue]

    __slots__ = ('values',)

    def __init__(
        self,
        app: Any,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        rest: InteractionRequester,
        data: Dict[str, Any]
    ) -> None:
        super().__init__(app, send, rest, data)

        self.values = [SelectInteractionValue(value) for value in data['data']['values']]
