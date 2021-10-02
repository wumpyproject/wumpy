from typing import Any, Dict

import anyio.abc

from ..base import ComponentInteraction

__all__ = ('ComponentHandler',)


class ComponentHandler:
    """Dispatching components waiting for a result."""

    # This is a dictionary with the key either being the interaction ID for
    # the original response, or a message ID for followup messages
    components: Dict[int, Any]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.components = {}

    def handle_component(
        self,
        interaction: ComponentInteraction,
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Handle the component, setting waiting events and calling callbacks.

        The lookup order here for events is first by the message ID for the
        followup replies, if that fails a lookup by interaction ID is done for
        the original response.
        """
        component = self.components.get(int(interaction.message['id']))
        if not component:
            interact = interaction.message.get('interaction')
            if interact:
                component = self.components.get(int(interact['id']))

        if component is None:
            # We know no components for this interaction
            return

        component.handle_component(interaction, tg=tg)

    def add_component(self, snowflake: int, component: Any) -> None:
        """Add a component to be dispatched when an interaction is received.

        If there is an existing component for the message, it will be replaced.
        The snowflake should either be an interaction ID or a message ID. When
        a message component is attempted to resolved both are looked up.
        """
        self.components[snowflake] = component
