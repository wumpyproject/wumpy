from typing import Optional

import attrs
from discord_typings import (
    DiscordIntegrationData, IntegrationAccountData, IntegrationApplicationData,
    StreamingIntegrationData
)
from typing_extensions import Self

from .._raw import (
    Integration, IntegrationAccount, IntegrationType, RawBotIntegration,
    RawIntegrationApplication, RawStreamIntegration
)
from .._utils import Model, Snowflake, _get_as_snowflake
from . import _user


@attrs.define(eq=False, kw_only=True)
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


@attrs.define(eq=False, kw_only=True)
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
            type=IntegrationType(data['type']),
            enabled=data['enabled'],
            account=IntegrationAccount.from_data(data['account']),
            application=application
        )


@attrs.define(eq=False)
class StreamIntegration(RawStreamIntegration):
    ...
