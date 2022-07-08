from typing import Any, Dict, List, SupportsInt

from discord_typings import StickerData, StickerPackData

from .._requester import FileContent, Requester
from .._route import Route
from .._utils import MISSING

__all__ = (
    'StickerEndpoints',
)


class StickerEndpoints(Requester):
    """Endpoints for managing stickers."""

    __slots__ = ()

    async def fetch_sticker(self, sticker: SupportsInt) -> StickerData:
        """Fetch a sticker by its ID.

        Parameters:
            sticker: The ID of the sticker to fetch.

        Returns:
            The sticker object from Discord.
        """
        return await self.request(Route('GET', '/stickers/{sticker_id}', sticker_id=int(sticker)))

    async def fetch_nitro_sticker_packs(self) -> List[StickerPackData]:
        """Fetch all sticker packs currently available to Nitro subscribers.

        Returns:
            """
        return (await self.request(Route('GET', '/sticker-packs')))['sticker_packs']

    async def fetch_guild_stickers(self, guild: SupportsInt) -> List[StickerPackData]:
        """Fetch all stickers for a guild by its ID.

        The `user` field will be present if the bot has the
        `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild to fetch stickers for.

        Returns:
            A list of sticker objects for the guild.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}/stickers', guild_id=int(guild)))

    async def fetch_guild_sticker(self, guild: SupportsInt, sticker: SupportsInt) -> StickerData:
        """Fetch a specific sticker from a guild given its ID.

        The `user` field will be present if the bot has the
        `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild to fetch the sticker from.
            sticker: The ID of the sticker to fetch.

        Returns:
            The sticker object from Discord.
        """
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/stickers/{sticker_id}',
            guild_id=int(guild), sticker_id=int(sticker)
        ))

    async def create_sticker(
        self,
        guild: SupportsInt,
        *,
        name: str,
        description: str = '',
        tags: str,
        file: FileContent,
        reason: str = MISSING
    ) -> StickerData:
        """Create a new sticker for a guild.

        This endpoint requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild to create the sticker in.
            name: The 2-30 character name of the sticker.
            description:
                The (empty or 2-100 character) description of the sticker.
            tags: Autocomplete tags for the sticker (max 200 characters).
            file: The file to upload as the sticker.
            reason: The audit log reason for creating this sticker.

        Returns:
            The newly created sticker.
        """
        data = {
            'name': name,
            'description': description,
            'tags': tags
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/stickers', guild_id=int(guild)),
            data=data, files=[('file', file)], reason=reason
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
    ) -> StickerData:
        """Edit a guild sticker by its ID.

        This endpoint requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild the sticker is from.
            sticker: The ID of the sticker to edit.
            name: The new 2-30 character name of the sticker.
            description:
                The new (empty or 2-100 character) description of the sticker.
            tags: New autocomplete tags for the sticker (max 200 characters).
            reason: The audit log reason for editing this sticker.

        Returns:
            The updated sticker object.
        """
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
        """Delete a guild sticker by its ID.

        This endpoint requires the `MANAGE_EMOJIS_AND_STICKERS` permission.

        Parameters:
            guild: The ID of the guild the sticker is from.
            sticker: The ID of the sticker to delete.
            reason: The audit log reason for deleting this sticker.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            reason=reason
        )
