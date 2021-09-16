from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..base import MessageComponentInteraction


class ActionRow(list):
    """Non-interactive container component for other components.

    This is different from a ComponentList in that it is an actual component
    sent to the Discord API and cannot be subtituted for a ComponentList.
    """

    def handle_component(self, interaction: 'MessageComponentInteraction', *, tg) -> Any:
        for component in self:
            if component.custom_id == interaction.custom_id:
                component.handle_component(interaction, tg=tg)
                return component

    def to_json(self) -> Dict[str, Any]:
        return {
            'type': 1,
            'components': [item.to_json() for item in self]
        }
