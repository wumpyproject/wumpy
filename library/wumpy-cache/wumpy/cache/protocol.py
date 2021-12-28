from typing import Any, Optional, Protocol, SupportsInt

import anyio.lowlevel

__all__ = ('Cache',)


class Cache(Protocol):
    """Protocol for a cache implementation for Wumpy.

    Another benefit this class gives is that it can be overriden to get
    all necessary methods defined with no implementation provided. By default
    all methods will simply yield to the event loop and return None.
    """

    async def update(self, payload: dict) -> Optional[Any]:
        """Update the cache with new information from an event.

        This method should return the older data that was in the cache, so that
        it can be dispatched to the user's event listeners. Because of the huge
        amounts of types of events that Discord sends it is not worth it to
        document the specific return types per event, but here are the rules:

        - Events that CREATE new data is not required to return any data.
          If, for whatever reason, there is appropriate data it is urged to be
          returned but will be discarded because of implementation details.

        - Events that UPDATE existing data should return the older data if
          present in the cache. That way it can be used by the user.

        - Events that DELETE objects should return the existing data if it can
          be found in the cache.

        - All other events, such as RESUMED or TYPING_START should return None
          as it is simply discarded.

        Parameters:
            payload:
                The dictionary representation of the payload received by
                Discord over the gateway.

        Returns:
            The older cached data - that is now being updated by this event.
            If there is no older data then None should be returned.
        """
        ...

