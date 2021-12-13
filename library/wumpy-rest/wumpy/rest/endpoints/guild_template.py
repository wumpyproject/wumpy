from typing import Any, Dict, List, Optional, SupportsInt

from ..route import Route
from ..utils import MISSING
from .base import Requester


class GuildTemplateRequester(Requester):

    __slots__ = ()

    async def fetch_guild_template(self, code: str) -> Dict[str, Any]:
        """Fetch a guild template by its code."""
        return await self.request(Route(
            'GET', '/guilds/templates/{template_code}', template_code=str(code)
        ))

    async def create_guild_from_template(
        self,
        template: str,
        *,
        name: str,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new guild based on a template."""
        return await self.request(
            Route('POST', '/guilds/templates/{template_code}', template_code=str(template)),
            json={'name': name, 'icon': icon}
        )

    async def fetch_guild_templates(self, guild: SupportsInt) -> List[Any]:
        """Fetch a list of all guild templates created from a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/templates', guild_id=int(guild)))

    async def create_guild_template(
        self,
        guild: SupportsInt,
        *,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a template from a guild."""
        return await self.request(
            Route('POST', '/guilds/{guild_id}/templates', guild_id=int(guild)),
            json={'name': name, 'description': description}
        )

    async def sync_guild_template(self, guild: SupportsInt, template: str) -> Dict[str, Any]:
        """Sync the template with the guild's current state."""
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
    ) -> Dict[str, Any]:
        """Edit the guild template's metadata."""
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

    async def delete_guild_template(self, guild: SupportsInt, template: str) -> Dict[str, Any]:
        """Delete the guild template by its code."""
        return await self.request(Route(
            'DELETE', '/guilds/{guild_id}/templates/{template_code}',
            guild_id=int(guild), template_code=str(template)
        ))
