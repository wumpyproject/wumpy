from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, List, Set, Tuple, Optional, TypeVar

import anyio

if TYPE_CHECKING:
    from ..base import MessageComponentInteraction


RT = TypeVar('RT')


class Result(Generic[RT]):
    """Synchronizing Event but modified to pass a result."""

    __slots__ = ('event', 'value')

    def __init__(self) -> None:
        self.event = anyio.Event()

    def is_set(self) -> bool:
        return self.event.is_set()

    def set(self, value: RT) -> None:
        self.event.set()
        self.value = value

    async def wait(self) -> RT:
        await self.event.wait()
        return self.value  # value should now be set


class ComponentList(list):
    """A ComponentList is a mix between a list and a dict.

    It needs to behave similarly to a list, but still get O(1) lookup by
    custom_id as Discord's component interactions only contain custom ids.
    """

    waiters: List[Tuple[
        Callable[['MessageComponentInteraction'], bool], Result['MessageComponentInteraction']
    ]]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.waiters = []

    async def __call__(
        self,
        check: Callable[['MessageComponentInteraction'], bool] = lambda i: True,
        *,
        timeout: Optional[float] = None
    ) -> 'MessageComponentInteraction':
        event: Result['MessageComponentInteraction'] = Result()
        self.waiters.append((check, event))

        with anyio.fail_after(timeout):
            return await event.wait()

    async def handle_component(self, interaction: 'MessageComponentInteraction', *, tg) -> Any:
        # We actually don't know which action row the component belonged
        # to, so we'll have to just let each ActionRow handle the interaction
        # and check if they got the component.
        for item in self:
            handled = await item.handle_component(interaction)
            if handled is not None:
                break

        for index, (check, result) in enumerate(self.waiters):
            if check(interaction):
                result.set(interaction)
                self.waiters.pop(index)

    def to_json(self) -> List[Dict[str, Any]]:
        return [item.to_json() for item in self]
