import importlib
import importlib.util
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Union, Tuple

from wumpy.interactions import (
    CommandRegistrar, ComponentHandler, SubcommandGroup, ErrorHandlerMixin
)

from ._dispatch import EventDispatcher
from ._errors import ExtensionFailure

__all__ = (
    'Extension',
    'ExtensionLoader',
)


class Extension(CommandRegistrar, ComponentHandler, EventDispatcher, ErrorHandlerMixin):
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
        target: Union[CommandRegistrar, ComponentHandler, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable[[Union[CommandRegistrar, ComponentHandler, EventDispatcher]], None]:
        return self.load(target, data)

    def load(
        self,
        target: Union[CommandRegistrar, ComponentHandler, EventDispatcher],
        data: Dict[str, Any]
    ) -> Callable[[Union[CommandRegistrar, ComponentHandler, EventDispatcher]], None]:
        """Load the extension and add all listeners and commands to the target.

        When the extension should be unloaded again the function returned
        should be called.

        Parameters:
            target: The target to load registered objects to.
            data: Extra information passed to the extension when loading.

        Returns:
            The callback to call to unload the extension.
        """
        if isinstance(target, ErrorHandlerMixin):
            target._error_handlers.extend(self._error_handlers)

        if isinstance(target, EventDispatcher):
            # When loading the callbacks and events, it is important that we
            # copy the containers (list and dicts) so that if commands are
            # added to the extension in the future, they are not added to the
            # target in weird behaviour.

            for name, events in self._listeners.items():
                if name not in target._listeners:
                    container = {}
                    target._listeners[name] = container
                else:
                    container = target._listeners[name]

                for initializer, callbacks in events.items():
                    if initializer in container:
                        container[initializer].extend(callbacks)
                    else:
                        # Insert a shallow copy of the list object itself
                        container[initializer] = callbacks.copy()

        if isinstance(target, CommandRegistrar):
            target._commands.update(self._commands)

        if isinstance(target, ComponentHandler):
            target._regex_components.extend(self._regex_components)

        self._data = data

        return self.unload

    def unload(
            self,
            target: Union[CommandRegistrar, ComponentHandler, EventDispatcher]
    ) -> None:
        """Unload the extension from the target.

        This method is designed to make no assumptions and therefore never
        fail with an error.

        Parameters:
            target: The target to remove previously loaded objects from.

        Raises:
            Exception: Something went wrong trying to unload the extension.
        """
        # NOTE: Any interaction with 'target' MUST be wrapped with a
        # try/except statement. This method is designed to always continue,
        # no matter what, so we cannot trust the user.

        to_raise = None

        if isinstance(target, ErrorHandlerMixin):
            for callback in self._error_handlers:
                try:
                    target._error_handlers.remove(callback)
                except Exception as err:
                    err.__cause__ = to_raise
                    to_raise = err

        if isinstance(target, EventDispatcher):
            for name, events in self._listeners.items():
                try:
                    container = target._listeners[name]
                except Exception as err:
                    err.__cause__ = to_raise
                    to_raise = err
                    continue

                for initializer, callbacks in events.items():
                    try:
                        registered = container[initializer]
                    except Exception as err:
                        err.__cause__ = to_raise
                        to_raise = err
                        continue

                    # This doesn't have great performance and a list
                    # comprehension would provide better performance, however,
                    # to ensure no suprises in the future the internal
                    # structures shoud always be mutated.
                    for callback in callbacks:
                        try:
                            registered.remove(callback)
                        except Exception as err:
                            err.__cause__ = to_raise
                            to_raise = err

                    # Now that we have removed all callbacks that should be
                    # removed, clean up empty structures if possible

                    try:
                        if not registered:
                            del container[initializer]
                    except Exception as err:
                        err.__cause__ = to_raise
                        to_raise = err

                try:
                    if not container:
                        del target._listeners[name]
                except Exception as err:
                    err.__cause__ = to_raise
                    to_raise = err

        if isinstance(target, CommandRegistrar):
            for command in self._commands:
                try:
                    del target._commands[command]
                except KeyError:
                    pass
                except Exception as err:
                    err.__cause__ = to_raise
                    to_raise = err

        if isinstance(target, ComponentHandler):
            for element in self._regex_components:
                try:
                    target._regex_components.remove(element)
                except Exception as err:
                    err.__cause__ = to_raise
                    to_raise = err

        self._data = None

        if to_raise:
            raise to_raise


def _is_submodule(a: str, b: str) -> bool:
    """Check if 'a' is a submodule of 'b'."""
    # The latter condition doesn't work when a == b so we need to add it
    # explicitly. We also need to add a trailing period so that 'abc' doesn't
    # accidentally match 'abcdefg' which is in-fact not a submodule.
    return a == b or a.startswith(b + '.')


class ExtensionLoader:
    """Mixin that allows dynamically loading extensions.

    This class has been implemented with being subclasses of
    `CommandRegistrar`, `ComponentHandler`, `ErrorHandlerMixin`, and
    `EventDispatcher` in mind. It can be used with other mixins / parents, but
    keep in mind that those cannot be accounted for if something fails.
    """

    _extensions: Dict[
        str, Tuple[
            ModuleType,
            Callable[[Union[CommandRegistrar, EventDispatcher]], object]
        ]
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._extensions = {}

    def _remove_module(self, module: str) -> None:
        """Attempt to find all references to a module and remove them.

        This should be used as a last-resort to clean up from a module and
        restore the state of the extension loader.

        Parameters:
            module:
                The module to look for. References to submodules will also
                be removed if possible.
        """
        if isinstance(self, ErrorHandlerMixin):
            removed_handlers = [
                cb for cb in self._error_handlers
                if _is_submodule(cb.__module__, module)
            ]

            for handler in removed_handlers:
                self._error_handlers.remove(handler)

        if isinstance(self, EventDispatcher):
            empty_events = []
            for name, events in self._listeners.items():
                empty_callbacks = []
                for initializer, callbacks in events.items():
                    # This list comprehension means we don't iterate the same
                    # list that is mutated, since it creates a new one.
                    to_remove = [c for c in callbacks if _is_submodule(c.__module__, module)]
                    for item in to_remove:
                        callbacks.remove(item)

                    if not callbacks:
                        empty_callbacks.append(initializer)

                # Clean up empty callbacks after we are done iterating
                for key in empty_callbacks:
                    del events[key]

                if not events:
                    empty_events.append(name)

            for key in empty_events:
                del self._listeners[key]

        if isinstance(self, CommandRegistrar):
            removed_commands = []
            for name, command in self._commands.items():
                if not isinstance(command, SubcommandGroup):
                    if _is_submodule(command.callback.__module__, module):
                        removed_commands.append(name)

                    continue

                # The command in question is a subcommand group, the origin
                # will have to be looked up in one its subcommand. Because the
                # subcommand group should not be mutated, it is not possible
                # to only remove the subcommands that is in the module.
                for subcommand in command._commands.values():
                    if not isinstance(subcommand, SubcommandGroup):
                        if _is_submodule(subcommand.callback.__module__, module):
                            removed_commands.append(name)

                        break

                    for nested_subcommand in subcommand._commands.values():
                        # Discord only supports 2 levels of nesting. Now, it
                        # is possible that the user has created more than that
                        # but it is not worth the effort to continue like this.
                        if isinstance(nested_subcommand, SubcommandGroup):
                            continue

                        if _is_submodule(nested_subcommand.callback.__module, module):
                            removed_commands.append(name)

                        break

            for name in removed_commands:
                del self._commands[name]

        if isinstance(self, ComponentHandler):
            removed_components = []
            for pair in self._regex_components:
                if _is_submodule(pair[1].__module__, module):
                    removed_components.append(pair)

            for component in removed_components:
                self._regex_components.remove(component)

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

        if resolved in self._extensions:
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

            if isinstance(loader, Extension):
                try:
                    loader.unload(self)
                except Exception as e:
                    err = e

            # We can try our best to recover but this can't fix attributes set
            # by the user or other code that was ran.
            self._remove_module(resolved)

            raise ExtensionFailure(f"Failed call loader '{var}' of '{resolved}'") from err

        # After all places where things can go wrong, it looks like we actually
        # successfully loaded a module!
        self._extensions[resolved] = (ext, unloader)

    def get_extension(self, path: str, package: Optional[str] = None) -> ModuleType:
        """Get a loaded extension.

        Parameters:
            path: The path to the extension, does not require a `:`.
            package: Required if `path` is relative, see `load_extension()`.

        Returns:
            The loaded module. This enables functions in the module to be used.
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

        if resolved not in self._extensions:
            raise ValueError(f"'{path}' is not an already loaded extension")

        return self._extensions[resolved][0]

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

        if resolved not in self._extensions:
            raise ValueError(f"'{path}' is not an already loaded extension")

        try:
            self._extensions[resolved][1](self)
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
