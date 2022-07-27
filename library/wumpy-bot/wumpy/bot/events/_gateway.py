import dataclasses
from typing import Any, ClassVar, FrozenSet, Mapping, Optional, Tuple

from discord_typings import ReadyData
from typing_extensions import Self
from wumpy.models import (
    Snowflake, User, ApplicationFlags
)


from .._dispatch import Event
from .._utils import backport_slots


__all__ = (
    'HelloEvent',
    'ResumedEvent',
    'ReadyEvent',
)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class HelloEvent(Event):

    NAME: ClassVar[str] = 'HELLO'

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], cached: None = None) -> Self:
        return cls()


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ResumedEvent(Event):

    NAME: ClassVar[str] = 'RESUMED'

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], cached: None = None) -> Optional[Self]:
        return cls()


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ReadyEvent(Event):
    user: User
    guilds: FrozenSet[Snowflake]
    shard: Optional[Tuple[int, int]]

    flags: ApplicationFlags

    NAME: ClassVar[str] = 'READY'

    @classmethod
    def from_payload(cls, payload: ReadyData, cached: None = None) -> Self:
        return cls(
            user=User.from_data(payload['user']),
            guilds=frozenset([Snowflake(int(guild['id'])) for guild in payload['guilds']]),
            shard=tuple(payload['shard']) if 'shard' in payload else None,
            flags=ApplicationFlags(int(payload['application']['flags']))
        )
