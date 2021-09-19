from typing import Any, Dict

from .componentlist import ComponentList


class ActionRow(ComponentList):
    """Non-interactive container component for other components.

    This is different from a ComponentList in that it is an actual component
    sent to the Discord API.
    """

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 1,
            'components': [item.to_dict() for item in self.children]
        }
