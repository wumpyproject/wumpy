from typing import Any, Awaitable, Callable, Generic, TypeVar

from typing_extensions import ParamSpec
from wumpy.models import CommandInteraction

__all__ = ('Middleware', 'SlashCommand',)


P = ParamSpec('P')
RT = TypeVar('RT')
MiddlewareCallback = Callable[[CommandInteraction], Awaitable[object]]
Middleware = Callable[[MiddlewareCallback], MiddlewareCallback]


class SlashCommand(Generic[P, RT]):
    """Top-level slashcommand callback.

    Currently subcommand groups and subcommands are not supported.
    """

    def __init__(self, callback: Callable[P, Awaitable[RT]]) -> None:
        self.callback = callback

        self._invoke_stack = self._inner_call

    async def __call__(self, *args: P.args, **kwds: P.kwargs) -> RT:
        return await self.callback(*args, **kwds)

    async def _inner_call(self, interaction: CommandInteraction) -> RT:
        # invoke() calls the callstack of middlewares. This is the
        # bottom-most middleware that, if all other middlewares successfully
        # call the next, will call the command callback.
        return await self.callback(interaction)

    async def invoke(self, interaction: CommandInteraction) -> Any:
        """Invoke the command with the given interaction.

        Compared to directly calling the subcommand, this will invoke
        middlewares in order, such that checks and cooldowns are executed.

        Parameters:
            interaction: The interaction to invoke the command with.
        """
        return await self._invoke_stack(interaction)

    def push_middleware(self, middleware: Middleware) -> None:
        """Push a middleware to the stack.

        Middlewares are a lowlevel functionality that allows heavily extensible
        behaviour in how commands are invoked. They are essentially before
        / after hooks for the command.

        If you need to pass other options to the middleware, use `partial()`
        from `functools`.

        Parameters:
            middleware:
                An instance of the `Middleware` namedtuple with a callback and
                dictionary of options to pass it when calling it.
        """
        self._invoke_stack = middleware(self._invoke_stack)
