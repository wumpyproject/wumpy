from typing import Any, List, Optional, Sequence, SupportsInt, Union, overload

from discord_typings import (
    AuditLogData, AutoModerationActionData, AutoModerationRuleData,
    AutoModerationTriggerMetadataData, BanData, ChannelData,
    ChannelPositionData, EmojiData, GuildData, GuildMemberData,
    GuildPreviewData, GuildScheduledEventData,
    GuildScheduledEventEntityMetadata, GuildScheduledEventEntityTypes,
    GuildScheduledEventPrivacyLevels, GuildScheduledEventStatus,
    GuildScheduledEventUserData, GuildWidgetData, GuildWidgetSettingsData,
    IntegrationData, InviteData, ListThreadsData, PermissionOverwriteData,
    RoleData, RolePositionData, StageInstanceData, VoiceRegionData,
    WelcomeChannelData, WelcomeScreenData
)
from typing_extensions import Literal

from .._requester import Requester
from .._route import Route
from .._utils import MISSING

__all__ = (
    'GuildEndpoints',
)


class GuildEndpoints(Requester):
    """Guild-related endpoints under `/guilds/`."""

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

    # Auto Moderation endpoints

    async def fetch_automod_rules(self, guild: SupportsInt) -> List[AutoModerationRuleData]:
        """Fetch all rules configured in a guild by its ID.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch rules from.

        Returns:
            A list of automod rules.
        """
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/auto-moderation/rules', guild_id=int(guild)
        ))

    async def fetch_automod_rule(
            self,
            guild: SupportsInt,
            rule: SupportsInt
    ) -> AutoModerationRuleData:
        """Fetch a specific automod rule in a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild the rule is in,
            rule: The ID of the automod rule to fetch.

        Returns:
            The automod rule object.
        """
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/auto-moderation/rules/{automod_rule}',
            guild_id=int(guild), automod_rule=int(rule)
        ))

    async def create_automod_rule(
            self,
            guild: SupportsInt,
            *,
            name: str,
            event_type: int,
            trigger_type: int,
            actions: List[AutoModerationActionData],
            trigger_metadata: AutoModerationTriggerMetadataData = MISSING,
            enabled: bool = MISSING,
            exempt_roles: List[SupportsInt] = MISSING,
            exempt_channels: List[SupportsInt] = MISSING,
            reason: str = MISSING,
    ) -> AutoModerationRuleData:
        """Create a new automoderation rule.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to create the automod rule in.
            name: The name of the rule.
            event_type: The type of event to check the rule for.
            trigger_type: The type of trigger the rule checks.
            trigger_metadata: Additional metadata when checking the trigger.
            actions: A list of actions to execute when the rule is triggered.
            enabled: Whether the rule is enabled.
            exempt_roles: Role IDs which should not be affected by the rule.
            exempt_channels: Channel IDs which should not be affected.
            reason: The audit log reason for creating the rule.

        Returns:
            The newly created automod rule object.
        """
        payload = {
            'name': name,
            'event_type': event_type,
            'trigger_type': trigger_type,
            'trigger_metadata': trigger_metadata,
            'actions': actions,
            'enabled': enabled,
            'exempt_roles': [int(r) for r in exempt_roles] if exempt_roles else MISSING,
            'exempt_channels': [
                int(c) for c in exempt_channels
            ] if exempt_channels else MISSING,
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/auto-moderation/rules', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_automod_rule(
            self,
            guild: SupportsInt,
            rule: SupportsInt,
            *,
            name: str = MISSING,
            event_type: int = MISSING,
            trigger_type: int = MISSING,
            actions: List[AutoModerationActionData] = MISSING,
            trigger_metadata: AutoModerationTriggerMetadataData = MISSING,
            enabled: bool = MISSING,
            exempt_roles: List[SupportsInt] = MISSING,
            exempt_channels: List[SupportsInt] = MISSING,
            reason: str = MISSING,
    ) -> AutoModerationRuleData:
        """Edit an existing automoderation rule.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to create the automod rule in.
            name: The name of the rule.
            event_type: The type of event to check the rule for.
            trigger_type: The type of trigger the rule checks.
            trigger_metadata: Additional metadata when checking the trigger.
            actions: A list of actions to execute when the rule is triggered.
            enabled: Whether the rule is enabled.
            exempt_roles: Role IDs which should not be affected by the rule.
            exempt_channels: Channel IDs which should not be affected.
            reason: The audit log reason for editing the rule.

        Returns:
            The newly created automod rule object.
        """
        payload = {
            'name': name,
            'event_type': event_type,
            'trigger_type': trigger_type,
            'trigger_metadata': trigger_metadata,
            'actions': actions,
            'enabled': enabled,
            'exempt_roles': [int(r) for r in exempt_roles] if exempt_roles else MISSING,
            'exempt_channels': [
                int(c) for c in exempt_channels
            ] if exempt_channels else MISSING,
        }
        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/auto-moderation/rules/{automod_rule}',
                guild_id=int(guild), automod_rule=int(rule)
            ),
            json=payload, reason=reason
        )

    async def delete_automod_rule(
            self,
            guild: SupportsInt,
            rule: SupportsInt,
            *,
            reason: str = MISSING,
    ) -> None:
        """Delete an automod rule by its ID.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild the automod rule is in.
            rule: The ID of the automod rule to delete.
            reason: The audit log reason for deleting the rule.
        """
        return await self.request(Route(
            'DELETE', '/guilds/{guild_id}/auto-moderation/{automod_rule}',
            guild_id=int(guild), automod_rule=int(rule), reason=reason
        ))

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
            guild: The ID of the guild to fetch a preview of.

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
        premium_progress_bar: bool = MISSING,
        reason: str = MISSING
    ) -> GuildData:
        """Edit a guild's settings.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to edit.
            name: The new name of the guild.
            verification_level: The new verification level of the guild.
            notification_level: The new notification level of the guild.
            content_filter: The new explicit content filter level of the guild.
            afk_channel:
                The ID of the channel to use as the AFK channel, where members
                are moved when they are considered AFK.
            afk_timeout:
                The timeout in seconds before the member is moved to the AFK
                channel from inactivity.
            icon: The base64 encoded image data of the new guild icon.
            owner:
                The ID of the new owner of the guild. The bot must be the
                owner of the guild.
            splash: The new base64 encoded image data for a new guild splash.
            discovery:
                The new base64 encoded image data for a new discovery splash
                image of the guild.
            banner: The new base64 encoded image data for a new guild banner.
            system_channel:
                The ID of the channel to use as the system channel for welcome
                messages and boost messages.
            system_channel_flags:
                Bitfield of system flags. Refer to the Discord API for specific
                bits and what they do.
            rules_channel: The ID of the channel to use as the rules channel.
            updates_channel:
                The ID of the channel to use as the updates channel where
                admins and moderators receive official Community updates
                from Discord.
            preferred_locale: The new preferred locale of the guild.
            features: Enabled features of the guild.
            description: The new description of the guild.
            premium_progress_bar: Whether to show the guild's premium progress.
            reason: The audit log reason for editing the guild's settings.

        Returns:
            The updated data of the guild object.
        """
        payload = {
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
            'description': description,
            'premium_progress_bar_enabled': premium_progress_bar
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
        type: Literal[0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13] = MISSING,
        topic: str = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rate_limit: int = MISSING,
        position: int = MISSING,
        permission_overwrites: List[PermissionOverwriteData] = MISSING,
        parent: SupportsInt = MISSING,
        nsfw: bool = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
        """Create a new guild channel.

        This requires the `MANAGE_CHANNELS` permission. If permission
        overwrites are changed, only permissions your bot user has in the guild
        can be updated. Setting `MANAGE_ROLES` is only possible for guild
        administrators.

        Parameters:
            guild: The ID of the guild to create the channel in.
            name: The (1-100 character) name of the new channel.
            type: The type of the new channel.
            topic: The (0-1024 character) topic of the new channel.
            bitrate: The bitrate of the new channel if it is a voice channel.
            user_limit:
                The limit of users able to be in the voice channel at the same
                time.
            rate_limit:
                The amount of seconds a user has to wait before sending another
                message (0-21600). Bots and users with the `MANAGE_MESSAGES` or
                `MANAGE_CHANNELS` permission bypass this.
            position: The position of the new channel.
            permission_overwrites:
                A list of permission overwrite objects to apply to the new
                channel upon creation.
            parent: The ID of the parent category to create the channel in.
            nsfw: Whether the channel should be marked NSFW or not.

        Returns:
            The created channel object.
        """
        payload = {
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
        channels: List[ChannelPositionData],
        *,
        reason: str = MISSING
    ) -> None:
        """Edit several channels' positions.

        This requires the `MANAGE_CHANNELS` permission.

        Parameters:
            guild: The ID of the guild to edit the channels in.
            channels:
                A list of a special type of position data with `id`,
                `position`, `lock_permissions` (whether to sync permissions
                with the new parent, if moving to a new category) and
                `parent_id` keys. All fields are optional (can be None) except
                for `id` which is required.
            reason: The audit log reason for editing the channels.
        """
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/channels', guild_id=int(guild)),
            json=channels, reason=reason
        )

    async def fetch_active_threads(self, guild: SupportsInt) -> ListThreadsData:
        """Fetch all active threads in a guild.

        This endpoint returns both public and private threads, sorted by their
        `id` snowflake in descending order.

        Parameters:
            guild: The ID of the guild to fetch threads from.

        Returns:
            A special payload with `threads` and `members` keys containing
            channel, respectively tread member objects.
        """
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
            'GET', '/guilds/{guild_id}/members/{user_id}',
            guild_id=int(guild), user_id=int(user)
        ))

    async def fetch_members(
        self,
        guild: SupportsInt,
        *,
        limit: int = MISSING,
        after: int = MISSING
    ) -> List[GuildMemberData]:
        """Fetch all members in a guild.

        This endpoint requires the `GUILD_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild to fetch members from.
            limit:
                The maximum number of members to return (1-1000). Defaulting
                to 1 on the API side.
            after:
                The ID of the highest user in the previous page. This defaults
                to 0 on the API side to fetch the first page.

        Returns:
            A list of member objects.
        """
        if 0 > limit > 1001:
            raise TypeError("'limit' must be a value between 1-1000")

        return await self.request(
            Route('GET', '/guilds/{guild_id}/members', guild_id=int(guild)),
            params={'limit': limit, 'after': after}
        )

    async def search_members(
        self,
        guild: SupportsInt,
        query: str,
        *,
        limit: int = MISSING
    ) -> List[GuildMemberData]:
        """Search guild members after a name or nickname starting with `query`.

        Parameters:
            guild: The ID of the guild to search members in.
            query: The string to search for by usernames and nicknames.
            limit:
                The maximum number of members to return (1-1000). Similar to
                `fetch_members()` this will default to 1 on the API side.

        Returns:
            A list of member objects.
        """
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
        timeout: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> GuildMemberData:
        """Edit another guild member.

        This endpoint requires a few different permissions depending on the
        options passed, including `MANAGE_NICKNAMES`, `MANAGE_ROLES`,
        `MUTE_MEMBERS`, `DEAFEN_MEMBERS`, `MOVE_MEMBERS` and `MODERATE_MEMBERS`
        respectively.

        Parameters:
            guild: The ID of the guild to edit the member in.
            user: The ID of the user to edit.
            nick: The new nickname of the member.
            roles: A list of role IDs to set to the member (add and remove).
            mute: Whether to mute the member in voice channels.
            deafen: Whether to deafen the member in voice channels.
            channel: The ID of the voice channel to move the member to.
            timeout:
                The number of seconds to timeout the member for. This can be
                set up until 28 days in the future.

        Returns:
            The updated data of the member object.
        """
        payload = {
            'nick': nick,
            'roles': [int(r) for r in roles] if roles else roles,
            'mute': mute,
            'deaf': deafen,
            'channel_id': int(channel) if channel else channel,
            'communication_disabled_until': timeout,
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
        nick: Optional[str] = MISSING,
        *,
        reason: str = MISSING
    ) -> GuildMemberData:
        """Edit the nickname of the bot user in the guild.

        Parameters:
            guild: The ID of the guild to edit the nickname in.
            nick: The new nickname of the bot user. Set to None to reset it.

        Returns:
            The updated data of the member object.
        """
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/members/@me/nick', guild_id=int(guild)),
            json={'nick': nick}, reason=reason
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

    async def pardon_user(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Pardon a user and remove their ban.

        This method requires the `BAN_MEMBERS` permission.

        Parameters:
            guild: The ID of the guild to pardon the user from.
            user: The ID of the user to pardon.
            reason: The audit log reason for removing the ban.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_roles(self, guild: SupportsInt) -> List[Any]:
        """Fetch all roles from a guild.

        Parameters:
            guild: The ID of the guild to fetch roles from.

        Returns:
            A list of roles present in the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/roles', guild_id=int(guild))
        )

    async def create_role(
        self,
        guild: SupportsInt,
        *,
        name: str = "new role",
        permissions: Union[str, int] = MISSING,
        color: int = 0,
        hoist: bool = False,
        icon: str = MISSING,
        unicode_emoji: str = MISSING,
        mentionable: bool = False,
        reason: str = MISSING
    ) -> RoleData:
        """Create a new role in a guild.

        This method requires the `MANAGE_ROLES` permission.

        Parameters:
            guild: The ID of the guild to create the role in.
            name: The name of the role, defaults to `"new role"`.
            permissions: The permissions to assign to the role.
            color: The color of the role, defaults to `0`.
            hoist:
                Whether to hoist the role in the members list, displaying them
                separately in the sidebar. This defaults to `False`.
            icon: The base64 image data for the icon of the role.
            unicode_emoji:
                The unicode emoji (renders as twemoji in the client) to use for
                the role. This is mutually exclusive with `icon`.
            mentionable: Whether anyone can mention the role.

        Returns:
            The newly created role data.
        """
        payload = {
            'name': name,
            'permissions': str(permissions) if permissions else MISSING,
            'color': color,
            'hoist': hoist,
            'icon': icon,
            'unicode_emoji': unicode_emoji,
            'mentionable': mentionable
        }

        return await self.request(
            Route('POST', '/guilds/{guild_id}/roles', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_role_positions(
        self,
        guild: SupportsInt,
        roles: List[RolePositionData],
        reason: str = MISSING
    ) -> List[RoleData]:
        """Edit several roles' positions at the same time.

        This method requires the `MANAGE_ROLES` permission.

        Parameters:
            guild: The ID of the guild to edit the roles in.
            roles: A list of payloads with `id ` and `position` fields.
            reason: The audit log reason for moving the roles.

        Returns:
            All of the guild's roles.
        """
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
        icon: Optional[str] = MISSING,
        unicode_emoji: Optional[str] = MISSING,
        mentionable: Optional[bool] = MISSING,
        reason: str = MISSING
    ) -> RoleData:
        """Edit a guild role's different fields.

        This method requires the `MANAGE_ROLES` permission.

        Parameters:
            guild: The ID of the guild the role is in.
            role: The ID of the role to edit.
            name: The new name of the role.
            permissions: The new permissions of the role.
            color: The new color of the role.
            hoist: Whether to hoist the role in the members list.
            icon: The base64 image data for the new icon of the role.
            unicode_emoji: The unicode emoji to use as the role icon.
            mentionable: Whether anyone can mention the role.
            reason: The audit log reason for editing the role.

        Returns:
            The newly edited role data.
        """
        payload = {
            'name': name,
            'permissions': str(permissions) if permissions else permissions,
            'color': color,
            'hoist': hoist,
            'icon': icon,
            'unicode_emoji': unicode_emoji,
            'mentionable': mentionable
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/roles/{role_id}',
                guild_id=int(guild), role_id=int(role)
            ),
            json=payload, reason=reason
        )

    async def delete_role(
        self,
        guild: SupportsInt,
        role: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a role from a guild.

        This method requires the `MANAGE_ROLES` permission.

        Parameters:
            guild: The ID of the guild to delete the role from.
            role: The ID of the role to delete.
            reason: The audit log reason for deleting the role.
        """
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
    ) -> int:
        """Fetch the amount of members that would be pruned.

        This requires the `KICK_MEMBERS` permission.

        By default, pruning will not touch any users with roles. Use the
        `roles` kwarg to add roles that should be included.

        Parameters:
            guild: The ID of the guild to fetch the prune count for.
            days: The number of days of inactivity to consider for pruning.
            roles: A list of role IDs that should be included in the prune.

        Returns:
            The amount of members that would be pruned.
        """
        # Roles may be a list of role object, first we int() them for the IDs
        # and then convert them to strings to join them
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        data = await self.request(
            Route('GET', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            params={'days': days, 'include_roles': include_roles}
        )
        return data['pruned']

    @overload
    async def prune_guild(
        self,
        guild: SupportsInt,
        *,
        days: int = ...,
        compute_count: Literal[True] = ...,
        roles: Optional[Sequence[SupportsInt]] = ...,
        reason: str = ...
    ) -> int:
        ...

    @overload
    async def prune_guild(
        self,
        guild: SupportsInt,
        *,
        days: int = ...,
        compute_count: Literal[False] = ...,
        roles: Optional[Sequence[SupportsInt]] = ...,
        reason: str = ...
    ) -> None:
        ...

    async def prune_guild(
        self,
        guild: SupportsInt,
        *,
        days: int = MISSING,
        compute_count: bool = True,
        roles: Optional[Sequence[SupportsInt]] = MISSING,
        reason: str = MISSING
    ) -> Optional[int]:
        """Begin a prune operation.

        This requires the `KICK_MEMBERS` permission.

        For very large guilds it is recommended to set `compute_count` to
        `False`. This will force the return value to be None.

        By default, pruning will not touch any users with roles. Use the
        `roles` kwarg to add roles that should be included.

        Parameters:
            guild: The ID of the guild to prune.
            days: The number of days of inactivity to consider for pruning.
            compute_count: Whether to wait and return the prune count.
            roles: A list of role IDs that should be included in the prune.
            reason: The audit log reason for pruning the guild.

        Returns:
            The amount of members pruned, if `compute_count` is `True`.
        """
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        data = await self.request(
            Route('POST', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            json={'days': days, 'compute_prune_count': compute_count, 'include_roles': include_roles},
            reason=reason
        )
        return data['pruned']

    async def fetch_voice_regions(self, guild: SupportsInt = MISSING) -> List[VoiceRegionData]:
        """Fetch a list of voice regions.

        If a guild is passed, this may return VIP servers if the guild
        is VIP-enabled.

        Parameters:
            guild:
                The ID of the guild to fetch the voice regions for, otherwise
                all (non-VIP) voice regions will be fetched.

        Returns:
            A list of voice region data.
        """
        if guild is MISSING:
            return await self.request(Route('GET', '/voice/regions'))

        return await self.request(
            Route('GET', '/guilds/{guild_id}/regions', guild_id=int(guild))
        )

    async def fetch_guild_invites(self, guild: SupportsInt) -> List[InviteData]:
        """Fetch all invites for a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch all invites from.

        Returns:
            A list of all invites for the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/invites', guild_id=int(guild))
        )

    async def fetch_integrations(self, guild: SupportsInt) -> List[IntegrationData]:
        """Fetch all intergration for a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch all integrations from.

        Returns:
            A list of integrations for the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/integrations', guild_id=int(guild))
        )

    async def delete_integration(
        self,
        guild: SupportsInt,
        integration: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete an attached integration for the guild.

        This method requires the `MANAGE_GUILD` permission.

        This may also delete any associated webhooks and kick the bot if
        there is one attached.

        Parameters:
            guild: The ID of the guild to delete the integration from.
            integration: The ID of the integration to delete.
            reason: The audit log reason for deleting the integration.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/integrations/{integration_id}',
                guild_id=int(guild), integration_id=int(integration)
            ), reason=reason
        )

    async def fetch_widget_settings(self, guild: SupportsInt) -> GuildWidgetSettingsData:
        """Fetch the settings for a widget for a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch the widget settins for.

        Returns:
            The widget settings for the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/widget', guild_id=int(guild))
        )

    async def edit_widget(
        self,
        guild: SupportsInt,
        *,
        enabled: bool = MISSING,
        channel: Optional[SupportsInt] = MISSING,
        reason: str = MISSING
    ) -> GuildWidgetSettingsData:
        """Edit a guild's widget settings.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to edit the widget settings for.
            enabled: Whether the widget is enabled.
            channel: The ID of the channel the widget should display.
            reason: The audit log reason for editing the widget settings.

        Returns:
            The updated widget settings.
        """
        payload = {
            'enabled': enabled,
            'channel_id': int(channel) if channel else channel
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/widget', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def fetch_widget(self, guild: SupportsInt) -> GuildWidgetData:
        """Fetch a complete widget for a guild.

        Parameters:
            guild: The ID of the guild to fetch a widget for.

        Returns:
            The full widget for the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/widget.json', guild_id=int(guild))
        )

    async def fetch_vanity_invite(self, guild: SupportsInt) -> InviteData:
        """Fetch a partial invite for a guild that has a vanity invite.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch a vanity invite for.

        Returns:
            The vanity invite for the guild. If the guild does not have a
            vanity invite, the `code` key will be `None`.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/vanity-url', guild_id=int(guild))
        )

    async def read_widget_image(
        self,
        guild: SupportsInt,
        *,
        style: Literal['shield', 'banner1', 'banner2', 'banner3', 'banner4'] = 'shield'
    ) -> bytes:
        """Read a guild's widget image.

        Parameters:
            guild: The ID of the guild to read the widget image for.
            style:
                The style of the widget image, has to be one of `'shield'`,
                `'banner1'`, `'banner2'`, `'banner3'`, or `'banner4'`.

        Returns:
            The raw image data for the guild's widget.
        """
        return await self._bypass_request(
            'GET',
            Route.BASE + f'/guilds/{int(guild)}/widget.png',
            params={'style': style}
        )

    async def fetch_welcome_screen(self, guild: SupportsInt) -> WelcomeScreenData:
        """Fetch the welcome screen for a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch the welcome screen for.

        Returns:
            The welcome screen for the guild.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/welcome-screen', guild_id=int(guild))
        )

    async def edit_welcome_screen(
        self,
        guild: SupportsInt,
        *,
        enabled: Optional[bool] = MISSING,
        welcome_channels: List[WelcomeChannelData] = MISSING,
        description: Optional[str] = MISSING
    ) -> WelcomeScreenData:
        """Edit the guild's welcome screen.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to edit the welcome screen for.
            enabled: Whether the welcome screen is enabled.
            welcome_channels:
                A list of welcome screen channel data with their display
                options for the welcome screen.
            description: The server description to show in the welcome screen.

        Returns:
            The updated welcome screen.
        """
        if enabled is MISSING and welcome_channels is MISSING and description is MISSING:
            raise TypeError("one of 'enabled', 'welcome_channels' or 'description' is requied")

        payload = {
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
        request_to_speak: Optional[str] = MISSING
    ) -> Any:  # TODO: What does this return?
        """Update the bot user's voice state in that guild.

        This endpoint can only be used when `channel` is already a stage
        channel, and the bot must be in that channel. The `MUTE_MEMBERS`
        permission is required to set `supress` to False and the
        `REQUEST_TO_SPEAK` permission is required to set `request_to_speak`.

        Parameters:
            guild: The ID of the guild to update the bot's voice state in.
            channel: The ID of the voice channel the bot user is in.
            suppress: Whether the bot user's voice should be suppressed.
            request_to_speak:
                A ISO8601 timestamp of when the bot user should ask to speak.
        """
        payload = {
            'channel_id': int(channel),
            'suppress': suppress,
            'request_to_speak_timestamp': request_to_speak,
        }

        return await self.request(
            Route('PATCH', 'guild/{guild_id}/voice-states/@me', guild_id=int(guild)),
            json=payload
        )

    async def edit_voice_state(
        self,
        guild: SupportsInt,
        user: SupportsInt,
        *,
        channel: SupportsInt,
        suppress: bool = MISSING
    ) -> Any:  # TODO: What does this return?
        """Edit another user's voice state.

        This endpoint can only be used when `channel` is already a stage
        channel, and the bot must be in that channel. The `MUTE_MEMBERS`
        permission is required since `supress` is the only option in the
        Discord API currently.

        Parameters:
            guild: The ID of the guild to update the user's voice state in.
            user: The ID of the user to update the voice state for.
            channel: The ID of the voice channel the user is in.
            suppress: Whether the user's voice should be suppressed.
        """
        payload = {
            'channel': int(channel),
            'suppress': suppress,
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/voice-states/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), json=payload
        )

    # Guild Scheduled Events endpoints

    async def fetch_scheduled_events(
            self,
            guild: SupportsInt,
            *,
            with_counts: bool = MISSING,
    ) -> List[GuildScheduledEventData]:
        """Fetch all current scheduled events for a guild.

        Parameters:
            guild: The ID of the guild.
            with_counts: Whether to include user-counts.

        Returns:
            A list of guild scheduled events.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/scheduled-events', guild_id=int(guild)),
            params={'with_user_count': with_counts}
        )

    async def create_scheduled_event(
            self,
            guild: SupportsInt,
            *,
            name: str,
            privacy_level: GuildScheduledEventPrivacyLevels,
            entity_type: GuildScheduledEventEntityTypes,
            start_time: str,
            description: str = MISSING,
            channel: SupportsInt = MISSING,
            entity_metadata: GuildScheduledEventEntityMetadata = MISSING,
            end_time: str = MISSING,
            image: str = MISSING,
            reason: str = MISSING,
    ) -> GuildScheduledEventData:
        """Create a new scheduled event in a guild.

        Guild can have up to 100 scheduled or active events at a time.

        Parameters:
            guild: The ID of the guild to schedule the event in.
            name: The name of the scheduled event.
            privacy_level: The privacy level of the scheduled event.
            entity_type: The type of the scheduled event entity.
            start_time: The ISO8601 timestamp of when the event starts.
            description: The longer description of the scheduled event.
            channel: The channel that the scheduled event will take place.
            entity_metadata:
                Additional metadata about the scheduled event, having to do
                with its entity.
            end_time: The ISO8601 timestamp of when the event ends.
            image: The cover image for the scheduled event.
            reason: The audit log reason for creating the scheduled event.

        Returns:
            The created scheduled event.
        """
        payload = {
            'channel_id': int(channel) if channel is not MISSING else MISSING,
            'entity_metadata': entity_metadata,
            'name': name,
            'privacy_level': privacy_level,
            'scheduled_start_time': start_time,
            'scheduled_end_time': end_time,
            'description': description,
            'entity_type': entity_type,
            'image': image,
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/scheduled-events', guild_id=int(guild)),
            json=payload, reason=reason,
        )

    async def fetch_scheduled_event(
            self,
            guild: SupportsInt,
            scheduled_event: SupportsInt,
            *,
            with_counts: bool = MISSING
    ) -> GuildScheduledEventData:
        """Fetch a scheduled event in a guild by its ID.

        Parameters:
            guild: The ID of the guild the scheduled even is in.
            scheduled_event: The scheduled event to fetch.
            with_counts: Whether to include user counts.

        Returns:
            The guild scheduled event object from Discord.
        """
        return await self.request(
            Route(
                'GET', '/guilds{guild_id}/scheduled-events/{scheduled_event}',
                guild_id=int(guild), scheduled_event=int(scheduled_event)
            ),
            params={'with_user_count': with_counts}
        )

    async def edit_scheduled_event(
            self,
            guild: SupportsInt,
            scheduled_event: SupportsInt,
            *,
            status: GuildScheduledEventStatus = MISSING,
            name: str = MISSING,
            privacy_level: GuildScheduledEventPrivacyLevels = MISSING,
            entity_type: GuildScheduledEventEntityTypes = MISSING,
            start_time: str = MISSING,
            description: Optional[str] = MISSING,
            channel: Optional[SupportsInt] = MISSING,
            entity_metadata: Optional[GuildScheduledEventEntityMetadata] = MISSING,
            end_time: str = MISSING,
            image: str = MISSING,
            reason: str = MISSING,
    ) -> GuildScheduledEventData:
        """Edit a scheduled event for a guild.

        This method is used to start or end an event by modifying its status.

        Parameters:
            guild: The ID of the guild to schedule the event in.
            scheduled_event: The ID of the scheduled event.
            status: The new status of the scheduled event.
            name: The new name of the scheduled event.
            privacy_level: The new privacy level of the scheduled event.
            entity_type: The new type of the scheduled event entity.
            start_time: The new ISO8601 timestamp of when the event starts.
            description: The new longer description of the scheduled event.
            channel: The new channel that the scheduled event will take place.
            entity_metadata:
                The new metadata about the scheduled event, having to do
                with its entity.
            end_time: The new ISO8601 timestamp of when the event ends.
            image: The new cover image for the scheduled event.
            reason: The audit log reason for editing the scheduled event.

        Returns:
            The updated and new guild scheduled event.
        """
        if channel is not None and channel is not MISSING:
            channel = int(channel)

        payload = {
            'status': status,
            'channel_id': channel,
            'entity_metadata': entity_metadata,
            'name': name,
            'privacy_level': privacy_level,
            'scheduled_start_time': start_time,
            'scheduled_end_time': end_time,
            'description': description,
            'entity_type': entity_type,
            'image': image,
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/scheduled-events/{scheduled_event}',
                guild_id=int(guild), scheduled_event=int(scheduled_event)
            ),
            json=payload
        )

    async def delete_scheduled_event(
            self,
            guild: SupportsInt,
            scheduled_event: SupportsInt,
            *,
            reason: str = MISSING
    ) -> None:
        """Delete a scheduled event.

        Parameters:
            guild: The ID of the guild the scheduled event is in.
            scheduled_event: The ID of the scheduled event.
            reason: The audit log reason for deleting the scheduled event.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/scheduled-events/{scheduled_event}',
                guild_id=int(guild), scheduled_event=int(scheduled_event)
            ),
            reason=reason
        )

    async def fetch_scheduled_event_users(
            self,
            guild: SupportsInt,
            scheduled_event: SupportsInt,
            *,
            limit: int = 100,
            with_member: bool = False,
            before: SupportsInt = MISSING,
            after: SupportsInt = MISSING
    ) -> List[GuildScheduledEventUserData]:
        """Fetch currently interested users for a scheduled event.

        Parameters:
            guild: The ID of the guild the scheduled event is in.
            scheduled_event: The ID of the scheduled event.
            limit: Maximm number of users to return.
            with_member: Whether to include member information in the response.
            before: User ID to only return users before.
            after: User ID to only return users after.

        Return:
            A list of scheduled event users, with a `guild_scheduled_event_id`,
            `user` and potentially `member` key.
        """
        params = {
            'limit': limit,
            'with_member': with_member,
            'before': before,
            'after': after,
        }

        return await self.request(
            Route(
                'GET', '/guilds/{guild_id}/scheduled-events/{scheduled_event}/users',
                guild_id=int(guild), scheduled_event=int(scheduled_event)
            ),
            params=params
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
    ) -> StageInstanceData:
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
    ) -> StageInstanceData:
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
