import dataclasses
import inspect
import sys
import traceback
from abc import abstractmethod
from functools import partial
from typing import (
    Any, Callable, ClassVar, Coroutine, Dict, List, Mapping, NoReturn, Optional, Tuple,
    Type, TypeVar, Union, overload
)

import anyio
import anyio.abc
import anyio.lowlevel
from typing_extensions import Self, TypeAlias
from wumpy.models.utils import backport_slots

from .utils import _eval_annotations

__all__ = ['Event', 'EventDispatcher']


T = TypeVar('T')
CoroFunc: TypeAlias = 'Callable[..., Coroutine[Any, Any, T]]'
C = TypeVar('C', bound='CoroFunc[object]')


@dataclasses.dataclass(frozen=True)
class Event:
    """Parent class for events, meant to be read from annotations.

    Subclasses should set the `NAME` class variable which is used when
    dispatching and emitting events.

    To start using the event all you need to do is annotate a listener with
    your subclass and it will automatically be registered with the name
    specified in the class variable.

    The event will be initialized in the form of a `from_payload()`
    classmethod, see the docstring for more information.
    """

    NAME: ClassVar[str]

    __slots__ = ()  # If subclasses want to use it

    @classmethod
    @abstractmethod
    async def from_payload(
            cls,
            payload: Mapping[str, Any],
            cached: Optional[Any] = None
    ) -> Optional[Self]:
        """Initialize the event from a payload and cached values.

        Subclasses **must** override this method.

        This classmethod is meant as an initializer, and should return the
        instance that will be passed to the callback, or `None` to have the
        handler of this event be ignored.

        Parameters:
            payload: Deserialized JSON event from the gateway (`d` field).
            cached:
                Return value of the current cache. This will be the "old" value
                which was replaced by this event, or `None` if the cache did
                not keep any value.
        """
        raise NotImplementedError()


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ErrorEvent(Event):
    """Event dispatched when an error occured.

    This event only catches subclasses of `Exception`. Other exceptions, such
    as `KeyboardInterrupt` will not be dispatched with this event.

    If callbacks of this event raises an error, it is printed and ignored.

    Unlike other events, this one is special in its construction and does not
    corrolate to any given gateway event. Therefore this is instantiated using
    `__init__()` and subclasses are required to match the same signature.

    Attributes:
        exception: The exception that was raised.
        event:
            The event that was dispatched unless the exception that triggered
            this event came from the library without a dispatched event.
        callback:
            The callback which raised an error trying to handle the event,
            unless the exception came from the library without a callback.
    """

    # Note that this is a special event which does not implement the
    # usual from_payload() method because it does not get dispatched from
    # gateway events like other events.
    NAME: ClassVar[str] = '__ERROR'

    exception: Exception

    event: Optional[Event] = None

    # Return type is Any because the user might want to use the return type and
    # having it be object would not allow any meaningful operations.
    callback: Optional['CoroFunc[Any]'] = None

    @classmethod
    @abstractmethod
    async def from_payload(
            cls,
            payload: Mapping[str, Any],
            cached: Optional[Any] = None
    ) -> NoReturn:
        raise RuntimeError(
            f"{cls.__name__!r} cannot be dispatched using the 'from_payload()' method"
        )


def _extract_event(callback: 'Callable[..., object]') -> Type[Event]:
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

    if annotation is None or (isinstance(annotation, type) and not issubclass(annotation, Event)):
        raise TypeError(
            "The first parameter of 'callback' has to be annotated with an 'Event' subclass"
        )

    if annotation is Event:
        # It should be a subclass of Event
        raise TypeError(
            "The first parameter of 'callback' cannot be annotated with 'Event' directly"
        )
    return annotation


