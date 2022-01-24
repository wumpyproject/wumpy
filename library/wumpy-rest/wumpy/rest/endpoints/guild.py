from typing import (
    Any, Dict, List, Literal, Optional, Sequence, SupportsInt, Union
)

from discord_typings import (
    AuditLogData, BanData, ChannelData, EmojiData, GuildData, GuildMemberData,
    GuildPreviewData, InviteData, RoleData, StageInstanceData
)

from ..route import Route
from ..utils import MISSING
from .base import Requester


class GuildRequester(Requester):

    __slots__ = ()

    # Audit Log endpoints

    async def fetch_audit_logs(
        self,
        guild: SupportsInt,
        *,
        user: SupportsInt = MISSING,
        action_type: int = MISSING,
        before: SupportsInt = MISSING,
        limit: int = MISSING
    ) -> AuditLogData:
        """Fetch the audit log entries for this guild.

        Whenever an admin actions is performed on the API, an entry is added to
        the respective guild's audit log. This endpoint allows fetching these
        audit logs.

        Parameters:
            user: Filter audit logs for actions made by one user.
            action_type: The type of the action that generated an audit log.
            before: Filter for audit logs before a certain audit log.
            limit: The amount of entries to return.

        Returns:
            An audit log object containing entries and attached objects.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=int(guild)),
            params={
                'user_id': int(user), 'action_type': action_type,
                'before': int(before), 'limit': limit
            }
        )

    # Emoji endpoints

    async def fetch_emojis(self, guild: SupportsInt) -> List[EmojiData]:
        """Fetch all emojis in a guild by its ID.

        Parameters:
            guild: The ID of the guild to fetch emojis from.

        Returns:
            A list of emoji objects from the guild.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_emoji(self, guild: SupportsInt, emoji: SupportsInt) -> EmojiData:
        """Fetch a specific emoji from a guild by its ID.

        Parameters:
            guild: The ID of the guild to fetch the emoji from.
            emoji: The ID of the emoji to fetch.

        Returns:
            The data of the emoji fetched.
        """
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
    ) -> EmojiData:
        """Create an emoji in a guild.

        This method requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild to create the emoji in.
            name: The name of the emoji.
            image: The base64 encoded image data of the emoji.
            roles: A list of role IDs to restrict the emoji to.
            reason: The audit log reason for creating the emoji.

        Returns:
            The data of the created emoji object.
        """
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
    ) -> EmojiData:
        """Edit fields of an emoji by its ID.

        This method requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild the emoji is from.
            emoji: The ID of the emoji to edit.
            name: The new name of the emoji.
            roles: A list of role IDs to restrict the emoji to.
            reason: The audit log reason for editing the emoji.

        Returns:
            The updated data of the emoji object.
        """
        if not name and roles == []:
            raise TypeError("one of 'name' or 'roles' is required")

        payload = {
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
    ) -> None:
        """Delete an emoji from a guild.

        This method requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild the emoji is from.
            emoji: The ID of the emoji to delete.
            reason: The audit log reason for deleting the emoji.
        """
        await self.request(
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
        verification_level: Literal[0, 1, 2, 3, 4] = MISSING,
        notification_level: Literal[0, 1] = MISSING,
        content_filter: Literal[0, 1, 2] = MISSING,
        roles: Sequence[RoleData] = MISSING,
        channels: Sequence[ChannelData] = MISSING,
        afk_channel: int = MISSING,
        afk_timeout: int = MISSING,
        system_channel: int = MISSING,
        system_channel_flags: int = MISSING
    ) -> GuildData:
        """Create a new guild, making the bot the owner.

        This method can only be used by bots in less than 10 guilds.

        Parameters:
            name: The (2-100 character) name of the guild.
            icon: The base64 encoded image data icon of the guild.
            verification_level: The verification level of the guild.
            notification_level: The default notification level of the guild.
            content_filter: The content filter level of the guild.
            roles:
                A list of role objects to create in the guild. The `id` field
                in each role object is still required, but an integer
                placeholder can be used to create a guild with pre-made
                permissions set up in its channels. **Note that the first role
                will become the guild's `@everyone` role.**
            channels:
                A list of channel objects to create in the guild. The `id`
                field within each channel object is still required, allowing
                you to setup categories using `parent_id`. Categories must
                come before its children. The `position` field will be ignored
                by the Discord API.
            afk_channel: The ID of the channel to use as the AFK channel.
            afk_timeout:
                The timeout in seconds before the member is moved to the AFK
                channel from inactivity.
            system_channel:
                The ID of the channel to use as the system channel for welcome
                messages and boost messages.
            system_channel_flags:
                Bitfield of system flags. Refer to the Discord API
                documentation for the exact bits you can set and what they do.

        Returns:
            The data of the created guild object.
        """
        payload = {
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

    async def fetch_guild(self, guild: SupportsInt, *, with_counts: bool = False) -> GuildData:
        """Fetch a guild by its ID.

        If `with_counts` is set, `approximate_member_count` and
        `approximate_presence_count` will be included in the guild data.

        Parameters:
            guild: The ID of the guild to fetch.
            with_counts: Whether to include approximate fields in the response.

        Returns:
            The fetched data of the guild object.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}', guild_id=int(guild)),
            params={'with_counts': with_counts}
        )

    async def fetch_guild_preview(self, guild: SupportsInt) -> GuildPreviewData:
        """Fetch a preview of a guild by its ID.

        If the bot user is not in the guild, it must be lurkable - meaning that
        it must be discoverable or have a live public stage.

        Parameters:
            guid: The ID of the guild to fetch a preview of.

        Returns:
            The preview of the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/preview', guild_id=int(guild))
        )

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
        """Delete a guild permanently, the bot must be the owner.

        Parameters:
            guild: The ID of the guild to delete.
        """
        await self.request(
            Route('DELETE', '/guilds/{guild_id}', guild_id=int(guild))
        )

    async def fetch_channels(self, guild: SupportsInt) -> List[ChannelData]:
        """Fetch all channels in a guild, excluding threads.

        Parameters:
            guild: The ID of the guild to fetch channels from.

        Returns:
            A list of channel objects.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/channels', guild_id=int(guild))
        )

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

    async def fetch_active_threads(self, guild: SupportsInt) -> ListActive:
        """Fetch all active threads in a guild, both public and private threads."""
        return await self.request(
            Route('GET', '/guilds/{guild_id}/threads/active', guild_id=int(guild))
        )

    async def fetch_member(self, guild: SupportsInt, user: SupportsInt) -> GuildMemberData:
        """Fetch a specific member object by its user ID.

        Parameters:
            guild: The ID of the guild to fetch the member from.
            user: The ID of the user to fetch member data of.

        Returns:
            The member data of the user.
        """
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
        """Add a role to a guild member.

        It is better to use the `edit_member()` method and pass a list of
        roles to override, allowing you to bulk-add roles to a member.

        Parameters:
            guild: The ID of the guild the member is in.
            user: The ID of the user to add the role to.
            role: The ID of the role to add to the member.
            reason: The audit log reason for adding the role to the member.
        """
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
        """Remove a role from a guild member.

        It is better to use the `edit_member()` method and pass a list of
        roles to override, allowing you to bulk-removes roles from a member.

        Parameters:
            guild: The ID of the guild the member is in.
            user: The ID of the user to remove the role from.
            role: The ID of the role to remove from the member.
            reason: The audit log reason for removing the role from the member.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                guild_id=int(guild), user_id=int(user), role_id=int(role)
            ), reason=reason
        )

    async def kick_member(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Remove a member from a guild, also known as kicking a member.

        This method requires the `KICK_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild the member is in.
            user: The ID of the user to remove from the guild.
            reason: The audit log reason for kicking the member.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_bans(self, guild: SupportsInt) -> List[BanData]:
        """Fetch all bans made on a guild.

        This method requires the `BAN_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild to fetch bans from.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}/bans', guild_id=int(guild)))

    async def fetch_ban(self, guild: SupportsInt, user: SupportsInt) -> BanData:
        """Fetch a specific ban made on a user.

        This method requires the `BAN_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild to fetch the ban from.
            user: The ID of the user that was banned.

        Returns:
            The data about the ban made on the user.
        """
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
        """Ban a specific member from re-joining the guild.

        This method requires the `BAN_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild to ban the member from.
            user: The ID of the user to ban.
            delete_message_days:
                The number of days worth of messages to delete from the user.
                This can be between a value between 0 and 7.
            reason: The audit log reason for banning the member.
        """
        await self.request(
            Route(
                'PUT', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ),
            json={'delete_message_days': delete_message_days}, reason=reason
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

    async def fetch_invite(self, code: str) -> InviteData:
        """Fetch invite information by its code.

        Parameters:
            code: The code of the invite.

        Returns:
            The invite information.
        """
        return await self.request(
            Route('GET', '/invites/{invite_code}', invite_code=str(code))
        )

    async def delete_invite(self, code: str, *, reason: str = MISSING) -> InviteData:
        """Delete an invite by its code.

        This method requires the `MANAGE_CHANNELS` permission on the channel
        that the invite belongs to, or `MANAGE_GUILD` on the guild.

        Parameters:
            code: The code of the invite to delete.
            reason: The reason for deleting the invite.

        Returns:
            The data of the deleted invite.
        """
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
        privacy_level: Literal[1, 2] = MISSING,
        reason: str = MISSING
    ) -> StageInstanceData:
        """Create a new stage instance associated with a stage channel.

        The bot user has to be a moderator of the stage channel.

        Parameters:
            channel: The ID of the stage channel.
            topic: The (1-120 character) topic of the new stage instance.
            privacy_level: The privacy level of the new stage instance.
            reason: The audit log reason for creating the stage instance.

        Returns:
            The data of the new stage instance.
        """
        payload = {
            'channel_id': int(channel),
            'topic': topic,
            'privacy_level': privacy_level,
        }

        return await self.request(
            Route('POST', '/stage-instances'),
            json=payload, reason=reason
        )

    async def fetch_stage_instance(self, channel: SupportsInt) -> StageInstanceData:
        """Fetch the stage instance associated with the stage channel.

        Parameters:
            channel: The ID of the stage channel.

        Returns:
            The data of the stage instance.
        """
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
        """Edit fields of an existing stage instance.

        This method requires that the bot user is a moderator of the stage
        channel.

        Parameters:
            channel: The ID of the stage channel.
            topic: The new (1-120 character) topic of the stage instance.
            privacy_level: The new privacy level of the stage instance.
            reason: The audit log reason for editing the stage instance.

        Returns:
            The data of the edited stage instance.
        """
        if topic is MISSING and privacy_level is MISSING:
            raise TypeError("at least one of 'topic' or 'privacy_level' is required")

        payload = {
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
        """Delete a stage instance by the ID of the stage channel.

        This method requires that the bot user is a moderator of the stage
        channel.

        Parameters:
            channel: The ID of the stage channel.
            reason: The audit log reason for deleting the stage instance.

        Returns:
            The data of the deleted stage instance.
        """
        return await self.request(
            Route('DELETE', '/stage-instances/{channel_id}', channel_id=int(channel)),
            reason=reason
        )
