from datetime import datetime
from typing import Optional

import attrs
from discord_typings import (
    DiscordIntegrationData, IntegrationAccountData, IntegrationApplicationData,
    StreamingIntegrationData
)
from typing_extensions import Self

from .._utils import Model, Snowflake, _get_as_snowflake
from ._user import RawUser

__all__ = (
    'IntegrationAccount',
    'RawIntegrationApplication',
    'RawBotIntegration',
    'RawStreamIntegration',
)


@attrs.define(frozen=True)
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


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawIntegrationApplication(Model):
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
    user: Optional[RawUser] = None

    @classmethod
    def from_data(cls, data: IntegrationApplicationData) -> Self:
        user = data.get('bot')
        if user is not None:
            user = RawUser.from_data(user)

        return cls(
            id=int(data['id']),
            name=data['name'],
            icon=data.get('icon'),
            description=data['description'],
            summary=data['summary'],
            user=user
        )


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawBotIntegration(Model):
    """Representation of a bot integration in a guild.

    Attributes:
        application: The application associated with the integration.
    """

    name: str
    type: str
    enabled: bool
    account: IntegrationAccount

    application: Optional[RawIntegrationApplication] = None

    @property
    def user(self) -> Optional[RawUser]:
        """The user associated with the integration."""
        return None if self.application is None else self.application.user

    @classmethod
    def from_data(cls, data: DiscordIntegrationData) -> Self:
        application = data.get('application')
        if application is not None:
            application = RawIntegrationApplication.from_data(application)

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            application=application
        )


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawStreamIntegration(Model):
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
    type: str
    enabled: bool
    account: IntegrationAccount

    syncing: bool
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    expire_behavior: int
    expire_grace_period: int
    user: RawUser
    synced_at: datetime
    subscriber_count: int
    revoked: bool

    @classmethod
    def from_data(cls, data: StreamingIntegrationData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            syncing=data['syncing'],
            role_id=_get_as_snowflake(data, 'role_id'),
            enable_emoticons=data['enable_emoticons'],
            expire_behavior=data['expire_behavior'],
            expire_grace_period=data['expire_grace_period'],
            user=RawUser.from_data(data['user']),
            synced_at=datetime.fromisoformat(data['synced_at']),
            subscriber_count=data['subscriber_count'],
            revoked=data['revoked'],
        )
