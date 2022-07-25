import importlib
import importlib.util
import sys
from typing import Any, Callable, Dict, Optional, Union

from wumpy.interactions import (
    CommandRegistrar, ComponentHandler, SubcommandGroup
)

from ._dispatch import EventDispatcher
from ._errors import ExtensionFailure

__all__ = (
    'Extension',
    'ExtensionLoader',
)


class Extension(CommandRegistrar, ComponentHandler, EventDispatcher):
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
                "Cannot access 'data' attribute before extension has been loaded"
            )

        return self._data

    def __call__(
        self,
        target: Union[CommandRegistrar, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable[[Union[CommandRegistrar, EventDispatcher]], None]:
        return self.load(target, data)

    def load(
        self,
        target: Union[CommandRegistrar, ComponentHandler, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable[[Union[CommandRegistrar, EventDispatcher]], None]:
        """Load the extension and add all listeners and commands to the target.

        When the extension should be unloaded again the function returned
        should be called.
        """
        if isinstance(target, EventDispatcher):
            for name in self._listeners.values():
                for event, callbacks in name.items():
                    for callback in callbacks:
                        target.add_listener(callback, event=event)

        if isinstance(target, CommandRegistrar):
            for command in self._commands.values():
                target.add_command(command)

        if isinstance(target, ComponentHandler):
            for pattern, func in self._regex_components.items():
                target.add_component(pattern, func)

        self._data = data

        return self.unload

    def unload(self, target: Union[CommandRegistrar, EventDispatcher]) -> None:
        if isinstance(target, EventDispatcher):
            for name in self._listeners.values():
                for event, callbacks in name.items():
                    for callback in callbacks:
                        target.remove_listener(callback, event=event)

        if isinstance(target, CommandRegistrar):
            for command in self._commands.values():
                target.remove_command(command)

        if isinstance(target, ComponentHandler):
            for pattern, func in self._regex_components.items():
                target.add_component(pattern, func)


def _is_submodule(a: str, b: str) -> bool:
    """Check if 'a' is a submodule of 'b'."""
    # The latter condition doesn't work when a == b so we need to add it
    # explicitly. We also need to add a trailing period so that 'abc' doesn't
    # accidentally match 'abcdefg' which is in-fact not a submodule.
    return a == b or a.startswith(b + '.')


class ExtensionLoader(CommandRegistrar, EventDispatcher):
    """Simple mixin that allows dynamically loading extensions."""

    extensions: Dict[str, Callable[[Union[CommandRegistrar, EventDispatcher]], object]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.extensions = {}

    def _remove_module(self, module: str) -> None:
        """Attempt to find all references to a module and remove them.

        This should be used as a last-resort to clean up from a module and
        restore the state of the extension loader.
        """
        for name in self._listeners.values():
            for event, callbacks in name.items():
                for callback in [c for c in callbacks if _is_submodule(c.__module__, module)]:
                    self.remove_listener(callback, event=event)

        for command in self._commands.values():
            if (
                    not isinstance(command, SubcommandGroup)
                    and _is_submodule(command.callback.__module__, module)
            ):
                self.remove_command(command)

    def load_extension(self, path: str, package: Optional[str] = None, **kwargs: Any) -> None:
        """Load an extension at `path`.

        `path` is the path to the file, dot-seperated like Python imports.
        It can be a relative import of `package` is specified, which should be
        `__name__` most of the times. Followed by a `:` and the name of the
        callback to load extension (Extension instance or a callable).

        Parameters:
            path:
                The path to the file, followed by a `:` and the name of the
                callback to the extension.
            package:
                Needs to be specified if `path` is relative, should be
                `__name__` for the majority of uses.

        Raises:
            TypeError: `package` wasn't passed when `path` is relative.
            ValueError: `path` is already loaded or invalid.
            ExtensionFailure: Failed to execute the module or call the loader.
            ValueError: The variable name of the loader is incorrect.
        """
        name, var = path.split(':', maxsplit=1)

        try:
            resolved = importlib.util.resolve_name(name, package)
        except (ImportError, ValueError) as err:
            if not package:
                raise TypeError(
                    "'package' is a required argument when 'path' is relative"
                ) from err
            else:
                raise ValueError("'path' walks too many parent directories") from err

        if resolved in self.extensions:
            raise ValueError("'path' cannot be a path to an already loaded extension")

        spec = importlib.util.find_spec(resolved, package)
        if spec is None:
            raise ValueError("'path' is not a path to a valid Python file")

        ext = importlib.util.module_from_spec(spec)
        sys.modules[resolved] = ext  # This isn't actually done automatically

        try:
            # module_from_spec() relies on and has code that attempts to
            # override the 'loader' attribute unless that raises
            # AttributeError at which point someone probably has messed around
            # with importer hooks and can only blame themselves. It should be
            # safe to assume spec's loader attribute is not None
            spec.loader.exec_module(ext)  # type: ignore
        except Exception as err:
            del sys.modules[resolved]
            raise ExtensionFailure(f"Failed to execute extension '{resolved}'") from err

        # Attempt to load the extension by retrieving the loader
        try:
            loader = getattr(ext, var)
        except AttributeError:
            del sys.modules[resolved]
            raise ValueError(
                f"Could not find variable '{var}' of '{resolved}' to load the extension"
            )

        if not callable(loader):
            del sys.modules[resolved]
            raise ExtensionFailure(
                f"Failed to load extension: '{type(loader).__name__}' is not callable"
            )

        try:
            unloader = loader(self, kwargs)
        except Exception as err:
            # This is actually very bad because this method is supposed to
            # return the callback that unloads the listeners and commands.
            # There is a potential that some listeners and commands were loaded
            # before running into the error meaning that we might not be able
            # to cleanup!
            del sys.modules[resolved]

            # We can try our best to recover but this can't fix attributes set
            # by the user or other code that was ran.
            self._remove_module(resolved)

            raise ExtensionFailure(f"Failed call loader '{var}' of '{resolved}'") from err

        # After all places where things can go wrong, it looks like we actually
        # successfully loaded a module!
        self.extensions[resolved] = unloader

    def unload_extension(self, path: str, package: Optional[str] = None) -> None:
        """Unload a previously loaded extension.

        Parameters:
            path: The path to the extension, does not require a `:`.
            package: Required if `path` is relative, see `load_extension()`.

        Raises:
            TypeError: `package` wasn't passed when `path` is relative.
            ValueError: `path` isn't an already loaded extension.
            ExtensionFailure: The unloader callback raised an exception.
        """
        try:
            name, _ = path.split(':', maxsplit=1)
        except ValueError:
            # 'path' doesn't contain an ':' character and so it can't be
            # unpacked to a tuple with two elements.
            name = path

        try:
            resolved = importlib.util.resolve_name(name, package)
        except (ImportError, ValueError) as err:
            if not package:
                raise TypeError(
                    "'package' is a required argument when 'path' is relative"
                ) from err
            else:
                raise ValueError("'path' walks too many parent directories") from err

        if resolved not in self.extensions:
            raise ValueError(f"'{path}' is not an already loaded extension")

        try:
            self.extensions[resolved](self)
        except Exception as err:
            # This is *also* very bad, something stopped the extension from
            # finalizing and cleaning up. We can do our best to clean up on the
            # library's part though.
            self._remove_module(resolved)
            raise ExtensionFailure(
                'Failed to unload extension because unloader for '
                f"extension '{resolved}' raised an exception"
            ) from err

        finally:
            # Clean up sys.modules
            del sys.modules[resolved]
