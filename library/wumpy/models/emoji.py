from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils import _get_as_snowflake
from .base import Snowflake

__all__ = ('Reaction', 'Emoji')


class Reaction(str):
    """Representation of a Discord reaction.

    A Discord reaction is an emoji with only a handful of fields - sent during
    reaction events.

    This is a subclass of a string for convenience, which means that an
    instance of this class can be passed anywhere a string can be and that any
    methods on strings work on an instance of this class.

    Attributes:
        id:
            Optionally a snowflake of the emoji's ID. Built-in unicode emojis
            do not have an ID.
        name:
            The name of the emoji. **Defaults to `_`** when no name is passed.
            Discord currently allows any name to be used for any emoji, so
            Wumpy creates a string such as this one: `<:_:41771983429993937>`.
        animated: Whether the emoji is animated.
    """
    id: Optional[Snowflake]
    name: str
    animated: bool

    __slots__ = ('id', 'name', 'animated')

    def __new__(cls, data: Dict[str, Any]) -> 'Reaction':
        id_ = _get_as_snowflake(data, 'id')
        name = data.get('name', '_')
        animated = data.get('animated', False)

        # If id_ is None then it is default Emoji and only consists of the
        # emoji name (which is a unicode eomji).
        return super().__new__(cls, name) if id_ is None else super().__new__(
                cls,
                '<' + ('a' if animated else '') + ':' +
                name + ':' + str(id_) + '>'
            )

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id = _get_as_snowflake(data, 'id')
        self.name = data.get('name', '_')
        self.animated = data.get('animated', False)

    @property
    def created_at(self) -> Optional[datetime]:
        """When the emoji was created extracted from the ID.

        This is None when the emoji does not have an ID; when it is a built-in
        unicode emoji.
        """
        if self.id is None:
            return None

        return self.id.created_at


class Emoji(Reaction):
    """Full Discord emoji representation.

    Because this is a subclass of `Reaction` that means that this is also a
    subclass of string.

    Attributes:
        roles: A list of snowflakes representing roles that can use this emoji.
        user: The user who created this emoji.
        require_colons: Whether this emoji requires colons to be used.
        managed: Whether this emoji is managed by an integration.
        animated: Whether this emoji is animated.
        available:
            Whether this emoji is available; can be False when a guild looses
            Server Boosts and the new custom emoji limit is less than the
            amount of custom emojis the guild has.
    """

    roles: List[Snowflake]
    user: Optional[Dict]

    require_colons: bool
    managed: bool
    animated: bool
    available: bool

    __slots__ = (
        'roles', 'user', 'require_colons',
        'managed', 'animated', 'available',
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self.roles = [Snowflake(role) for role in data.get('roles', [])]
        self.user = data.get('user')

        self.require_colons = data.get('require_colons', True)
        self.managed = data.get('managed', False)
        self.animated = data.get('animated', False)
        self.available = data.get('available', True)
