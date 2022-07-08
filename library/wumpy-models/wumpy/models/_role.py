import dataclasses
from typing import Optional

from discord_typings import RoleData, RoleTagsData
from typing_extensions import Self

from ._base import Model, Snowflake
from ._permissions import Permissions
from ._utils import backport_slots

__all__ = (
    'RoleTags',
    'Role',
)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class RoleTags:
    """Tags on a particular Discord role.

    This contains extra metadata about a role, such as what makes the role
    managed or whether it is the role members get when boosting.
    """

    bot_id: Optional[Snowflake]
    integration_id: Optional[Snowflake]

    premium_subscriber: bool

    @classmethod
    def from_data(cls, data: RoleTagsData) -> Self:
        bot_id = data.get('bot_id')
        if bot_id is not None:
            bot_id = Snowflake(int(bot_id))

        integration_id = data.get('integration_id')
        if integration_id is not None:
            integration_id = Snowflake(int(integration_id))

        return cls(
            bot_id=bot_id,
            integration_id=integration_id,
            premium_subscriber=data.get('premium_subscriber', False) is None
        )


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class Role(Model):
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

    @property
    def premium_subscriber(self) -> bool:
        """Whether this role is the role that premium subscribers get.

        Shortcut for accessing the `premium_subscriber` attribute of the
        RoleTags object.
        """
        return self.tags.premium_subscriber

    @classmethod
    def from_data(cls, data: RoleData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            color=data['color'],
            position=data['position'],
            permissions=Permissions(int(data['permissions'])),
            hoist=data['hoist'],
            managed=data['managed'],
            mentionable=data['mentionable'],
            tags=RoleTags.from_data(data.get('tags', {}))
        )
