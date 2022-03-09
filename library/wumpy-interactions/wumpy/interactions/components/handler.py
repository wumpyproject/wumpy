from typing import TYPE_CHECKING, Dict

import anyio.abc

from .component import Component

if TYPE_CHECKING:
    from wumpy.models import ComponentInteraction


__all__ = ('ComponentHandler',)


class ComponentHandler:
    """Handler for components, dispatching waiting components.

    Attributes:
        components:
            A dictionary of interaction IDs or message IDs to the component.
    """

    # This is a dictionary with the key either being the interaction ID for
    # the original response, or a message ID for followup messages
    components: Dict[int, Component]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.components = {}

    def handle_component(
        self,
        interaction: 'ComponentInteraction',
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Handle the component, setting waiting events and calling callbacks.

        The lookup order here is first for message ID, then by interaction ID.
        This because it is not know the ID of the message that the original
        response created.

        Parameters:
            interaction: The interaction a component should handle.
            tg: Task group to launch callbacks with.
        """
        component = self.components.get(int(interaction.message['id']))
        if not component:
            interact = interaction.message.get('interaction')
            if interact:
                component = self.components.get(int(interact['id']))

        if component is None:
            # We know no components for this interaction
            return

        component.handle_interaction(interaction, tg=tg)

    def add_component(self, snowflake: int, component: Component) -> None:
        """Add a component to be dispatched when an interaction is received.

        If there is an existing component for the snowflake, it will be
        replaced with the passed component.

        Parameters:
            snowflake: An interaction ID or message ID fitting.
            component: Component to add that will be called to handle.
        """
        self.components[snowflake] = component
