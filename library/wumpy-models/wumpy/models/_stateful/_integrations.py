from typing import Optional

import attrs
from discord_typings import (
    DiscordIntegrationData, IntegrationApplicationData
)
from typing_extensions import Self

from .._raw import (
    IntegrationAccount, RawBotIntegration,
    RawIntegrationApplication, RawStreamIntegration
)
from . import _user

__all__ = (
    'IntegrationApplication',
    'BotIntegration',
    'StreamIntegration',
)


@attrs.define(eq=False, frozen=True, kw_only=True)
class IntegrationApplication(RawIntegrationApplication):
    user: Optional['_user.User']

    @classmethod
    def from_data(cls, data: IntegrationApplicationData) -> Self:
        user = data.get('bot')
        if user is not None:
            user = _user.User.from_data(user)

        return cls(
            id=int(data['id']),
            name=data['name'],
            icon=data.get('icon'),
            description=data['description'],
            summary=data['summary'],
            user=user
        )


@attrs.define(eq=False, frozen=True, kw_only=True)
class BotIntegration(RawBotIntegration):
    application: Optional[IntegrationApplication] = None

    @property
    def user(self) -> Optional['_user.User']:
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
            type=data['type'],
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            application=application
        )


@attrs.define(eq=False, frozen=True)
class StreamIntegration(RawStreamIntegration):
    ...
