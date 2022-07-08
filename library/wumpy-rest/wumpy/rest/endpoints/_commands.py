from typing import List, Sequence, SupportsInt

from discord_typings import (
    ApplicationCommandData, ApplicationCommandPayload,
    ApplicationCommandPermissionsData, GuildApplicationCommandPermissionData
)

from .._requester import Requester
from .._route import Route

__all__ = (
    'ApplicationCommandEndpoints',
)


class ApplicationCommandEndpoints(Requester):
    """Endpoints for managing application commands."""

    __slots__ = ()

    async def fetch_global_commands(
        self,
        application: SupportsInt
    ) -> List[ApplicationCommandData]:
        """Fetch all global commands for the application.

        Parameters:
            application: The ID of the application.

        Returns:
            A list of all global commands.
        """
        return await self.request(Route(
            'GET', '/applications/{application_id}/commands',
            application_id=int(application)
        ))

    async def create_global_command(
        self,
        application: SupportsInt,
        payload: ApplicationCommandPayload
    ) -> ApplicationCommandData:
        """Create a global command.

        Global commands can take up to 1 hour to propagate.

        Parameters:
            application: The ID of the application.
            payload: The payload of the command to create.
        """
        return await self.request(Route(
            'POST', '/applications/{application_id}/commands',
            webhook_id=int(application)
        ), json=payload)

    async def fetch_global_command(
        self,
        application: SupportsInt,
        command: SupportsInt
    ) -> ApplicationCommandData:
        """Fetch a specific global command.

        Parameters:
            command: The ID of the command.

        Returns:
            The data for the global command.
        """
        return await self.request(Route(
            'GET', '/applications/{application_id}/commands/{command_id}}',
            application_id=int(application), command_id=int(command)
        ))

    async def edit_global_command(
        self,
        application: SupportsInt,
        command: SupportsInt,
        payload: ApplicationCommandPayload
    ) -> ApplicationCommandData:
        """Edit a global command.

        Changes to global commands can take up to an hour to propagate.

        Parameters:
            application: The ID of the application.
            command: The ID of the command to edit.
            payload: The new payload for the command.

        Returns:
            The new global command data.
        """
        return await self.request(Route(
            'PATCH', '/applications/{application_id}/commands/{command_id}',
            application_id=int(application), command_id=int(command)
        ), json=payload)

    async def delete_global_command(
        self,
        application: SupportsInt,
        command: SupportsInt
    ) -> None:
        """Delete a global command.

        Parameters:
            application: The ID of the application.
            command: The ID of the command to delete.
        """
        await self.request(Route(
            'DELETE', '/applications/{application_id}/commands/{command_id}',
            application_id=int(application), command_id=int(command)
        ))

    async def overwrite_global_commands(
        self,
        application: SupportsInt,
        payloads: Sequence[ApplicationCommandPayload]
    ) -> List[ApplicationCommandData]:
        """Bulk overwrite all global commands.

        This will overwrite all application commands (slash commands, user
        commands and message commands) with the given payloads.

        Parameters:
            application: The ID of the application.
            payloads: The payloads to overwrite all commands with.

        Returns:
            A list of all global commands.
        """
        return await self.request(Route(
            'PUT', '/applications/{application_id}/commands',
            application_id=int(application)
        ), json=payloads)

    async def fetch_guild_commands(
        self,
        application: SupportsInt,
        guild: SupportsInt
    ) -> List[ApplicationCommandData]:
        """Fetch all commands created for a guild.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.

        Returns:
            A list of all commands for the guild.
        """
        return await self.request(Route(
            'GET', '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=int(application), guild_id=int(guild)
        ))

    async def create_guild_command(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        payload: ApplicationCommandPayload
    ) -> ApplicationCommandData:
        """Create a guild-specific command.

        Compared to global commands, guild commands will be available
        immediately.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            payload: The payload of the command to create.

        Returns:
            The data for the created guild command.
        """
        return await self.request(Route(
            'POST', '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=int(application), guild_id=int(guild)
        ), json=payload)

    async def fetch_guild_command(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        command: SupportsInt
    ) -> ApplicationCommandData:
        """Fetch a specific guild command.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            command: The ID of the command.

        Returns:
            The data for the guild command.
        """
        return await self.request(Route(
            'GET', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=int(application), guild_id=int(guild), command_id=int(command)
        ))

    async def edit_guild_command(
        self,
        application: SupportsInt,
        command: SupportsInt,
        guild: SupportsInt,
        payload: ApplicationCommandPayload
    ) -> ApplicationCommandData:
        """Edit a guild command's data.

        Compared to global commands, guild commands will be available
        immediately.

        Parameters:
            application: The ID of the application.
            command: The ID of the command to edit.
            guild: The ID of the guild.
            payload: The new payload for the command.

        Returns:
            The new guild command data.
        """
        return await self.request(Route(
            'PATCH', '/applications/{application_id}/guilds/{guild_id}commands/{command_id}',
            application_id=int(application), guild_id=int(guild), command_id=int(command)
        ), json=payload)

    async def delete_guild_command(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        command: SupportsInt
    ) -> None:
        """Delete a guild specific command.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            command: The ID of the command to delete.
        """
        await self.request(Route(
            'DELETE', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=int(application), guild_id=int(guild), command_id=int(command)
        ))

    async def overwrite_guild_commands(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        payloads: List[ApplicationCommandPayload]
    ) -> List[ApplicationCommandData]:
        """Bulk overwrite a guild's all commands.

        This will overwrite all application commands (slash commands, user
        commands and message commands) with the given payloads.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            payloads: The payloads to overwrite all commands with.

        Returns:
            A list of all global commands.
        """
        return await self.request(Route(
            'PUT', '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=int(application), guild_id=int(guild)
        ), json=payloads)

    async def fetch_all_guild_command_permissions(
        self,
        application: SupportsInt,
        guild: SupportsInt
    ) -> List[GuildApplicationCommandPermissionData]:
        """Fetch all permissions for all commands in a guild.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.

        Returns:
            A list of guild application command permissions.
        """
        return await self.request(Route(
            'GET', '/application/{application_id}/guilds/{guild_id}/commands/permissions',
            application_id=int(application), guild_id=int(guild)
        ))

    async def fetch_guild_command_permissions(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        command: SupportsInt
    ) -> GuildApplicationCommandPermissionData:
        """Fetch a specific guild command's permissions.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            command: The ID of the command.

        Returns:
            The guild application command permissions.
        """
        return await self.request(Route(
            'GET', '/application/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=int(application), guild_id=int(guild), command_id=int(command)
        ))

    async def edit_guild_command_permissions(
        self,
        application: SupportsInt,
        guild: SupportsInt,
        command: SupportsInt,
        permissions: Sequence[ApplicationCommandPermissionsData],
    ) -> GuildApplicationCommandPermissionData:
        """Edit a guild command's permissions.

        Parameters:
            application: The ID of the application.
            guild: The ID of the guild.
            command: The ID of the command.
            permissions: The new permissions for the commands.

        Returns:
            The new guild application command permissions.
        """
        return await self.request(Route(
            'PUT', '/application/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=int(application), guild_id=int(guild), command_id=int(command)
        ), json={'permissions': permissions})
