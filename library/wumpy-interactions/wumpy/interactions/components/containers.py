from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from .component import Component, Coro

if TYPE_CHECKING:
    from wumpy.models import ComponentInteraction


__all__ = ('ActionRow', 'ComponentList')


class ActionRow(Component):
    """Non-interactive container component for other components."""

    children: List[Component]

    def __init__(
        self,
        *children: Component,
        callback: Optional[Callable[['ComponentInteraction'], Coro[object]]] = None
    ) -> None:
        super().__init__(callback)

        self.children = list(children)

    def to_dict(self) -> Dict[str, Any]:
        """Turn the action row into data to send to Discord."""
        return {
            'type': 1,
            'components': [item.to_dict() for item in self.children]
        }


class ComponentList(Component):
    """A ComponentList is a overarching container for components."""

    children: List[ActionRow]

    def __init__(
        self,
        *children: Union[List[ActionRow], ActionRow],
        callback: Optional[Callable[['ComponentInteraction'], Coro[object]]] = None
    ) -> None:
        super().__init__(callback)

        self.children = [
            ActionRow(*row) if isinstance(row, list) else row for row in children
        ]

    def to_dict(self) -> List[Union[List[Any], Dict[str, Any]]]:
        """Create a list of JSON serializable data to send to Discord."""
        return [item.to_dict() for item in self.children]
