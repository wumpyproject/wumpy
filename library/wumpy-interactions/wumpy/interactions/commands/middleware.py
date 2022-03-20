from typing import Any, Awaitable, Callable, List, TypeVar

from wumpy.models import CommandInteractionOption

from ..models import CommandInteraction

__all__ = ('CommandMiddlewareMixin', 'MiddlewareCallback')


MiddlewareCallback = Callable[
    [CommandInteraction, List[CommandInteractionOption]],
    Awaitable[object]
]
MiddlewareCallbackT = TypeVar('MiddlewareCallbackT', bound=MiddlewareCallback)
Middleware = Callable[[MiddlewareCallback], MiddlewareCallback]


class CommandMiddlewareMixin:
    """Mixin for invoking a command with middleware."""

    _invoke_stack: MiddlewareCallback

    __slots__ = ('_invoke_stack',)

    def __init__(self, *args, **kwargs) -> None:
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
