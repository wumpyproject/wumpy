from typing import Any

__all__ = ('ComponentHandler',)


class ComponentHandler:
    """Handler for components, dispatching waiting components.

    This is a mixin class keeping track of handlers for components setup.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
