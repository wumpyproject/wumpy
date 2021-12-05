from typing import Any, Dict, List, SupportsInt

from ..ratelimiter import Route
from ..utils import MISSING, File
from .base import Requester


class StickerRequester(Requester):
    async def fetch_sticker(self, sticker: SupportsInt) -> Dict[str, Any]:
        """Fetch a sticker by its ID."""
        return await self.request(Route('GET', '/stickers/{sticker_id}', sticker_id=int(sticker)))

    async def fetch_nitro_sticker_packs(self) -> Dict[str, Any]:
        """Fetch a list of all sticker packs currently available to Nitro subscribers."""
        return await self.request(Route('GET', '/sticker-packs'))

    async def fetch_guild_stickers(self, guild: SupportsInt) -> List[Any]:
        """Fetch all stickers for a guild by its ID."""
        return await self.request(Route('GET', '/guilds/{guild_id}/stickers', guild_id=int(guild)))

    async def fetch_guild_sticker(self, guild: SupportsInt, sticker: SupportsInt) -> Dict[str, Any]:
        """Fetch a sticker from a guild given its ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/stickers/{sticker_id}',
            guild_id=int(guild), sticker_id=int(sticker)
        ))

    async def create_sticker(
        self,
        guild: SupportsInt,
        *,
        name: str,
        description: str,
        tags: str,
        file: File,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new sticker for a guild."""
        data = {
            'name': name,
            'description': description,
            'tags': tags,
            'file': file
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/stickers', guild_id=int(guild)),
            data=data, reason=reason
        )

    async def edit_sticker(
        self,
        guild: SupportsInt,
        sticker: SupportsInt,
        *,
        name: str = MISSING,
        description: str = MISSING,
        tags: str = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild sticker by its ID."""
        if name is MISSING and description is MISSING and tags is MISSING:
            raise TypeError("at least one of 'name', 'description' or 'tags is required")

        payload: Dict[str, Any] = {
            'name': name,
            'description': description,
            'tags': tags,
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            json=payload, reason=reason
        )

    async def delete_sticker(
        self,
        guild: SupportsInt,
        sticker: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a guild sticker by its ID."""
        return await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            reason=reason
        )
