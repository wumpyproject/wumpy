from functools import partial
from typing import Any, Awaitable, Callable, Generic, List, Type, TypeVar

from wumpy.models import CommandInteractionOption

from .._models import CommandInteraction

__all__ = (
    'MiddlewareCallback',
    'CommandMiddlewareMixin',
)


ET = TypeVar('ET', bound='Exception')
ErrorHandler = Callable[[CommandInteraction, ET], Awaitable[object]]


MiddlewareCallback = Callable[
    [CommandInteraction, List[CommandInteractionOption]],
    Awaitable[object]
]
MiddlewareCallbackT = TypeVar('MiddlewareCallbackT', bound=MiddlewareCallback)


class CommandMiddlewareMixin:
    """Mixin for invoking a command with middleware."""

    _invoke_stack: MiddlewareCallback

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._invoke_stack = self._inner_call

    async def _inner_call(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        raise NotImplementedError()

    async def invoke(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> Any:
        """Invoke the command with the given interaction and options.

        Compared to directly calling the command, this will invoke
        middlewares in order, such that checks and cooldowns are executed.

        Parameters:
            interaction: The interaction to invoke the command with.
            options: The options for the command to invoke.
        """
        return await self._invoke_stack(interaction, options)

    def push_middleware(
        self,
        middleware: Callable[[MiddlewareCallback], MiddlewareCallbackT]
    ) -> MiddlewareCallbackT:
        """Push a middleware to the stack.

        Middlewares are a lowlevel functionality that allows heavily extensible
        behaviour in how commands are invoked. They are essentially before
        / after hooks for the command.

        If you need to pass other options to the middleware, use `partial()`
        from `functools`.

        Parameters:
            middleware:
                A callable that takes the next middleware to invoke when the
                callable it returns is called with the interaction and options.

        Returns:
            The returned callback of the middleware. This is the object that
            is returned when `middleware` is called.
        """
        called = middleware(self._invoke_stack)
        self._invoke_stack = called
        return called

    def error(self, error: Type[ET]) -> Callable[[ErrorHandler[ET]], 'ErrorMiddleware[ET]']:
        """Register an error handler for the given error type.

        This is a simplification over adding a middleware that wraps the next
        middleware with a `try`/`except` block.

        Parameters:
            error: The type of error to handle.

        Returns:
            A decorator that takes the handler callback to use and pushes the
            final middleware to the stack.
        """
        def decorator(handler: ErrorHandler[ET]) -> 'ErrorMiddleware[ET]':
            return self.push_middleware(partial(ErrorMiddleware, error=error, handler=handler))
        return decorator


class ErrorMiddleware(Generic[ET]):
    call_next: MiddlewareCallback

    error: Type[ET]
    handler: ErrorHandler[ET]

    __slots__ = ('call_next', 'error', 'handler')

    def __init__(
        self,
        call_next: MiddlewareCallback,
        *,
        error: Type[ET],
        handler: Callable[[CommandInteraction, ET], Awaitable[object]]
    ) -> None:
        self.call_next = call_next

        self.error = error
        self.handler = handler

    async def __call__(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        try:
            await self.call_next(interaction, options)
        except self.error as error:
            await self.handler(interaction, error)
