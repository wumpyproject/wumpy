import sys
import traceback
from types import MappingProxyType
from typing import (
    Any, Callable, Coroutine, ItemsView, Iterator, KeysView, List, Mapping,
    Optional, TypeVar, Union, ValuesView, overload
)

import anyio
import anyio.lowlevel
from typing_extensions import Literal

__all__ = (
    'ErrorContext',
    'ErrorHandlerMixin',
    'CommandSetupError',
)


T = TypeVar('T')
Coro = Coroutine[Any, Any, T]


class ErrorContext(Mapping[str, Any]):
    """Contextual information about an error that happened.

    This class is a dict-like immutable mapping of relevant variables
    present when the error happened.

    An instance of this class is passed to error handlers. If an error handler
    raises an error, that error will be forwarded to the next error handler
    registered.

    Attributes:
        error: The exception/error that occured.
        internal: Whether the error came from the library.
    """

    error: Exception
    internal: bool

    _vars: 'MappingProxyType[str, Any]'

    __slots__ = ('error', 'internal', '_vars')

    def __init__(
            self,
            error: Exception,
            internal: bool,
            **kwargs: Any
    ) -> None:
        if not isinstance(error, BaseException):
            raise TypeError("'error' must be an Exception instance")
        elif not isinstance(error, Exception):
            # This is handled separately, because we don't want to raise a
            # TypeError (which might be captured higher up in the callstack)
            # instead of this BaseException.
            raise error  # type: ignore

        self.error = error
        self.internal = internal

        self._vars = MappingProxyType(kwargs)

    def __bool__(self) -> Literal[True]:
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        return (
            self.error == other.error
            and self.internal == other.internal
            and self._vars == other._vars
        )

    def __len__(self) -> int:
        return len(self._vars)

    def __contains__(self, item: object) -> bool:
        return item in self._vars if isinstance(item, str) else NotImplemented

    def __iter__(self) -> Iterator[str]:
        return iter(self._vars)

    def __getitem__(self, key: str) -> Any:
        """Lookup the key in the relevant variables.

        Common values include `'callback'`, `'event'`, `'context'`, and
        `'interaction'`. The variables present depend on where the error
        occured.

        This is implemented as an O(1) operation with a dictionary.

        Raises:
            KeyError: The key was not found by the variables.
        """
        return self._vars[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._vars.get(key, default)

    def items(self) -> ItemsView[str, Any]:
        return self._vars.items()

    def keys(self) -> KeysView[str]:
        return self._vars.keys()

    def values(self) -> ValuesView[Any]:
        return self._vars.values()


def _ignore_exception(context: ErrorContext) -> None:
    msg = 'Ignoring exception'
    if 'event' in context:
        msg += f" handling event {context['event']}"
    elif 'interaction' in context:
        msg += f" handling interaction {context['interaction']}"

    print(msg, file=sys.stderr)
    traceback.print_exception(
        type(context.error),
        context.error,
        context.error.__traceback__
    )


class ErrorHandlerMixin:
    """Mixin adding ability to handle errors.

    This mixin adds `handle_error()` to be called when an error is received,
    and `error()` decorator to register error handlers.

    Error handlers are dispatched in-order they have been added, sequentially,
    with the most recently added error handler called first. This means that
    you can register "root handlers" which get called if no other handler
    could handle the error, by registering them first.
    """

    _error_handlers: List[Callable[[ErrorContext], Coroutine[Any, Any, object]]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._error_handlers = []

    async def handle_error(self, context: ErrorContext) -> None:
        """Dispatch an error that happened to registered error handlers.

        This method does not return until one of the error handlers has
        returned `True` to indicate that it has been handled. Start it as a
        task to avoid waiting for this to complete.

        Parameters:
            context: The error context to supress and handle.
        """
        if not self._error_handlers:
            _ignore_exception(context)
            await anyio.lowlevel.checkpoint()
            return

        caught = False
        for handler in reversed(self._error_handlers):
            try:
                caught = await handler(context)
            except Exception as exc:
                context = ErrorContext(exc, False, context=context, callback=handler)

            if caught:
                return

        if not caught:
            _ignore_exception(context)

        # Unconditionally yield, we don't know whether the user has yielded.
        # We cannot trust user callbacks.
        await anyio.lowlevel.checkpoint()

    @overload
    def error(self) -> Callable[
        [Callable[[ErrorContext], Coro[T]]],
        Callable[[ErrorContext], Coro[T]]
    ]:
        ...

    @overload
    def error(
            self, callback: Callable[[ErrorContext], Coro[T]]
    ) -> Callable[[ErrorContext], Coro[T]]:
        ...

    def error(self, callback: Optional[Callable[[ErrorContext], Coro[T]]] = None) -> Union[
        Callable[[Callable[[ErrorContext], Coro[T]]], Callable[[ErrorContext], Coro[T]]],
        Callable[[ErrorContext], Coro[T]]
    ]:
        """Add a error handler called to handle errors.

        Error handlers are called in sequence with the first error handler
        called last. If an error handler raises an error, it will overwrite
        the current error that is being handled and then continue.

        Each error handler is called with a created instance of `ErrorContext`,
        which is mapping of relevant variables, until one returns `True`.

        Examples:

            ```python
            @app.error()
            async def handle_cooldown(context: ErrorContext) -> Optional[bool]:
                if not isinstance(context.error, CommandOnCooldown):
                    return None

                if 'interaction' not in context:
                    return False

                await context['interaction'].respond(f'Please try again later')
                return True
            ```

        Parameters:
            callback: The callback to be called; filled in by the decorator.

        Returns:
            A decorator which adds the handler. The callback is returned again
            afterwards.
        """
        def inner(
                func: Callable[[ErrorContext], Coro[T]]
        ) -> Callable[[ErrorContext], Coro[T]]:
            self._error_handlers.append(func)
            return func

        if callback is not None:
            return inner(callback)

        return inner


class CommandSetupError(Exception):
    """Raised when local command setup does not align with interactions.

    Examples of this is incorrect types of local options compared to what
    Discord sends, or subcommand-groups not receiving subcommands.
    """
    pass
