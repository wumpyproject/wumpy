from typing import List, Optional, SupportsInt

from discord_typings import (
    DMChannelData, GuildData, PartialGuildData, UserData
)

from .._requester import Requester
from .._route import Route
from .._utils import MISSING

__all__ = (
    'UserEndpoints',
)


class UserEndpoints(Requester):
    """Endpoints for interacting with user data."""

    __slots__ = ()

    async def fetch_my_user(self) -> UserData:
        """Fetch the bot user account.

        This is not a shortcut to `fetch_user()`, it has a different ratelimit
        and returns a bit more information.

        Returns:
            The user object received from Discord.
        """
        return await self.request(Route('GET', '/users/@me'))

    async def fetch_user(self, user: SupportsInt) -> UserData:
        """Fetch a data about a user by its ID.

        You also do not need to share a guild with the user to fetch their
        (limited) information.

        Parameters:
            user: The ID of the user to fetch.

        Returns:
            The user object received from Discord.
        """
        return await self.request(Route('GET', '/users/{user_id}', user_id=int(user)))

    async def edit_my_user(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[str] = MISSING,
    ) -> UserData:
        """Edit the bot user account.

        Parameters:
            username:
                The new bot user's name (can cause the discriminator to
                be randomized if there are already a user with that name).
            avatar:
                Image data in the Data URI scheme, or None to reset the avatar
                to the default Discord version according to the discriminator.

        Returns:
            The updated and new user object from Discord.
        """
        if username is MISSING and avatar is MISSING:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        payload = {
            'username': username,
            'avatar': avatar,
        }

        return await self.request(Route('PATCH', '/users/@me'), json=payload)

    async def fetch_my_guilds(
        self,
        *,
        before: SupportsInt = MISSING,
        after: SupportsInt = MISSING,
        limit: int = 200
    ) -> List[PartialGuildData]:
        """Fetch all guilds that the bot user is in.

        This endpoint allows pagination for bots who are a member of more than
        200 guilds using the `before` and `after` parameters.

        Parameters:
            before: Snowflake to fetch guilds before.
            after: Snowflake to fetch guilds after.
            limit: How many guilds to maximally return.

        Returns:
            A list of partial guilds the bot user is a part of.
        """
        params = {'limit': limit}
        if before is not MISSING:
            params['before'] = int(before)
        elif after is not MISSING:
            params['after'] = int(after)

        return await self.request(Route('GET', '/users/@me/guilds'))

    async def leave_guild(self, guild: SupportsInt) -> None:
        """Make the bot user leave the specified guild.

        Parameters:
            guild: The ID of the guild to leave.
        """
        await self.request(Route('DELETE', '/users/@me/guilds/{guild_id}', guild_id=int(guild)))

    async def create_dm(self, recipient: SupportsInt) -> DMChannelData:
        """Create a DM with the recipient.

        This method is safe to call several times to get the DM channel when
        needed. In fact, in other wrappers this is called everytime you send
        a message to a user.

        Parameters:
            recipient: The user to open a DM with.

        Returns:
            The DM channel object returned by Discord.
        """
        return await self.request(Route(
            'POST', '/users/@me/channels'), json={'recipient_id': int(recipient)}
        )
