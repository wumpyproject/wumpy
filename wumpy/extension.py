import importlib
import importlib.util
import sys
from typing import Any, Callable, Dict, Optional, Union

from .interactions import CommandRegistrar
from .utils import EventDispatcher

__all__ = ('Extension', 'ExtensionLoader')


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


def _is_submodule(a: str, b: str, /) -> bool:
    """Check if 'a' is a submodule of 'b'."""
    # The latter condition doesn't work when a == b so we need to add it
    # explicitly. We also need to add a trailing period so that 'abc' doesn't
    # accidentally match 'abcdefg' which is in-fact not a submodule.
    return a == b or a.startswith(b + '.')


class ExtensionLoader(CommandRegistrar, EventDispatcher):
    """Simple mixin that allows dynamically loading extensions."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.extensions = {}

    def _remove_module(self, module: str) -> None:
        """Attempt to find all references to a module and remove them.

        This should be used as a last-resort to clean up from a module and
        restore the state of the extension loader.
        """
        for event in self.listeners.values():
            for annotation, callback in event:
                if _is_submodule(callback.__module__, module):
                    self.remove_listener(callback, event=annotation)

        for command in self.commands.values():
            if _is_submodule(command.callback.__module__, module):
                self.unregister_command(command)

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
        """
        name, var = path.split(':', maxsplit=1)

        try:
            resolved = importlib.util.resolve_name(name, package)
        except ImportError:
            # 'package' is None but 'path' is a relative import, or 'path' is
            # trying to go too many parent directories far
            raise  # TODO

        if resolved in self.extensions:
            raise ValueError('Extension already loaded')

        spec = importlib.util.find_spec(resolved, package)
        if spec is None:
            raise ValueError('Could not find that extension')

        ext = importlib.util.module_from_spec(spec)
        # This isn't actually done automatically
        sys.modules[resolved] = ext

        try:
            # module_from_spec() relies on and has code that attempts to
            # override the 'loader' attribute unless that raises
            # AttrributeError at which point someone probably has messed around
            # with importer hooks and can only blame themselves. It should be
            # safe to assume spec's loader attribute is not None
            spec.loader.exec_module(ext)  # type: ignore
        except Exception:
            del sys.modules[resolved]
            raise  # TODO

        # Attempt to load the extension by retrieving the loader
        try:
            loader = getattr(ext, var)
        except AttributeError:
            del sys.modules[resolved]
            raise ValueError(f'Could not find {var} load callback')

        if not callable(loader):
            raise ValueError('Loader is not callable')

        try:
            unloader = loader(self, kwargs)
        except Exception:
            # This is actually very bad because this method is supposed to
            # return the callback that unloads the listeners and commands.
            # There is a potential that some listeners and commands were loaded
            # before running into the error meaning that we might not be able
            # to cleanup!
            del sys.modules[resolved]

            # We may have loaded a folder that added other files to sys.modules
            for module in list(sys.modules):
                if _is_submodule(module, resolved):
                    del sys.modules[module]

            if isinstance(loader, Extension):
                # There could be potential cleanup code the user put in the
                # unload() so it's best to call it if possible..
                loader.unload(self)

            # We can try our best to recover but this can't fix attributes set
            # by the user or other code that was ran.
            self._remove_module(resolved)

            raise

        # After all places where things can go wrong, it looks like we actually
        # successfully loaded a module!
        self.extensions[resolved] = unloader

    def unload_extension(self, path: str, package: Optional[str] = None) -> None:
        """Unload a previously loaded extension.

        Parameters:
            path: The path to the extension, does not require a `:`.
            package: Required if `path` is relative, see `load_extension()`.
        """
        name, _ = path.split(':', maxsplit=1)

        try:
            resolved = importlib.util.resolve_name(name, package)
        except ImportError:
            # 'package' is None but 'path' is a relative import, or 'path' is
            # trying to go too many parent directories far
            raise  # TODO

        if resolved not in self.extensions:
            raise ValueError('That is not a loaded extension')

        try:
            self.extensions[resolved](self)
        except Exception:
            # This is *also* very bad, something stopped the extension from
            # finalizing and cleaning up. We can do our best to clean up on the
            # library's part though.
            self._remove_module(resolved)
            raise

        finally:
            # Clean up sys.modules
            del sys.modules[resolved]

            for module in list(sys.modules):
                if _is_submodule(module, resolved):
                    del sys.modules[module]
