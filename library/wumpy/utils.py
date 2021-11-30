import functools
import inspect
from types import FunctionType, LambdaType
from typing import (
    Any, Awaitable, BinaryIO, Callable, ClassVar, Coroutine, Dict, List, Optional, Tuple,
    Type, TypeVar, Union, overload
)

import anyio.abc
from typing_extensions import Final, final

from .errors import CommandSetupError
from .models import Snowflake

__all__ = (
    'dump_json', 'load_json', 'MISSING', 'File',
    'ErrorHandlerMixin', 'Event', 'EventDispatcher'
)


try:
    import orjson

    dump_json = orjson.dumps
    load_json = orjson.loads

except ImportError:
    import json

    dump_json = json.dumps
    load_json = json.loads


def _eval_annotations(obj: Callable) -> Dict[str, Any]:
    """Eval a callable's annotations.

    This is primarily a backport of Python 3.10's `get_annotations()`
    method implemented by Larry Hastings:
    https://github.com/python/cpython/commit/74613a46fc79cacc88d3eae4105b12691cd4ba20

    Parameters:
        obj: The received callable to evaluate

    Returns:
        A dictionary of parameter name to its annotation.
    """
    unwrapped = obj
    while True:
        if hasattr(unwrapped, '__wrapped__'):
            unwrapped = unwrapped.__wrapped__
            continue
        if isinstance(unwrapped, functools.partial):
            unwrapped = unwrapped.func
            continue
        break

    annotations = getattr(unwrapped, '__annotations__', None)
    eval_globals = getattr(unwrapped, '__globals__', None)

    if annotations is None or not annotations:
        return {}

    if not isinstance(annotations, dict):
        raise ValueError(f'{unwrapped!r}.__annotations__ is neither a dict nor None')

    try:
        return {
            key: value if not isinstance(value, str) else eval(value, eval_globals)
            for key, value in annotations.items()
        }
    except (NameError, SyntaxError) as e:
        raise ValueError(f'Could not evaluate the annotations of {unwrapped!r}') from e


def _get_as_snowflake(data: Optional[dict], key: str) -> Optional[Snowflake]:
    """Get a key as a snowflake.

    Returns None if `data` is None or does not have the key.
    """
    if data is None:
        return None

    value = data.get(key)
    return Snowflake(value) if value is not None else None


@final
class MissingType(object):
    """Representing an optional default when no value has been passed.

    This is mainly used as a sentinel value for defaults to work nicely
    with typehints, so that `Optional[X]` doesn't have to be used.
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING: Final[Any] = MissingType()


class File:
    """Representing a file to be uploaded to Discord."""

    source: BinaryIO
    filename: str

    __slots__ = ('source', 'filename')

    def __init__(self, source: BinaryIO, filename: str, *, spoiler: bool = False) -> None:
        self.source = source

        # We use the removeprefix methods as they do nothing if the string does not
        # start with the string passed.
        if not spoiler:
            self.filename = filename.removeprefix('SPOILER_')
        else:
            # The user may have already added a SPOILER_ prefix
            self.filename = 'SPOILER_' + filename.removeprefix('SPOILER_')

    def read(self, n: int) -> bytes:
        return self.source.read(n)

    def close(self) -> None:
        return self.source.close()


class Event:
    """Parent class for events, meant to be read from annotations.

    Subclasses should set the `name` class variable which is used when
    dispatching and emitting events.

    To start using the event all you need to do is annotate a listener with
    your subclass and it will automatically be registered with the name
    specified in the class variable.

    All arguments passed into the dispatch method will be forwarded to the
    your subclass' `__init__()`.
    """

    NAME: ClassVar[str]

    __slots__ = ()  # If subclasses want to use it

    def __init__(self, *args: Any) -> None:
        """Initializer called with arguments passed to the dispatch method."""
        raise NotImplementedError()


def _extract_event(callback: Callable[..., Coroutine]) -> Type[Event]:
    """Extract the event from the callback.

    This function also ensures that the callback is an acceptable listener
    and will raise TypeError otherwise.

    Because of how EventDispatcher is a mixin, in an attempt to not clutter
    its subclasses this is placed globally in the file.
    """
    if not inspect.iscoroutinefunction(callback):
        raise TypeError("'callback' has to be a coroutine function")

    signature = inspect.signature(callback)

    if len(signature.parameters) == 0:
        raise TypeError("'callback' has to have at least one parameter")

    defaulted = [
        # Find all parameters that have a default
        param for param in signature.parameters.values()
        if param.default != param.empty
    ]
    if len(signature.parameters) - len(defaulted) > 1:
        raise TypeError("'callback' cannot have more than one non-default parameter")

    # Grab the first parameter which *should* be the parameter that has the
    # event annotation.
    param = list(signature.parameters.values())[0]

    if param.kind is param.kind.KEYWORD_ONLY:
        raise TypeError("The first parameter of 'callback' cannot be keyword-only")

    annotation = _eval_annotations(callback).get(param.name)

    if annotation is None or not issubclass(annotation, Event):
        raise TypeError(
            "The first parameter of 'callback' has to be annotated with an 'Event' subclass"
        )

    if annotation == Event:
        # It should be a subclass of Event
        raise TypeError(
            "The first parameter of 'callback' cannot be annotated with 'Event' directly"
        )
    return annotation


C = TypeVar('C', bound='Callable[..., Coroutine]')


class ErrorHandlerMixin:
    """Mixin that allows registering error handlers.

    This being a mixin means that it takes no arguments in its `__init__`
    and any passed will be forwarded to `super()`.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.error_handlers = []

    async def handle_error(
        self,
        context: Any,
        raised: Exception,
        *,
        callback: Optional[Callable[..., Awaitable]] = None
    ) -> None:
        """Handle an error that occured - calling registered handlers.

        Following the sorted order of error handlers this will call them by
        how "broad" the error is considered - so that subclasses are called
        before their parents.

        The way an error handler marks an error as handled is by returning
        `True`, any other value is discarded.

        If no handler handled the error the `callback` argument is called, this
        allows chaining error handlers on levels.

        Parameters:
            context: The one argument to pass onto the handler.
            raised: The `Exception` subclass that was raised.
            callback: Callback used if no handler handled the error.

        Raises:
            Exception: The `Exception` subclass that was passed in.
        """
        for error, handler in self.error_handlers:
            if not isinstance(raised, error):
                continue

            if await handler(context, raised) is True:
                break
        else:
            if callback is None:
                return

            # No handler at our level handled the error, propagate it up to a
            # level above or similar uses.
            await callback(context, raised)

    def register_error_handler(
        self,
        callback: Callable,
        *,
        exception: Type[Exception] = Exception
    ) -> None:
        self.error_handlers.append((exception, callback))

        # First sort the error handlers by name (this makes the result
        # determinable no matter what the order is) and then by the length of
        # its __mro__. The more parents the class has the longer its __mro__
        # will be and the more "narrow" it will be considered.
        self.error_handlers.sort(key=lambda item: str(item[0]))
        self.error_handlers.sort(key=lambda item: len(item[0].__mro__), reverse=True)

    @overload
    def error(self, *, type: Type[Exception]) -> Callable[[C], C]:
        ...

    @overload
    def error(self, callback: C) -> C:
        ...

    def error(
        self,
        callback: Optional[C] = None,
        *,
        type: Optional[Type[Exception]] = None
    ) -> Union[Callable[[C], C], C]:
        """Decorator to register an error handler.

        This decorator is designed to be called with and without parenthesis.
        """
        def decorator(func: C) -> C:
            self.register_error_handler(func, exception=type or Exception)
            return func

        if callback is not None:
            return decorator(callback)

        return decorator


