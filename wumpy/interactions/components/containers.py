from typing import (
    TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Optional, Union
)

from .component import Component

if TYPE_CHECKING:
    from ..base import ComponentInteraction


__all__ = ('ComponentList', 'ActionRow')


class ComponentList(Component):
    """A ComponentList is a overarching container for components."""

    children: List[Component]

    def __init__(
        self,
        *children: Component,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None
    ) -> None:
        super().__init__(callback)

        self.children = list(children)

    def to_dict(self) -> List[Union[List[Any], Dict[str, Any]]]:
        """Create a list of JSON serializable data to send to Discord."""
        return [item.to_dict() for item in self.children]


class ActionRow(ComponentList):
    """Non-interactive container component for other components."""

    def to_dict(self) -> Dict[str, Any]:
        """Turn the action row into data to send to Discord."""
        return {
            'type': 1,
            'components': [item.to_dict() for item in self.children]
        }
