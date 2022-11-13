import re
from typing import Any, Callable, Coroutine, List, Tuple, Optional

from .._models import ComponentInteraction

__all__ = (
    'ComponentHandler',
)


ComponentCallback = Callable[
    [ComponentInteraction, 're.Match[str]'],
    Coroutine[Any, Any, object]
]


class ComponentHandler:
    """Handler and container for components."""

    _regex_components: List[Tuple['re.Pattern[str]', ComponentCallback]]

    def __init__(self) -> None:
        self._regex_components = []

    async def invoke(self, interaction: ComponentInteraction) -> Optional[object]:
        for pattern, callback in self._regex_components:
            match = pattern.match(interaction.custom_id)
            if match:
                return await callback(interaction, match)

    def add_component(self, pattern: 're.Pattern[str]', func: ComponentCallback) -> None:
        """Add a callback to be dispatched when the pattern is matched.

        Parameters:
            pattern: The compiled regex pattern to match custom IDs with.
            func: The callback to be called when the pattern is matched.
        """
        self._regex_components.append((pattern, func))

    def remove_component(self, pattern: 're.Pattern[str]', func: ComponentCallback) -> None:
        """Remove a callback from the list of components.

        Parameters:
            pattern: The regex pattern used to add the callback.
            func: The callback to be removed.

        Raises:
            ValueError: The callback was not found.
        """
        try:
            self._regex_components.remove((pattern, func))
        except ValueError:
            raise ValueError(f'Callback {func} with pattern {pattern} not found.') from None
