from typing import Iterable, Optional, Sequence, SupportsInt, Union

from discord_typings import AllowedMentionsData
from typing_extensions import Self

__all__ = ('AllowedMentions',)


class AllowedMentions:
    """Allowed mentions configuration for a message.

    As with all other Wumpy models this is immutable for security reasons. To
    "mutate" the allowed mentions you should create a new instance. Allowed
    mentions objects can be bitwise-OR:d together to create a new object with
    the settings of the right object taking precedence.

    For convenience you can use the `replace()` method which will create an
    object and OR it with the current object to create the final return.

    Parameters:
        everyone: Whether to allow @everyone pings.
        users:
            Whether to allow user-pings. Set to `True` to allow all users,
            `False` to disallow all users, or an iterable of user IDs to
            only allow specific users to be pinged.
        roles:
            Whether to allow role-pings. Set to `True` to allow all roles,
            `False` to disallow all roles, or an iterable of role IDs to
            only allow specific roles to be pinged.
        replied_user: Whether to ping the user in a reply.
    """

    __slots__ = ('_everyone', '_users', '_roles', '_replied_user')

    def __init__(
        self,
        *,
        everyone: Optional[bool] = None,
        users: Union[bool, Iterable[SupportsInt], None] = None,
        roles: Union[bool, Iterable[SupportsInt], None] = None,
        replied_user: Optional[bool] = None,
    ) -> None:
        self._everyone = everyone

        if users is True or users is False or users is None:
            self._users = users
        else:
            self._users = tuple(int(u) for u in users)

        if roles is True or roles is False or roles is None:
            self._roles = roles
        else:
            self._roles = tuple(int(r) for r in roles)

        self._replied_user = replied_user

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            data = other.data()
        elif isinstance(other, dict):
            data = other
        else:
            return NotImplemented

        return self.data() == data

    def __or__(self, other: object) -> Self:
        if not isinstance(other, self.__class__):
            return NotImplemented

        everyone = self._everyone if other._everyone is None else other._everyone
        users = self._users if other._users is None else other._users
        roles = self._roles if other._roles is None else other._roles
        reply = self._replied_user if other._replied_user is None else other._replied_user

        return self.__class__(
            everyone=everyone,
            users=users,
            roles=roles,
            replied_user=reply
        )

    @property
    def everyone(self) -> Optional[bool]:
        return self._everyone

    @property
    def users(self) -> Union[bool, Sequence[int], None]:
        return self._users

    @property
    def roles(self) -> Union[bool, Sequence[int], None]:
        return self._roles

    @property
    def replied_user(self) -> Optional[bool]:
        return self._replied_user

    def data(self) -> AllowedMentionsData:
        data: AllowedMentionsData = {
            'parse': []
        }

        if self._everyone:
            data['parse'].append('everyone')

        if self._users:
            if isinstance(self._users, tuple):
                data['users'] = self._users
            else:
                data['parse'].append('users')

        if self._roles:
            if isinstance(self._roles, tuple):
                data['roles'] = self._roles
            else:
                data['parse'].append('roles')

        if self._replied_user is not None:
            data['replied_user'] = self._replied_user

        return data

    def replace(
        self,
        *,
        everyone: Optional[bool] = None,
        users: Union[bool, Iterable[SupportsInt], None] = None,
        roles: Union[bool, Iterable[SupportsInt], None] = None,
        replied_user: Optional[bool] = None,
    ) -> Self:
        """Replace a particular value, returning a new copy.

        This is the same as creating a new object with those configurations and
        bitwise-ORing it with the current object.

        Parameters:
            everyone: Whether to allow @everyone pings.
            users:
                Whether to allow user-pings. Set to `True` to allow all users,
                `False` to disallow all users, or an iterable of user IDs to
                only allow specific users to be pinged.
            roles:
                Whether to allow role-pings. Set to `True` to allow all roles,
                `False` to disallow all roles, or an iterable of role IDs to
                only allow specific roles to be pinged.
            replied_user: Whether to ping the user in a reply.
        """
        other = self.__class__(
            everyone=everyone,
            users=users,
            roles=roles,
            replied_user=replied_user
        )
        return self | other

    @classmethod
    def none(cls) -> Self:
        return cls(everyone=False, users=False, roles=False, replied_user=False)

    @classmethod
    def all(cls) -> Self:
        return cls(everyone=True, users=True, roles=True, replied_user=True)
