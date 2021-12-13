from typing import Any, Dict, Optional

from ..utils import _get_as_snowflake
from .base import Object, Snowflake
from .permissions import Permissions

__all__ = ('RoleTags', 'Role')


class RoleTags:
    """Tabs on a particular Discord role.

    This contains extra metadata about a role, such as what makes the role
    managed or whether it is the role members get when boosting.
    """

    bot_id: Optional[Snowflake]
    integration_id: Optional[Snowflake]

    premium_subscriber: bool

    __slots__ = ('bot_id', 'integration_id', 'premium_subscriber')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.bot_id = _get_as_snowflake(data, 'bot_id')
        self.integration_id = _get_as_snowflake(data, 'integration_id')

        # If this is present (null in JSON converted to None) that means the
        # role is the premium subscriber role.
        self.premium_subscriber = data.get('premium_subscriber', False) is None


class Role(Object):
    """Representation of a Discord role with permissions.¨

    A role represents a set of permissions attached to a group of members.
    `@everyone` is also a role like any other role expect for the fact that its
    ID is the same as the guild it is attached to.

    Attributes:
        name: The name of the role.
        color: The color of the role as an integer.
        position: The position of the role in the role list.
        permissions: The permissions that having this role gives.
        hoist: Whether this role is pinned in the user list.
        managed: Whether this role is managed by an integration or bot.
        mentionable: Whether this role can be mentioned by anyone.
        tags:
            Extra metadata about the role - this attribute contains data about
            what is managing this role and whether it is the role that premium
            subscribers (also called "boosters") are given.
    """

    name: str
    color: int
    position: int
    permissions: Permissions

    hoist: bool
    managed: bool
    mentionable: bool
    tags: RoleTags

    __slots__ = (
        'name', 'color', 'hoist', 'position', 'permissions',
        'managed', 'mentionable', 'tags'
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.name = data['name']
        self.color = data['color']
        self.position = data['position']
        self.permissions = Permissions(data['permissions'])

        self.hoist = data['hoist']
        self.managed = data['managed']
        self.mentionable = data['mentionable']
        self.tags = RoleTags(data.get('tags', {}))

    @property
    def premium_subscriber(self) -> bool:
        """Whether this role is the role that premium subscribers get.

        Shortcut for accessing the `premium_subscriber` attribute of the
        RoleTags object.
        """
        return self.tags.premium_subscriber
