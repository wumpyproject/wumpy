from typing import Any, Dict, Optional, Tuple

from .base import Object

__all__ = ('PartialGuild',)


class PartialGuild(Object):
    """Guild with only some of the fields filled.

    An instance of this class can be found with invites as an example.
    """

    name: str
    description: str
    features: Tuple[str, ...]
    verification_level: int
    vanity_url_code: Optional[str]

    __slots__ = (
        'name', 'description', 'features', 'verification_level',
        'vanity_url_code',
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.name = data['name']
        self.description = data['description']
        self.features = tuple(data['features'])
        self.verification_level = data['verification_level']
        self.vanity_url_code = data['verification_level']