class EventDispatcher:
    """Mixin to be able to dispatch events.

    Attributes:
        listeners:
            A dictionary of event names to a pair of event types and callback
            associated with it
    """

    listeners: Dict[str, List[Tuple[Type[Event], Callable[..., Coroutine]]]]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.listeners = {}

    def dispatch(self, event: str, *args: Any, tg: anyio.abc.TaskGroup) -> None:
        """Dispatch appropriate listeners.

        The callbacks will be started with the task group and passed the
        arguments given.

        Parameters:
            event: The event to dispatch
            *args: Arguments to pass onto the Event initializer
            tg: Task group to start the callbacks with
        """
        for initializer, callback in self.listeners.get(event, []):
            tg.start_soon(callback, initializer(*args))

    def add_listener(self, callback: Callable[..., Coroutine]) -> None:
        """Register and add a listener callback.

        The event it listens for will be read from the callback's arguments.

        Parameters:
            callback: The callback to register as a listener
        """
        annotation = _extract_event(callback)

        if annotation.NAME in self.listeners:
            self.listeners[annotation.NAME].append((annotation, callback))
        else:
            self.listeners[annotation.NAME] = [(annotation, callback)]

    def remove_listener(
        self,
        callback: Callable[..., Coroutine],
        *,
        event: Union[str, Type[Event], None] = None
    ) -> None:
        """Remove a particular listener callback.

        It is heavily encouraged to pass `event` if it is known to improve
        the performance, omitting it means all listeners for all events need to
        be checked.

        Parameters:
            callback: The registered callback to remove.
            event: The event that this callback is registered under.
        """
        if event is None:
            event = _extract_event(callback)

        if isinstance(event, str):
            name = event
        elif isinstance(event, type) and issubclass(event, Event):
            name = event.NAME
        else:
            raise TypeError(f"Expected 'str' or 'Event' subclass, got '{type(event).__name__}'")

        container = self.listeners.get(name, [])
        for i, (_, listener) in enumerate(container):
            if listener == callback:
                container.pop(i)

                if not container:
                    # The container is now empty so we can remove it from the
                    # dictionary
                    del self.listeners[name]

                return

        raise ValueError(f"{callback} isn't a registered callback under {event}")

    @overload
    def listener(self, callback: C) -> C:
        ...

    @overload
    def listener(self) -> Callable[[C], C]:
        ...

    def listener(self, callback: Optional[C] = None) -> Union[Callable[[C], C], C]:
        """Decorator to register a listener.

        This decorator works both with and without parenthesis.

        Examples:

            ```python
            @app.listener()
            async def event_listener(event: Event) -> None:
                ...
            ```
        """
        def decorator(func: C) -> C:
            self.add_listener(func)
            return func

        if callback is not None:
            return decorator(callback)

        return decorator