from typing import (
    Any, Awaitable, Callable, Dict, Generic, NamedTuple, TypeVar
)

from typing_extensions import ParamSpec
from wumpy.models import (
    CommandInteraction
)

__all__ = ('Middleware', 'SlashCommand',)


P = ParamSpec('P')
RT = TypeVar('RT')


class Middleware(NamedTuple):
    cls: Callable[..., Callable[[CommandInteraction], Awaitable[object]]]
    options: Dict[str, object]


class SlashCommand(Generic[P, RT]):
    """Top-level slashcommand callback.

    Currently subcommand groups and subcommands are not supported.
    """

    def __init__(self, callback: Callable[P, Awaitable[RT]]) -> None:
        self.callback = callback

        self.callstack = self._inner_call
        self.middlewares = []

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
        return await self.callstack(interaction)

    def _build_callstack(self) -> None:
        prev = self._inner_call
        for cls, options in self.middlewares:
            prev = cls(prev, **options)

        self.callstack = prev

    def add_middleware(self, middleware: Middleware) -> None:
        """Add a middleware to the stack.

        Middlewares are a lowlevel functionality that allows heavily extensible
        behaviour in how commands are invoked. Essentially middlewares are
        before/after hooks for the command.

        Parameters:
            middleware:
                An instance of the `Middleware` namedtuple with a callback and
                dictionary of options to pass it when calling it.
        """
        self.middlewares.append(middleware)
        self._build_callstack()
