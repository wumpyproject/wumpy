"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import functools
from typing import (
    Any, BinaryIO, Callable, ClassVar, Coroutine, Dict, List, Optional, Tuple,
    Type, TypeVar, Union, overload
)

import anyio.abc
from typing_extensions import Final, final

__all__ = ('dump_json', 'load_json', 'MISSING', 'File', 'Event', 'EventDispatcher')


try:
    import orjson

    def orjson_dump(obj: Any) -> str:
        # orjson returns bytes but aiohttp expects a string
        return orjson.dumps(obj).decode('utf-8')

    dump_json = orjson_dump
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

    name: ClassVar[str]

    __slots__ = ()  # If subclasses want to use it

    def __init__(self, *args: Any) -> None:
        """Initializer called with arguments passed to the dispatch method."""
        raise NotImplementedError()


C = TypeVar('C', bound='Callable[[Event], Coroutine]')


class EventDispatcher:
    """Mixin to be able to dispatch events.

    Attributes:
        listeners:
            A dictionary of event names to a pair of event types and callback
            associated with it
    """

    listeners: Dict[str, List[Tuple[Type[Event], Callable[[Event], Coroutine]]]]

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

    def add_listener(self, callback: Callable[[Event], Coroutine]) -> None:
        """Register and add a listener callback.

        The event it listens for will be read from the callback's arguments.

        Parameters:
            callback: The callback to register as a listener
        """
        annotations = _eval_annotations(callback)

        if len(annotations) != 1:
            raise TypeError(f'Listener callback should have one argument, not {len(annotations)}')

        # There should be one argument in the parameters, which means it is
        # safe for us to convert it to a list and grab the first item.
        annotation = list(annotations.values())[0].annotation

        if not issubclass(annotation, Event):
            raise TypeError('Listener argument annotation should be a subclass of Event')

        if annotation.name in self.listeners:
            self.listeners[annotation.name].append((annotation, callback))
        else:
            self.listeners[annotation.name] = [(annotation, callback)]

    def remove_listener(
        self,
        callback: Callable[[Event], Coroutine],
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
            # We have two options, either do the evaluation again or loop
            # through all listeners for the correct one. Neither is ideal..
            for container in self.listeners.values():
                for i, (_, listener) in enumerate(container):
                    if listener == callback:
                        container.pop(i)
                        return

        else:
            if isinstance(event, str):
                container = self.listeners[event]
            elif issubclass(event, Event):
                container = self.listeners[event.name]
            else:
                raise TypeError(f"Expected 'str' or 'Event' subclass, got '{type(event).__name__}'")

            for i, (_, listener) in enumerate(container):
                if listener == callback:
                    container.pop(i)
                    return

        # If we reach here we didn't return, which means the callback couldn't
        # be found in by the listeners.
        raise ValueError(f"{callback} isn't a registered callback")

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
