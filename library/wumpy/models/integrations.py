from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from ..utils import _get_as_snowflake
from .base import Object, Snowflake
from .user import User

__all__ = ('IntegrationExpire', 'IntegrationAccount', 'IntegrationApplication')


class IntegrationExpire(Enum):
    REMOVE_ROLE = 0
    KICK = 1


class IntegrationType(str, Enum):
    TWITCH = 'twitch'
    YOUTUBE = 'youtube'
    DISCORD = 'discord'


class IntegrationAccount:
    """Information about the account associated with an integration.

    Attributes:
        id: ID of the account.
        name: The name of the account.
    """

    id: str
    name: str

    __slots__ = ('id', 'name')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id = data['id']
        self.name = data['name']


class IntegrationApplication(Object):
    """Information about a bot/OAuth2 application.

    Attributes:
        name: The name of the application.
        icon: Icon hash of the application.
        description: Description of the application.
        summary: A summary of the application.
        user: The user object associated with the application.
    """

    name: str
    icon: Optional[str]
    description: str
    summary: str
    user: Optional[User]

    __slots__ = ('name', 'icon', 'description', 'summary', 'user')

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.name = data['name']
        self.icon = data['icon']
        self.description = data['description']
        self.summary = data['summary']

        user = data.get('bot')
        self.user = User(user) if user is not None else None


class Integration(Object):
    """Representation of a guild integration.

    This class only contains data that both BotIntegrations and
    StreamIntegration share.

    Attributes:
        name: The name of the integration.
        type: The type of integration (twitch or youtube).
        enabled: Whether the integration is enabled.
        account: Account information about the integration.
    """

    name: str
    type: str
    enabled: bool
    account: IntegrationAccount

    __slots__ = ('name', 'type', 'enabled', 'account')

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.name = data['name']
        self.type = data['type']
        self.enabled = data['enabled']
        self.account = IntegrationAccount(data['account'])


class BotIntegration(Integration):
    """Representation of a bot integration in a guild.

    Attributes:
        application: The application associated with the integration.
    """

    application: IntegrationApplication

    __slots__ = ('application',)

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self.application = IntegrationApplication(data['application'])

    @property
    def user(self) -> Optional[User]:
        """The user associated with the integration."""
        return self.application.user


class StreamIntegration(Integration):
    """Representation of a guild integration for Twitch or YouTube.

    Attributes:
        syncing: Whether the integration is synchronizing.
        role_id: The ID of the role associated with the integration.
        enable_emoticons:
            Whether emoticons should be synchronized (currently only for
            twitch integrations).
        expire_behavior: The behavior when the integration expires.
        expire_grace_period: The grace period before the integration expires.
        user: The user associated with the integration.
        synced_at: When the integration was last synchronized.
        subscriber_count: How many subscribers the integration has.
        revoked: Whether the integration has been revoked.
    """

    syncing: bool
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    expire_behavior: IntegrationExpire
    expire_grace_period: int
    user: User
    synced_at: datetime
    subscriber_count: int

    __slots__ = (
        'syncing', 'role_id', 'enable_emoticons', 'expire_behavior',
        'expire_grace_period', 'user', 'synced_at', 'subscriber_count',
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self.syncing = data['syncing']
        self.role_id = _get_as_snowflake(data, 'role_id')
        self.enable_emoticons = data['enable_emoticons']
        self.expire_behavior = IntegrationExpire(data['expire_behavior'])
        self.user = User(data['user'])
        self.synced_at = datetime.fromtimestamp(data['synced_at'], timezone.utc)
        self.subscriber_count = data['subscriber_count']
