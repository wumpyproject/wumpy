from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import ApplicationState


__all__ = ('Cache',)


class Cache:
    """Keeping track of the cache and memory state of the library.

    This class is also responsible for the creation of all models, so it is
    this class one should subclass to correctly inject their own models into
    the wrapper.
    """

    _state: ApplicationState

    __slots__ = ('_state',)

    def __init__(self, state: ApplicationState) -> None:
        self._state = state
