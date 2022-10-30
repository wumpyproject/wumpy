import attrs

from .._raw import RawRole
from .._utils import MISSING, get_api

__all__ = (
    'Role',
)


@attrs.define(eq=False)
class Role(RawRole):
    ...

    async def delete(self, *, reason: str = MISSING) -> None:
        """Delete the role.
        
        This method requires the `MANAGE_ROLES` permission.

        Parameters:
            reason: Audit log reason for deleting the role.
        """
        if not self.guild_id:
            raise ValueError('Cannot delete role without known guild ID')

        await get_api().delete_role(self.guild_id, self.id, reason=reason)
