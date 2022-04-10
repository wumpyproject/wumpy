from typing import Any, Dict, Optional, Tuple
from weakref import WeakValueDictionary

from discord_typings import GuildMemberData, UserData
from wumpy.models import Member, User

from .base import BaseMemoryCache

__all__ = ['UserMemoryCache', 'MemberMemoryCache']


class UserMemoryCache(BaseMemoryCache):
    _users: 'WeakValueDictionary[int, User]'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._users = WeakValueDictionary()

    def _store_user(self, data: UserData) -> User:
        # This is slower than simply constructing another User model, but for
        # memory purposes we want to share it between objects like Members as
        # much as possible.
        user = self._users.get(int(data['id']))
        if (
                user and user.id == data['id']
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._members = {}

    async def _process_guild_member_add(self, data: GuildMemberData) -> Tuple[None, Member]:
        if 'guild_id' not in data:
            raise ValueError("Member data must contain extra 'guild_id' field")

        guild_id = data['guild_id']
        user = self._store_user(data['user'])

        member = Member.from_user(user, data)
        self._members[(guild_id, member.id)] = member
        return (None, member)

    async def _process_guild_member_update(
        self,
        data: GuildMemberData
    ) -> Tuple[Optional[Member], Member]:
        return (
            (await self._process_guild_member_remove(data))[0],
            (await self._process_guild_member_add(data))[1]
        )

    async def _process_guild_member_remove(
            self,
            data: Dict[str, Any]
    ) -> Tuple[Optional[Member], None]:
        return (self._members.pop((data['guild_id'], data['user']['id']), None), None)
