import re
from typing import Any, Callable, Coroutine, List, Tuple, Union

import anyio

from .._models import ComponentInteraction

__all__ = (
    'ComponentHandler',
)


ComponentCallback = Callable[
    [ComponentInteraction, 're.Match[str]'],
    Coroutine[Any, Any, object]
]


class ComponentHandler:
    """Handler for components, dispatching waiting components.

    This is a mixin class keeping track of handlers for components setup.
    """

    _regex_components: List[Tuple['re.Pattern[str]', ComponentCallback]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._regex_components = []

    async def invoke_component(self, interaction: ComponentInteraction) -> None:
        for pattern, callback in self._regex_components:
            match = pattern.match(interaction.custom_id)
            if match:
                await callback(interaction, match)
                return

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

    def component(
            self,
            pattern: Union[str, 're.Pattern[str]']
    ) -> Callable[[ComponentCallback], ComponentCallback]:
        """Add a callback to be dispatched when the custom ID is matched.

        Examples:

            ```python
            @app.component(r'upvote-(?P<message_id>)')
            async def process_upvote(interaction: ComponentInteraction, match: re.Match):
                message_id = match.group('message_id')
                await interaction.reply(
                    f'You upvoted message {message_id}',
                    ephemeral=True
                )
            ```

        Parameters:
            pattern: The regex pattern to match custom IDs with.

        Returns:
            A decorator that adds the callback to the list of components.
        """
        def decorator(func: ComponentCallback) -> ComponentCallback:
            nonlocal pattern

            if isinstance(pattern, str):
                pattern = re.compile(pattern)

            self.add_component(pattern, func)
            return func
        return decorator
