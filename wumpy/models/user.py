"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, SupportsInt

from ..rest import Requester
from ..utils import MISSING, File
from .asset import Asset
from .base import Object
from .channels import DMChannel
from .flags import AllowedMentions, UserFlags

if TYPE_CHECKING:
    from ..state import RESTClient

__all__ = ('InteractionUser', 'BotUser', 'User')


class _BaseUser(Object):
    """The base for all user objects.

    The reason that this is seperated from User is because we don't want BotUser
    to inherit certain methods, you cannot DM yourself for example.
    """

    _rest: 'Requester'

    username: str
    discriminator: int
    avatar: Optional[Asset]

    public_flags: UserFlags

    bot: Optional[bool]
    system: Optional[bool]

    __slots__ = (
        '_rest', 'username', 'discriminator',
        'avatar', 'public_flags', 'bot', 'system'
    )

    def __init__(self, rest: 'Requester', data: Dict) -> None:
        super().__init__(int(data['id']))
        self._rest = rest

        self.bot = None
        self.system = None

        # We may need to update this object again, so if we seperate it
        # into another method we can call again
        self._update(data)

    def _update(self, data: Dict) -> None:
        self.username = data['username']
        self.discriminator = int(data['discriminator'])

        avatar = data['avatar']
        self.avatar = Asset(self._rest, f'avatars/{self.id}/{avatar}') if avatar else self.avatar

        flags = data.get('public_flags')
        self.public_flags = UserFlags(flags) if flags else self.public_flags

        self.bot = data.get('bot', self.bot)
        self.system = data.get('system', self.system)

    @property
    def mention(self):
        return f'<@{self.id}>'

    @property
    def default_avatar(self):
        # It is unneccessary to keep the default asset for each user in
        # memory, we create them when asked for.
        return Asset(self._rest, f'embed/avatars/{self.discriminator % 5}')


class InteractionUser(_BaseUser):
    """User object from an interaction, this wraps no user endpoints."""
    pass


class BotUser(_BaseUser):
    """User object attached to an application; the bot application's user account."""

    _rest: 'RESTClient'

    bio: str
    locale: str
    mfa_enabled: bool
    verified: bool

    __slots__ = ('bio', 'locale', 'mfa_enabled', 'verified')

    def __init__(self, rest: 'RESTClient', data: Dict) -> None:
        super().__init__(rest, data)
        self._rest = rest

        # We may need to update this object again, so if we seperate it
        # into another method we can call again
        self._update(data)

    def _update(self, data: Dict) -> None:
        super()._update(data)

        self.bio = data['bio']
        self.locale = data['locale']

        self.mfa_enabled = data['mfa_enabled']
        self.verified = data['verified']

    @property
    def flags(self):
        return self.public_flags

    async def edit(self, *, username: str = MISSING, avatar: str = MISSING) -> None:
        """Edit the bot user account."""
        data = await self._rest.edit_my_user(username=username, avatar=avatar)
        self._update(data)


class User(_BaseUser):
    """Discord User object."""

    _rest: 'RESTClient'

    channel: Optional[DMChannel]

    __slots__ = ('channel',)

    def __init__(self, rest: 'RESTClient', data: Dict) -> None:
        super().__init__(rest, data)

        self.channel = None

    async def create_dm(self) -> DMChannel:
        """Create a DM with the user, returning the DM channel."""
        self.channel = await self._rest.create_dm(self)
        return self.channel

    async def send(
        self,
        content: str = MISSING,
        *,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
        stickers: Sequence[SupportsInt] = MISSING
    ) -> Dict[str, Any]:
        """Send a message to the user.

        This requires knowing the channel, for that `create_dm()` is used.
        That means that this function may require two API calls, the library
        will call `create_dm()` if needed.
        """
        if not self.channel:
            # Even though create_dm() sets self.channel, the static
            # type checker doesn't know it does
            self.channel = await self.create_dm()

        return await self.channel.send(
            content, tts=tts, embeds=embeds,
            allowed_mentions=allowed_mentions, file=file, stickers=stickers
        )
