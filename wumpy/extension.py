from typing import Any, Callable, Dict, Optional, Union

from .interactions import CommandRegistrar
from .utils import EventDispatcher

__all__ = ('Extension',)


class Extension(CommandRegistrar, EventDispatcher):
    """Lazily loaded extension of a GatewayClient of InteractionApp.

    The point of this class is to be able to split the commands and listeners
    into several files that can easily be unloaded without restarting the whole
    process.
    """

    def __init__(self) -> None:
        super().__init__()

        self._data = None

    @property
    def data(self) -> Dict[str, Any]:
        """Data that this extension was loaded with.

        If accessed before this extension is loaded and the app is running this
        will raise RuntimeError.
        """
        if self._data is None:
            raise RuntimeError(
                "Cannot access 'data' attribute before extensi  on has been loaded"
            )

        return self._data

    def __call__(
        self,
        target: Union[CommandRegistrar, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable:
        return self.load(target, data)

    def load(
        self,
        target: Union[CommandRegistrar, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable:
        """Load the extension and add all listeners and commands to the target.

        When the extension should be unloaded again the function returned
        should be called.
        """
        if isinstance(target, EventDispatcher):
            for event in self.listeners.values():
                for _, callback in event:
                    target.add_listener(callback)

        if isinstance(target, CommandRegistrar):
            for command in self.commands.values():
                target.register_command(command)

        self._data = data

        return self.unload

    def unload(self, target: Union[CommandRegistrar, EventDispatcher]) -> None:
        if isinstance(target, EventDispatcher):
            for event in self.listeners.values():
                for annotation, callback in event:
                    target.remove_listener(callback, event=annotation)

        if isinstance(target, CommandRegistrar):
            for command in self.commands.values():
                target.register_command(command)
