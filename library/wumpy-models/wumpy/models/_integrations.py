import dataclasses
from datetime import datetime
from enum import Enum
from typing import Optional

from discord_typings import (
    DiscordIntegrationData, IntegrationAccountData, IntegrationApplicationData,
    StreamingIntegrationData
)
from typing_extensions import Self

from ._base import Model, Snowflake
from ._user import User
from ._utils import _get_as_snowflake, backport_slots

__all__ = (
    'IntegrationExpire',
    'IntegrationType',
    'IntegrationAccount',
    'IntegrationApplication',
    'BotIntegration',
    'StreamIntegration',
)


class IntegrationExpire(Enum):
    REMOVE_ROLE = 0
    KICK = 1


class IntegrationType(str, Enum):
    twitch = 'twitch'
    youtube = 'youtube'
    discord = 'discord'


@backport_slots()
@dataclasses.dataclass(frozen=True)
class IntegrationAccount:
    """Information about the account associated with an integration.

    Attributes:
        id: ID of the account.
        name: The name of the account.
    """

    id: str
    name: str

    @classmethod
    def from_data(cls, data: IntegrationAccountData) -> Self:
        return cls(data['id'], data['name'])


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class IntegrationApplication(Model):
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
    user: Optional[User] = None

    @classmethod
    def from_user(cls, user: User, data: IntegrationApplicationData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            icon=data.get('icon'),
            description=data['description'],
            summary=data['summary'],
            user=user
        )

    @classmethod
    def from_data(cls, data: IntegrationApplicationData) -> Self:
        user = data.get('bot')
        if user is not None:
            user = User.from_data(user)

        return cls(
            id=int(data['id']),
            name=data['name'],
            icon=data.get('icon'),
            description=data['description'],
            summary=data['summary'],
            user=user
        )


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class BotIntegration(Model):
    """Representation of a bot integration in a guild.

    Attributes:
        application: The application associated with the integration.
    """

    name: str
    type: IntegrationType
    enabled: bool
    account: IntegrationAccount

    application: Optional[IntegrationApplication] = None

    @property
    def user(self) -> Optional[User]:
        """The user associated with the integration."""
        return None if self.application is None else self.application.user

    @classmethod
    def from_data(cls, data: DiscordIntegrationData) -> Self:
        application = data.get('application')
        if application is not None:
            application = IntegrationApplication.from_data(application)

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=IntegrationType(data['type']),
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            application=application
        )


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class StreamIntegration(Model):
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

    name: str
    type: IntegrationType
    enabled: bool
    account: IntegrationAccount

    syncing: bool
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    expire_behavior: IntegrationExpire
    expire_grace_period: int
    user: User
    synced_at: datetime
    subscriber_count: int
    revoked: bool

    @classmethod
    def from_data(cls, data: StreamingIntegrationData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            type=IntegrationType(data['type']),
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            syncing=data['syncing'],
            role_id=_get_as_snowflake(data, 'role_id'),
            enable_emoticons=data['enable_emoticons'],
            expire_behavior=IntegrationExpire(data['expire_behavior']),
            expire_grace_period=data['expire_grace_period'],
            user=User.from_data(data['user']),
            synced_at=datetime.fromisoformat(data['synced_at']),
            subscriber_count=data['subscriber_count'],
            revoked=data['revoked'],
        )
