from typing import (
    TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Optional, Union
)

from .component import Component

if TYPE_CHECKING:
    from ..base import ComponentInteraction


__all__ = ('ComponentList',)


class ComponentList(Component):
    """A ComponentList is a mix between a list and a dict.

    It needs to behave similarly to a list, but still get O(1) lookup by
    custom_id as Discord's component interactions only contain custom ids.
    """

    children: List[Component]

    def __init__(
        self,
        *children: Component,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None
    ) -> None:
        super().__init__(callback)

        self.children = list(children)

    def to_dict(self) -> List[Union[List[Any], Dict[str, Any]]]:
        return [item.to_dict() for item in self.children]
