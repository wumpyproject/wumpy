from typing import (
    Any, Dict, List, Literal, Optional, Sequence, SupportsInt, Union
)

from ..ratelimiter import Route
from ..utils import MISSING
from .base import Requester


class GuildRequester(Requester):
    # Audit Log endpoints

    async def fetch_audit_logs(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch the audit log entries for this guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=int(guild)))

    # Emoji endpoints

    async def fetch_emojis(self, guild: SupportsInt) -> List[Any]:
        """Fetch all emojis in a guild by its ID."""
        return await self.request(Route('GET', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_emoji(self, guild: SupportsInt, emoji: SupportsInt) -> Dict[str, Any]:
        """Fetch a specific emoji from a guild by its ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/emojis/{emoji_id}',
            guild_id=int(guild), emoji_id=int(emoji)
        ))

    async def create_emoji(
        self,
        guild: SupportsInt,
        *,
        name: str,
        image: str,
        roles: Optional[Sequence[SupportsInt]] = None,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create an emoji in a guild."""
        payload = {
            'name': name,
            'image': image,
            # We can't iterate through None, so we need to add an additional
            # gate so that we simply pass None if it is
            'roles': [int(r) for r in roles] if roles else None
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/emojis', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_emoji(
        self,
        guild: SupportsInt,
        emoji: SupportsInt,
        *,
        name: str = MISSING,
        roles: List[SupportsInt] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit fields of an emoji by its ID."""
        if not name and roles == []:
            raise TypeError("one of 'name' or 'roles' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'roles': [int(r) for r in roles]
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/emojis/{emoji_id}',
                guild_id=int(guild), emoji_id=int(emoji)
            ),
            json=payload, reason=reason
        )

    async def delete_emoji(
        self,
        guild: SupportsInt,
        emoji: SupportsInt,
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Delete an emoji from a guild."""
        return await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/emojis/{emoji_id}',
                guild_id=int(guild), emoji_id=int(emoji)
            ),
            reason=reason
        )

    # Guild endpoints

    async def create_guild(
        self,
        name: str,
        *,
        icon: str = MISSING,
        verification_level: int = MISSING,
        notification_level: int = MISSING,
        content_filter: int = MISSING,
        roles: Sequence[Any] = MISSING,
        channels: Sequence[Any] = MISSING,
        afk_channel: int = MISSING,
        afk_timeout: int = MISSING,
        system_channel: int = MISSING,
        system_channel_flags: int = MISSING
    ) -> Dict[str, Any]:
        """Create a new guild, making the bot the owner."""
        payload: Dict[str, Any] = {
            'name': name,
            'icon': icon,
            'verification_level': verification_level,
            'default_message_notifications': notification_level,
            'explicit_content_filter': content_filter,
            'roles': roles,
            'channels': channels,
            'afk_channel_id': afk_channel,
            'afk_timeout': afk_timeout,
            'system_channel_id': system_channel,
            'system_channel_flags': system_channel_flags
        }

        return await self.request(Route('POST', '/guilds'), json=payload)

    async def fetch_guild(self, guild: SupportsInt, *, with_counts: bool = False) -> Dict[str, Any]:
        """Fetch a guild by its ID.

        If `with_counts` is set, an approximate member count will be included.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_guild_preview(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch a preview of a guild by its ID.

        If the bot user is not in the guild, it must be lurkable. Meaning that
        it must be discoverable or have a live public stage.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}/preview', guild_id=int(guild)))

    async def edit_guild(
        self,
        guild: SupportsInt,
        *,
        name: str = MISSING,
        verification_level: Optional[int] = MISSING,
        notification_level: Optional[int] = MISSING,
        content_filter: Optional[int] = MISSING,
        afk_channel: Optional[SupportsInt] = MISSING,
        afk_timeout: Optional[int] = MISSING,
        icon: Optional[str] = MISSING,
        owner: SupportsInt = MISSING,
        splash: Optional[str] = MISSING,
        discovery: Optional[str] = MISSING,
        banner: Optional[str] = MISSING,
        system_channel: Optional[SupportsInt] = MISSING,
        system_channel_flags: int = MISSING,
        rules_channel: Optional[SupportsInt] = MISSING,
        updates_channel: Optional[SupportsInt] = MISSING,
        preferred_locale: Optional[str] = MISSING,
        features: Sequence[str] = MISSING,
        description: Optional[str] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild."""
        payload: Dict[str, Any] = {
            'name': name,
            'verification_level': verification_level,
            'default_message_notifications': notification_level,
            'explicit_content_filter': content_filter,
            'afk_channel_id': int(afk_channel) if afk_channel else afk_channel,
            'afk_timeout': afk_timeout,
            'icon': icon,
            'owner_id': int(owner) if owner else owner,
            'splash': splash,
            'disconvery_splash': discovery,
            'banner': banner,
            'system_channel_id': int(system_channel) if system_channel else system_channel,
            'system_channel_flags': system_channel_flags,
            'rules_channel_id': int(rules_channel) if rules_channel else rules_channel,
            'public_updates_channel_id': int(updates_channel) if updates_channel else updates_channel,
            'preferred_locale': preferred_locale,
            'features': features,
            'description': description
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def delete_guild(self, guild: SupportsInt) -> None:
        """Delete a guild permanently, the bot must be the owner."""
        await self.request(Route('DELETE', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_channels(self, guild: SupportsInt) -> List[Any]:
        """Fetch all channels in a guild, excluding threads."""
        return await self.request(Route('GET', '/guilds/{guild_id}/channels', guild_id=int(guild)))

    async def create_channel(
        self,
        guild: SupportsInt,
        name: str,
        *,
        type: int = MISSING,
        topic: str = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rate_limit: int = MISSING,
        position: int = MISSING,
        permission_overwrites: List[PermissionOverwrite] = MISSING,
        parent: SupportsInt = MISSING,
        nsfw: bool = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new guild channel."""
        payload: Dict[str, Any] = {
            'name': name,
            'type': type,
            'topic': topic,
            'bitrate': bitrate,
            'user_limit': user_limit,
            'rate_limit_per_user': rate_limit,
            'position': position,
            'permissin_overwrites': permission_overwrites,
            'parent_id': int(parent) if parent else parent,
            'nsfw': nsfw,
        }

        return await self.request(
            Route('POST', '/guilds/{guild_id}/channels', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_channel_positions(
        self,
        guild: SupportsInt,
        channels: List[Dict[str, Any]],
        *,
        reason: str = MISSING
    ) -> None:
        """Edit several channels' positions."""
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/channels', guild_id=int(guild)),
            json=channels, reason=reason
        )

    async def fetch_active_threads(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch all active threads in a guild, both public and private threads."""
        return await self.request(
            Route('GET', '/guilds/{guild_id}/threads/active', guild_id=int(guild))
        )

    async def fetch_member(self, guild: SupportsInt, user: SupportsInt) -> Dict[str, Any]:
        """Fetch a specific member object by its user ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/embers/{user_id}',
            guild_id=int(guild), user_id=int(user)
        ))

    async def fetch_members(
        self,
        guild: SupportsInt,
        *,
        limit: int = 1,
        after: int = 0
    ) -> List[Any]:
        """Fetch all members in a guild.

        `after` is the highest user ID in the previous page, this way you can
        paginate all members even the guild has more than 1000 members.
        """
        if 0 > limit > 1001:
            raise TypeError("'limit' must be a value between 1-1000")

        return await self.request(
            Route('GET', '/guilds/{guild_id}/members', guild_id=int(guild)),
            params={'limit': limit, 'after': after}
        )

    async def search_members(self, guild: SupportsInt, query: str, *, limit: int = 1) -> List[Any]:
        """Search guild members after a name or nickname similar to `query`."""
        return await self.request(
            Route('GET', '/guilds/{guild_id}/members/search', guild_id=int(guild)),
            params={'query': query, 'limit': limit}
        )

    async def edit_member(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        nick: Optional[str] = MISSING,
        roles: Optional[Sequence[SupportsInt]] = MISSING,
        mute: Optional[bool] = MISSING,
        deafen: Optional[bool] = MISSING,
        channel: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit another guild member."""
        payload: Dict[str, Any] = {
            'nick': nick,
            'roles': [int(r) for r in roles] if roles else roles,
            'mute': mute,
            'deaf': deafen,
            'channel_id': int(channel) if channel else channel
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/members/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ),
            json=payload, reason=reason
        )

    async def edit_my_nick(
        self,
        guild: SupportsInt,
        nick: Optional[str] = '',
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit the nickname of the bot in the guild, passing None will reset the nickname."""
        # We need to mimic Discord's API, if you don't pass `nick` nothing happens
        options: Dict[str, Any] = {}
        if nick != '':
            options['nick'] = nick

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/members/@me/nick', guild_id=int(guild)),
            json=options, reason=reason
        )

    async def add_member_role(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        role: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Add a role to a guild member."""
        await self.request(
            Route(
                'PUT', '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                guild_id=int(guild), user_id=int(user), role_id=int(role)
            ), reason=reason
        )

    async def remove_member_role(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        role: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Remove a role from a guild member."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                guild_id=int(guild), user_id=int(user), role_id=int(role)
            ), reason=reason
        )

    async def kick_member(self, guild: SupportsInt, user: SupportsInt, *, reason: str = MISSING) -> None:
        """Remove a member from a guild, also known as kicking a member."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_bans(self, guild: SupportsInt) -> List[Any]:
        """Fetch all bans made on a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/bans', guild_id=int(guild)))

    async def fetch_ban(self, guild: SupportsInt, user: SupportsInt) -> Dict[str, Any]:
        """Fetch a specific ban made for a user."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/bans/{user_id}',
            guild_id=int(guild), user_id=int(user)
        ))

    async def ban_member(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        delete_message_days: int = MISSING,
        reason: str = MISSING
    ) -> None:
        """Create a guild ban, and ban a specific user from re-entering the guild."""
        options: Dict[str, Any] = {}
        if delete_message_days is not MISSING:
            options['delete_message_days'] = delete_message_days

        await self.request(
            Route(
                'PUT', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ),
            json=options, reason=reason
        )

    async def pardon_user(self, guild: SupportsInt, user: SupportsInt, *, reason: str = MISSING) -> None:
        """Pardon a user, and remove the ban allowing them to enter the guild again."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_roles(self, guild: SupportsInt) -> List[Any]:
        """Fetch all roles from a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/roles', guild_id=int(guild)))

    async def create_role(
        self,
        guild: SupportsInt,
        *,
        name: str = "new role",
        permissions: Union[str, int] = MISSING,
        color: int = 0,
        hoist: bool = False,
        mentionable: bool = False,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new role in a guild."""
        payload: Dict[str, Any] = {
            'name': name,
            'permissions': str(permissions) if permissions else MISSING,
            'color': color,
            'hoist': hoist,
            'mentionable': mentionable
        }

        return await self.request(
            Route('POST', '/guilds/{guild_id}/roles', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_role_positions(
        self,
        guild: SupportsInt,
        roles: List[Dict[str, Any]],
        reason: str = MISSING
    ) -> List[Any]:
        """Edit several roles' positions."""
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/roles', guild_id=int(guild)),
            json=roles, reason=reason
        )

    async def edit_role(
        self,
        guild: SupportsInt,
        role: SupportsInt,
        *,
        name: Optional[str] = MISSING,
        permissions: Optional[Union[int, str]] = MISSING,
        color: Optional[int] = MISSING,
        hoist: Optional[bool] = MISSING,
        mentionable: Optional[bool] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild role's different fields."""
        payload: Dict[str, Any] = {
            'name': name,
            'permissions': str(permissions) if permissions else permissions,
            'color': color,
            'hoist': hoist,
            'mentionable': mentionable
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/roles/{role_id}',
                guild_id=int(guild), role_id=int(role)
            ),
            json=payload, reason=reason
        )

    async def delete_role(self, guild: SupportsInt, role: SupportsInt, *, reason: str = MISSING) -> None:
        """Delete a guild role."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/roles/{role_id}',
                guild_id=int(guild), role_id=int(role)
            ), reason=reason
        )

    async def fetch_prune_count(
        self,
        guild: SupportsInt,
        *,
        days: int = 7,
        roles: Optional[Sequence[SupportsInt]] = None
    ) -> Dict[str, int]:
        """Fetch the amount of members that would be pruned.

        `roles` is a list of roles that should be included, as normally
        any member with roles is excluded from the operation.
        """
        # Roles may be a list of role object, first we int() them for the IDs
        # and then convert them to strings to join them
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        return await self.request(
            Route('GET', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            params={'days': days, 'include_roles': include_roles}
        )

    async def prune_guild(
        self,
        guild: SupportsInt,
        *,
        days: int = 7,
        compute_count: bool = True,
        roles: Optional[Sequence[SupportsInt]] = None,
        reason: str = MISSING
    ) -> Dict[str, Optional[int]]:
        """Begin a prune operation, and kick all members who do not meet the criteria passed."""
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        return await self.request(
            Route('POST', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            json={'days': days, 'compute_prune_count': compute_count, 'include_roles': include_roles},
            reason=reason
        )

    async def fetch_voice_regions(self, guild: SupportsInt = MISSING) -> List[Any]:
        """Fetch a list of voice regions.

        If a guild is passed, this may return VIP servers if the guild
        is VIP-enabled.
        """
        if guild is MISSING:
            return await self.request(Route('GET', '/voice/regions'))

        return await self.request(Route('GET', '/guilds/{guild_id}/regions', guild_id=int(guild)))

    async def fetch_guild_invites(self, guild: SupportsInt) -> List[Any]:
        """Fetch all invites for the guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=int(guild)))

    async def fetch_integrations(self, guild: SupportsInt) -> List[Any]:
        """Fetch all intergration for the guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/integrations', guild_id=int(guild)))

    async def delete_integration(
        self,
        guild: SupportsInt,
        integration: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete an attached integration for the guild.

        This may also delete any associated webhooks and kick the bot if
        there is one attached.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/integrations/{integration_id}',
                guild_id=int(guild), integration_id=int(integration)
            ), reason=reason
        )

    async def fetch_widget_settings(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch the settings for a widget for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/widget', guild_id=int(guild)))

    async def edit_widget(
        self,
        guild: SupportsInt,
        *,
        enabled: bool = MISSING,
        channel: Optional[SupportsInt] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild widget."""
        payload: Dict[str, Any] = {
            'enabled': enabled,
            'channel_id': int(channel) if channel else channel
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/widget', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def fetch_widget(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch a complete widget for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/widget.json', guild_id=int(guild)))

    async def fetch_vanity_invite(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch a partial invite for a guild that has that feature."""
        return await self.request(Route('GET', '/guilds/{guild_id}/vanity-url', guild_id=int(guild)))

    async def fetch_widget_image(
        self,
        guild: SupportsInt,
        *,
        style: Literal['shield', 'banner1', 'banner2', 'banner3', 'banner4'] = 'shield'
    ) -> bytes:
        """Read a style of PNG image for a guild's widget."""
        return await self._bypass_request(
            'GET',
            Route.BASE + f'/guilds/{int(guild)}/widget.png',
            params={'style': style}
        )

    async def fetch_welcome_screen(self, guild: SupportsInt) -> Dict[str, Any]:
        """Fetch the welcome screen for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/welcome-screen', guild_id=int(guild)))

    async def edit_welcome_screen(
        self,
        guild: SupportsInt,
        *,
        enabled: Optional[bool] = MISSING,
        welcome_channels: List[Dict[str, Any]] = MISSING,
        description: Optional[str] = MISSING
    ) -> Dict[str, Any]:
        """Edit the guild's welcome screen."""
        if enabled is MISSING and welcome_channels is MISSING and description is MISSING:
            raise TypeError("one of 'enabled', 'welcome_channels' or 'description' is requied")

        payload: Dict[str, Any] = {
            'enabled': enabled,
            'welcome_channels': welcome_channels,
            'description': description
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/welcome-screen', guild_id=int(guild)),
            json=payload
        )

    async def edit_my_voice_state(
        self,
        guild: SupportsInt,
        *,
        channel: SupportsInt,
        suppress: bool = MISSING,
        request_to_speak: int = MISSING
    ) -> Dict[str, Any]:
        """Update the bot user's voice state in that guild."""
        options: Dict[str, Any] = {'channel_id': int(channel)}
        if suppress is not MISSING:
            options['suppress'] = suppress

        if request_to_speak is not MISSING:
            options['request_to_speak_timestamp'] = request_to_speak

        return await self.request(
            Route('PATCH', 'guild/{guild_id}/voice-states/@me', guild_id=int(guild)),
            json=options
        )

    async def edit_voice_state(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        channel: SupportsInt,
        suppress: bool = MISSING
    ) -> Dict[str, Any]:
        """Edit another user's voice state."""
        options: Dict[str, Any] = {'channel': int(channel)}
        if suppress is not MISSING:
            options['suppress'] = suppress

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/voice-states/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), json=options
        )

    # Invite endpoints

    async def fetch_invite(self, code: str) -> Dict[str, Any]:
        """Fetch invite information by its code."""
        return await self.request(Route('GET', '/invites/{invite_code}', invite_code=str(code)))

    async def delete_invite(self, code: str, *, reason: str = MISSING) -> Dict[str, Any]:
        """Delete an invite by its code, this requires certain permissions."""
        return await self.request(
            Route(
                'DELETE', '/invites/{invite_code}', invite_code=str(code)
            ), reason=reason
        )

    # Stage Instance endpoints

    async def create_stage_instance(
        self,
        channel: SupportsInt,
        topic: str,
        privacy_level: int = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new stage instance associated with a stage channel."""
        payload: Dict[str, Any] = {
            'channel_id': int(channel),
            'topic': topic,
            'privacy_level': privacy_level,
        }

        return await self.request(
            Route('POST', '/stage-instances'),
            json=payload, reason=reason
        )

    async def fetch_stage_instance(self, channel: SupportsInt) -> Dict[str, Any]:
        """Fetch the stage instance associated with the stage channel, if it exists."""
        return await self.request(Route(
            'GET', '/stage-instances/{channel_id}', channel_id=int(channel)
        ))

    async def edit_stage_instance(
        self,
        channel: SupportsInt,
        *,
        topic: str = MISSING,
        privacy_level: int = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit fields of an existing stage instance."""
        if topic is MISSING and privacy_level is MISSING:
            raise TypeError("at least one of 'topic' or 'privacy_level' is required")

        payload: Dict[str, Any] = {
            'topic': topic,
            'privacy_level': privacy_level
        }

        return await self.request(
            Route('PATCH', '/stage-instances/{channel_id}', channel_id=int(channel)),
            json=payload, reason=reason
        )

    async def delete_stage_instance(
        self,
        channel: SupportsInt,
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Delete a stage instance by its ID."""
        return await self.request(
            Route('DELETE', '/stage-instances/{channel_id}', channel_id=int(channel)),
            reason=reason
        )
