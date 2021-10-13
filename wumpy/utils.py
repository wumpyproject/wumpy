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

import inspect
from typing import (
    Any, BinaryIO, Callable, ClassVar, Coroutine, Dict, List, Optional,
    Tuple, Type, TypeVar, Union, overload
)

import anyio.abc
from typing_extensions import Final, final

__all__ = ('MISSING', 'File', 'Event', 'EventDispatcher')


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
    """Subclass for events, meant to be read from annotations."""

    _name: ClassVar[str]

    def __init__(self, data: Any) -> None:
        raise NotImplementedError()


C = TypeVar('C', bound='Callable[[Event], Coroutine]')


class EventDispatcher:
    """Mixin to be able to dispatch events."""

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
        signature = inspect.signature(callback)

        if len(signature.parameters) != 1:
            raise TypeError(f'Listener callback should have one argument, not {signature}')

        # There should be one argument in the parameters, which means it is
        # safe for us to convert it to a list and grab the first item.
        annotation = list(signature.parameters.values())[0].annotation

        if not issubclass(annotation, Event):
            raise TypeError('Listener argument annotation should be a subclass of Event')

        if annotation._name in self.listeners:
            self.listeners[annotation._name].append((annotation, callback))
        else:
            self.listeners[annotation._name] = [(annotation, callback)]

    @overload
    def listener(self, func: C, /) -> C:
        ...

    @overload
    def listener(self) -> Callable[[C], C]:
        ...

    def listener(self, callback: Optional[C] = None, /) -> Union[Callable[[C], C], C]:
        def decorator(func: C) -> C:
            self.add_listener(func)
            return func

        if callback is not None:
            return decorator(callback)

        return decorator
