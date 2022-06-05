from typing import Any, Dict, Optional, SupportsInt, Tuple
from weakref import WeakValueDictionary

from discord_typings import (
    GuildMemberAddData, GuildMemberRemoveData, GuildMemberUpdateData, UserData
)
from wumpy.models import Member, User

from .base import BaseMemoryCache

__all__ = ['UserMemoryCache', 'MemberMemoryCache']


class UserMemoryCache(BaseMemoryCache):
    _users: 'WeakValueDictionary[int, User]'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._users = WeakValueDictionary()

    def _store_user(self, data: UserData) -> User:
        # This is slower than simply constructing another User model, but for
        # memory purposes we want to share it between objects like Members as
        # much as possible.
        user = self._users.get(int(data['id']))
        if (
                user and user.id == int(data['id'])
                and user.name == data['username']
                and user.discriminator == data['discriminator']
                and user.public_flags == data.get('public_flags')
        ):
            return user  # The existing user is up-to-date

        user = User.from_data(data)
        self._users[int(data['id'])] = user

        return user


class MemberMemoryCache(BaseMemoryCache):
    _members: Dict[Tuple[int, int], Member]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._members = {}

    def _process_guild_member_add(
            self,
            data: GuildMemberAddData,
            *,
            return_old: bool = True
    ) -> None:
        guild_id = int(data['guild_id'])
        user = self._store_user(data['user'])

        member = Member.from_user(user, data)
        self._members[(guild_id, member.id)] = member

    def _process_guild_member_update(
        self,
        data: GuildMemberUpdateData,
        *,
        return_old: bool = True
    ) -> Optional[Member]:
        old = self._process_guild_member_remove(data, return_old=return_old)
        self._process_guild_member_add(data, return_old=return_old)
        return old

    def _process_guild_member_remove(
            self,
            data: GuildMemberRemoveData,
            *,
            return_old: bool = True
    ) -> Optional[Member]:
        return self._members.pop((int(data['guild_id']), int(data['user']['id'])), None)

    async def get_member(self, guild: SupportsInt, user: SupportsInt) -> Optional[Member]:
        return self._members.get((int(guild), int(user)))
