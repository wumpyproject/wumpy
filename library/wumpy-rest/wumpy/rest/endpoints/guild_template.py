from typing import Any, Dict, List, Optional, SupportsInt

from discord_typings import GuildData, GuildTemplateData

from ..route import Route
from ..utils import MISSING
from .base import Requester


class GuildTemplateRequester(Requester):

    __slots__ = ()

    async def fetch_guild_template(self, code: str) -> GuildTemplateData:
        """Fetch a guild template by its code.

        Parameters:
            code: The string code of the guild template.

        Returns:
            The guild template object from Discord.
        """
        return await self.request(Route(
            'GET', '/guilds/templates/{template_code}', template_code=str(code)
        ))

    async def create_guild_from_template(
        self,
        template: str,
        *,
        name: str,
        icon: Optional[str] = None
    ) -> GuildData:
        """Create a new guild based on a template.

        Only bots that are in less than 10 guilds can use this method.

        Parameters:
            template: The code of the guild template.
            name: The name of the created guild.
            icon: The optional icon for the created guild.

        Returns:
            The newly created guild from the template.
        """
        return await self.request(
            Route('POST', '/guilds/templates/{template_code}', template_code=str(template)),
            json={'name': name, 'icon': icon}
        )

    async def fetch_guild_templates(self, guild: SupportsInt) -> List[GuildTemplateData]:
        """Fetch a list of all guild templates created from a guild.

        This method requires the `MANAGE_GUILD` permission.

        Parameters:
            guild: The ID of the guild to fetch templates from.

        Returns:
            A list of guild templates.
        """
        return await self.request(
            Route('GET', '/guilds/{guild_id}/templates', guild_id=int(guild))
        )

    async def create_guild_template(
        self,
        guild: SupportsInt,
        *,
        name: str,
        description: Optional[str] = None
    ) -> GuildTemplateData:
        """Create a template from a guild.

        This method requires the `MANAGE_GUILD` permission in the guild.

        Parameters:
            guild: The ID of the guild to create a template from.
            name: The 1-100 character name of the template.
            description: The 0-120 character description of the template.

        Returns:
            The created guild template.
        """
        return await self.request(
            Route('POST', '/guilds/{guild_id}/templates', guild_id=int(guild)),
            json={'name': name, 'description': description}
        )

    async def sync_guild_template(
        self,
        guild: SupportsInt,
        template: str
    ) -> GuildTemplateData:
        """Sync the template with the guild's current state.

        This method requires the `MANAGE_GUILD` permission in the guild.

        Parameters:
            guild: The ID of the guild to sync the template with.
            template: The code of the template to sync.

        Returns:
            The updated guild template.
        """
        return await self.request(Route(
            'PUT', '/guilds/{guild_id}/templates/{template_code}',
            guild_id=int(guild), template_code=str(template)
        ))

    async def edit_guild_template(
        self,
        guild: SupportsInt,
        template: str,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> GuildTemplateData:
        """Edit the guild template's metadata.

        This method requires the `MANAGE_GUILD` permission in the guild.

        Parameters:
            guild: The ID of the guild the template is from.
            template: The code of the template to edit.
            name: The new 1-100 character name of the template.
            description: The new 0-120 character description of the template.

        Returns:
            The updated guild template.
        """
        if name is MISSING and description is MISSING:
            raise TypeError("at least one of 'name' or 'description' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'description': description
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/templates/{template_code}',
                guild_id=int(guild), template_code=str(template)
            ), json=payload
        )

    async def delete_guild_template(
        self,
        guild: SupportsInt,
        template: str
    ) -> GuildTemplateData:
        """Delete the guild template by its code.

        This method requires the `MANAGE_GUILD` permission in the guild.

        Parameters:
            guild: The ID of the guild the template is from.
            template: The code of the template to delete.

        Returns:
            The deleted guild template.
        """
        return await self.request(Route(
            'DELETE', '/guilds/{guild_id}/templates/{template_code}',
            guild_id=int(guild), template_code=str(template)
        ))
