from typing import Any, Dict, List, Optional, SupportsInt, Tuple

from wumpy.models import Emoji, Role, Sticker

from .base import BaseMemoryCache

__all__ = ['RoleMemoryCache', 'EmojiMemoryCache']


class RoleMemoryCache(BaseMemoryCache):
    _roles: Dict[int, Role]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._roles = {}

    async def _process_guild_role_create(self, data: Dict[str, Any]) -> Tuple[None, Role]:
        role = Role.from_data(data['role'])
        self._roles[int(data['role']['id'])] = role
        return (None, role)

    async def _process_guild_role_update(self, data: Dict[str, Any]) -> Tuple[Optional[Role], Role]:
        return (
            (await self._process_guild_role_delete(data))[0],
            (await self._process_guild_role_create(data))[1]
        )

    async def _process_guild_role_delete(self, data: Dict[str, Any]) -> Tuple[Optional[Role], None]:
        return (self._roles.pop(int(data['role_id']), None), None)

    async def get_role(self, role: SupportsInt) -> Optional[Role]:
        return self._roles.get(int(role))


class EmojiMemoryCache(BaseMemoryCache):
    _emojis: Dict[int, Emoji]
    _guild_emojis: Dict[int, Tuple[int, ...]]

    _stickers: Dict[int, Sticker]
    _guild_stickers: Dict[int, Tuple[int, ...]]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._emojis = {}
        self._guild_emojis = {}

        self._stickers = {}
        self._guild_stickers = {}

    async def _process_guild_emojis_update(
            self,
            data: Dict[str, Any]
    ) -> Tuple[Optional[List[Emoji]], List[Emoji]]:
        # The reason that the first item is both Optional and a list (which we
        # might as well make empty) is to follow the same patterns as other
        # processors. If nothing was found in cache, the first item should be
        # None so that the code which wraps update() can handle it.

        prev = self._guild_emojis.get(int(data['guild_id']))
        if prev is not None:
            prev = [self._emojis[i] for i in prev]

            removed = {e.id for e in prev} - {int(e['id']) for e in data['emojis']}
            for id_ in removed:
                self._emojis.pop(id_, None)

        updated = [Emoji.from_data(e) for e in data['emojis']]
        for emoji in updated:
            self._emojis[emoji.id] = emoji

        self._guild_emojis[int(data['guild_id'])] = tuple(e.id for e in updated)
        return (prev, updated)

    async def _process_guild_stickers_update(
            self,
            data: Dict[str, Any]
    ) -> Tuple[Optional[List[Sticker]], List[Sticker]]:
        # See _process_guild_emojis_update() for why the first item is optional

        prev = self._guild_stickers.get(int(data['guild_id']))
        if prev is not None:
            prev = [self._stickers[i] for i in prev]

            removed = (
                {stick.id for stick in prev} - {int(stick['id']) for stick in data['stickers']}
            )
            for id_ in removed:
                self._stickers.pop(id_, None)

        updated = [Sticker.from_data(e) for e in data['emojis']]
        for sticker in updated:
            self._stickers[sticker.id] = sticker

        self._guild_stickers[int(data['guild_id'])] = tuple(stick.id for stick in updated)
        return (prev, updated)

    async def get_emoji(self, emoji: SupportsInt) -> Optional[Emoji]:
        return self._emojis.get(int(emoji))

    async def get_sticker(self, sticker: SupportsInt) -> Optional[Sticker]:
        return self._stickers.get(int(sticker))