def _ignore_dispatch_error(
        exc: Exception,
        *,
        event: Union[str, Type[Event], Event, None] = None,
) -> None:
    # We can't trust that the user has defined a NAME class variable like they
    # should have. Maybe that's why we're printing this error...
    if isinstance(event, (type, Event)) and hasattr(event, 'NAME'):
        name = event.NAME
    else:
        name = event

    print(f'Ignoring exception handling event {name!r}:', file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__)


async def _wrap_error_callback(callback: 'CoroFunc[object]', event: Event) -> None:
    try:
        await callback(event)
    except Exception as exc:
        _ignore_dispatch_error(exc, event=event)


class EventDispatcher:
    """Small mixin class adding the ability to dispatch events.

    This class can be inherited from to get the `get_dispatch_handlers()` and
    `dispatch()` methods for dispatching event objects.

    Dispatching works by first calling `get_dispatch_handlers()` with the name
    of the event you wish to dispatch. This allows you to know whether later
    calling `dispatch()` will call any handlers - although it isn't completely
    correct as the event objects may return in their constructors. Afterwards
    you should call `dispatch()` to launch the handlers as tasks.
    """

    _listeners: Dict[
        str, Dict[
            Type[Event], List['CoroFunc[object]']
        ]
    ]

    __slots__ = ('_listeners',)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._listeners = {}

    def get_dispatch_handlers(
            self,
            event: str
    ) -> Dict[Type[Event], List['CoroFunc[object]']]:
        """Get the dispatch handlers for the event passed.

        The point of this separation from `dispatch()` is being able to know
        whether calling `dispatch()` will actually dispatch any handlers. That
        said, there is a possibility that all event objects will `None` meaning
        that no handler will be dispatched anyways.

        Parameters:
            event: The name of the event to dispatch.

        Returns:
            A dictionary with the key being the event constructor, and the
            value a list of callbacks that should be called with that event.
        """
        return self._listeners.get(event, {})

    async def dispatch_error(
            self,
            exc: Exception,
            *,
            event: Optional[Event] = None,
            callback: Optional['CoroFunc[Any]'] = None,
    ) -> None:
        """Dispatch an error that happened.

        This is safe to call for errors that happened while dispatching other
        events (it is not recursive).

        Parameters:
            exc: Exception instance that was raised.
            tg: Task group to dispatch callbacks with.
            event: The event instance that failed to dispatch.
        """
        if not isinstance(exc, Exception):
            if isinstance(exc, BaseException):
                # If it is a BaseException subclass (but not a subclass of
                # Exception like normal exceptions) then we want to raise an
                # error. The issue is that if we raise another type of error
                # like a TypeError then that may be swallowed somewhere (unlike
                # these subclasses of BaseException).
                raise exc  # Re-raise if it is a BaseException subclass

            raise TypeError(f'Expected subclass of Exception but got {type(exc).__name__!r}')

        handlers = self.get_dispatch_handlers(ErrorEvent.NAME)
        if not handlers:
            _ignore_dispatch_error(exc, event=event)
            await anyio.lowlevel.checkpoint()
            return

        async with anyio.create_task_group() as tg:
            for subclass, callbacks in handlers.items():
                try:
                    instance = subclass(exc, event=event, callback=callback)
                except Exception as exc:
                    _ignore_dispatch_error(exc, event=event)
                    continue

                if not callbacks:
                    _ignore_dispatch_error(exc, event=event)
                    continue

                for func in callbacks:
                    tg.start_soon(_wrap_error_callback, func, instance)

    async def _wrap_dispatch_callback(
            self,
            callback: 'CoroFunc[object]',
            event: Event,
    ) -> None:
        try:
            await callback(event)
        except Exception as exc:
            await self.dispatch_error(exc, event=event, callback=callback)

    async def _dispatch_event_instance(
            self,
            event: Type[Event],
            payload: Dict[str, Any],
            cached: Optional[Any],
            callbacks: List['CoroFunc[object]'],
    ) -> None:
        try:
            instance = await event.from_payload(payload, cached)
        except Exception as exc:
            await self.dispatch_error(exc)
            return

        if instance is None:
            await anyio.lowlevel.checkpoint()
            return

        async with anyio.create_task_group() as tg:
            for func in callbacks:
                tg.start_soon(partial(self._wrap_dispatch_callback, func, instance))

    async def dispatch(
            self,
            handlers: Dict[Type[Event], List['CoroFunc[object]']],
            payload: Dict[str, Any],
            cached: Tuple[Optional[Any], Optional[Any]],
    ) -> None:
        """Dispatch appropriate listeners.

        The callbacks will be started with the task group and passed the
        arguments given. Error handling is handled meaning that the task group
        should not get cancelled by an error in a callback.

        Parameters:
            handlers: The return value of `get_dispatch_handlers()`.
            payload: Data returned by the gateway to dispatch.
            cached: Return value of the cache representing the "old" value.
            tg: Task group to use when launching the callbacks.
        """
        if not handlers:
            await anyio.lowlevel.checkpoint()
            return

        async with anyio.create_task_group() as tg:
            for event, callbacks in handlers.items():
                tg.start_soon(partial(
                    self._dispatch_event_instance,
                    event, payload, cached, callbacks,
                ))

    def add_listener(
            self,
            callback: 'CoroFunc[object]',
            *,
            event: Optional[Type[Event]] = None
    ) -> None:
        """Register and add a listener callback.

        If `event` is `None`, the actual event will be introspected from the
        callback's parameter annotations.

        Parameters:
            callback: The callback to register as a listener.
            event: Event subclass it wishes to listen to.
        """
        if event is None:
            event = _extract_event(callback)

        if event.NAME in self._listeners:
            types = self._listeners[event.NAME]
            if event in types:
                types[event].append(callback)
            else:
                types[event] = [callback]
        else:
            self._listeners[event.NAME] = {event: [callback]}

    def remove_listener(
        self,
        callback: 'CoroFunc[object]',
        *,
        event: Union[str, Type[Event], None] = None
    ) -> None:
        """Remove a particular listener callback.

        It is heavily encouraged to pass `event` if it is known. Without it,
        the event will be introspected from the parameters.

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
            raise TypeError(
                f"Expected 'str' or 'Event' subclass, got '{type(event).__name__}'"
            )

        try:
            container = self._listeners[name]
        except KeyError:
            raise ValueError(f"{callback} isn't a registered callback under {event}") from None

        if isinstance(event, type):
            container[event].remove(callback)
        else:
            for event, callbacks in container.items():
                if callback in callbacks:
                    callbacks.remove(callback)
                    break
            else:
                raise ValueError(f"{callback} isn't a registered callback under {event}")

        # If, as a result of removing this callback, the container and list of
        # callbacks are empty, we can now remove them completely and clean up.
        if not container[event]:
            del container[event]

        if not container:
            del self._listeners[name]

    @overload
    def listener(self) -> Callable[[C], C]:
        ...

    @overload
    def listener(self, callback: Type[Event]) -> Callable[[C], C]:
        # This can technically be joined to the above overload, but it means
        # that the user will be encouraged (or confused) about passing any
        # arguments to the function.
        ...

    @overload
    def listener(self, callback: C) -> C:
        ...

    def listener(
            self,
            callback: Union[C, Type[Event], None] = None
    ) -> Union[Callable[[C], C], C]:
        """Decorator to register a listener.

        This decorator works both with and without parenthesis.

        Examples:

            ```python
            @app.listener()
            async def event_listener(event: Event) -> None:
                ...
            ```
        """
        event = None

        def decorator(func: C) -> C:
            self.add_listener(func, event=event)
            return func

        if isinstance(callback, type):
            if not issubclass(callback, Event):
                raise TypeError(
                    f"Expected subclass of 'Event' but received {callback.__name__!r}"
                    f'with bases {callback.mro()}'
                )

            event = callback
        elif callback is not None:
            return decorator(callback)

        return decorator
