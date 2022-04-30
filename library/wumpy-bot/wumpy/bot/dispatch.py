import inspect
from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any, Callable, ClassVar, Coroutine, Dict, List, Optional, Tuple, Type,
    TypeVar, Union, overload
)

import anyio.abc
from typing_extensions import Self

from .utils import _eval_annotations

__all__ = ['Event', 'EventDispatcher']


@dataclass(frozen=True)
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
    def from_payload(
            cls,
            payload: Dict[str, Any],
            cached: Tuple[Optional[Any], Optional[Any]]
    ) -> Self:
        """Initialize the event from a payload and cached values.

        This classmethod is meant as an initializer, and should return the
        instance that will be passed to the callback.

        Parameters:
            payload:
                Deserialized JSON event directly from the gateway (including
                the `op`, `t`, `d` and `s` keys).
            cached:
                Return value of the current cache. This will be a tuple with
                the first value - unless `None` - represents the "previous"
                value that was found in the cache. The second item in the tuple
                is the newly created and now cached value.
        """
        raise NotImplementedError()


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

    if annotation == Event:
        # It should be a subclass of Event
        raise TypeError(
            "The first parameter of 'callback' cannot be annotated with 'Event' directly"
        )
    return annotation


C = TypeVar('C', bound='Callable[..., Coroutine[Any, Any, object]]')


class EventDispatcher:
    """Mixin to be able to dispatch events."""

    _listeners: Dict[
        str, List[Tuple[
            Type[Event], 'Callable[..., Coroutine[Any, Any, object]]'
        ]]
    ]

    __slots__ = ('_listeners',)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._listeners = {}

    def dispatch(
            self,
            event: str,
            payload: Dict[str, Any],
            cached: Tuple[Optional[Any], Optional[Any]],
            *,
            tg: anyio.abc.TaskGroup
    ) -> None:
        """Dispatch appropriate listeners.

        The callbacks will be started with the task group and passed the
        arguments given.

        Parameters:
            event: The event to dispatch
            *args: Arguments to pass onto the Event initializer
            tg: Task group to start the callbacks with
        """
        for initializer, callback in self._listeners.get(event, []):
            tg.start_soon(callback, initializer.from_payload(payload, cached))

    def add_listener(
            self,
            callback: 'Callable[..., Coroutine[Any, Any, object]]',
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
            self._listeners[event.NAME].append((event, callback))
        else:
            self._listeners[event.NAME] = [(event, callback)]

    def remove_listener(
        self,
        callback: 'Callable[..., Coroutine[Any, Any, object]]',
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

        container = self._listeners.get(name, [])
        for i, (_, listener) in enumerate(container):
            if listener != callback:
                continue

            container.pop(i)

            if not container:
                # The container is now empty so we can remove it from the
                # dictionary
                del self._listeners[name]

            return

        raise ValueError(f"{callback} isn't a registered callback under {event}")

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
