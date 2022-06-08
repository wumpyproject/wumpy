from typing import Any, Dict, FrozenSet, Optional, SupportsInt, Tuple

from discord_typings import (
    GuildCreateData, GuildDeleteData, GuildEmojisUpdateData,
    GuildRoleCreateData, GuildRoleDeleteData, GuildRoleUpdateData,
    GuildStickersUpdateData, GuildUpdateData
)
from wumpy.models import Emoji, Guild, Role, Sticker

from .base import BaseMemoryCache

__all__ = ['GuildMemoryCache', 'RoleMemoryCache', 'EmojiMemoryCache']


class GuildMemoryCache(BaseMemoryCache):
    _guilds: Dict[int, Guild]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._guilds = {}

    def _process_guild_create(
            self,
            data: GuildCreateData,
            *,
            return_old: bool = True
    ) -> None:
        self._guilds[int(data['id'])] = Guild.from_data(data)

    def _process_guild_update(
            self,
            data: GuildUpdateData,
            *,
            return_old: bool = True
    ) -> Optional[Guild]:
        old = self._process_guild_delete(data, return_old=return_old)
        self._process_guild_create(data, return_old=return_old)
        return old

    def _process_guild_delete(
            self,
            data: GuildDeleteData,
            *,
            return_old: bool = True
    ) -> Optional[Guild]:
        # Don't remove the guild, as it only became unavailable - we didn't
        # get kicked or left it.
        if not data.get('unavailable', False):
            return self._guilds.pop(int(data['id']))

        if return_old:
            return self._guilds.get(int(data['id']))
        return None

    async def get_guild(self, guild: SupportsInt) -> Optional[Guild]:
        return self._guilds.get(int(guild))


class RoleMemoryCache(BaseMemoryCache):
    _roles: Dict[int, Role]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._roles = {}

    def _process_guild_role_create(
            self,
            data: GuildRoleCreateData,
            *,
            return_old: bool = True
    ) -> None:
        role = Role.from_data(data['role'])
        self._roles[int(data['role']['id'])] = role

    def _process_guild_role_update(
            self,
            data: GuildRoleUpdateData,
            *,
            return_old: bool = True
    ) -> Optional[Role]:
        old = self._roles.pop(int(data['role']['id']), None)
        self._process_guild_role_create(data, return_old=return_old)
        return old

    def _process_guild_role_delete(
            self,
            data: GuildRoleDeleteData,
            *,
            return_old: bool = True
    ) -> Optional[Role]:
        return self._roles.pop(int(data['role_id']), None)

    async def get_role(self, role: SupportsInt) -> Optional[Role]:
        return self._roles.get(int(role))


class EmojiMemoryCache(BaseMemoryCache):
    _emojis: Dict[int, Emoji]
    _guild_emojis: Dict[int, Tuple[int, ...]]

    _stickers: Dict[int, Sticker]
    _guild_stickers: Dict[int, Tuple[int, ...]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._emojis = {}
        self._guild_emojis = {}

        self._stickers = {}
        self._guild_stickers = {}

    def _process_guild_emojis_update(
            self,
            data: GuildEmojisUpdateData,
            *,
            return_old: bool = True
    ) -> Optional[FrozenSet[Emoji]]:
        if return_old:
            prev = frozenset([
                emoji for emoji in [
                    self._emojis.pop(i, None) for i in
                    self._guild_emojis.get(int(data['guild_id']), ())
                ] if emoji is not None
            ])
        else:
            prev = None

        updated = [Emoji.from_data(e) for e in data['emojis']]
        for emoji in updated:
            self._emojis[emoji.id] = emoji

        self._guild_emojis[int(data['guild_id'])] = tuple(e.id for e in updated)

        return prev

    def _process_guild_stickers_update(
            self,
            data: GuildStickersUpdateData,
            *,
            return_old: bool = True
    ) -> Optional[FrozenSet[Sticker]]:
        if return_old:
            prev = frozenset([
                sticker for sticker in [
                    self._stickers.pop(i, None) for i in
                    self._guild_stickers.get(int(data['guild_id']), ())
                ] if sticker is not None
            ])
        else:
            prev = None

        updated = [Sticker.from_data(e) for e in data['stickers']]
        for sticker in updated:
            self._stickers[sticker.id] = sticker

        self._guild_stickers[int(data['guild_id'])] = tuple(s.id for s in updated)

        return prev

    async def get_emoji(self, emoji: SupportsInt) -> Optional[Emoji]:
        return self._emojis.get(int(emoji))

    async def get_sticker(self, sticker: SupportsInt) -> Optional[Sticker]:
        return self._stickers.get(int(sticker))
