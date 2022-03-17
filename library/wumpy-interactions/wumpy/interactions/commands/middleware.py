from typing import Callable, TypeVar
from functools import wraps, partial

from .base import CommandCallback, MiddlewareCallback
from ..models import CommandInteraction

__all__ = ('MiddlewareDecorator', 'CheckFailure', 'check')


CommandT = TypeVar('CommandT', bound=CommandCallback)
MiddlewareDecorator = Callable[[CommandT], CommandT]


class CheckFailure(Exception):
    """Raised when a check for an application command fails.

    Checks are encouraged to raise their own subclass of this exception, but it
    will automatically be raised if the check only returned a falsely value.
    """
    pass


class CheckMiddleware:
    call_next: MiddlewareCallback
    predicate: MiddlewareCallback

    __slots__ = ('call_next', 'predicate')

    def __init__(
        self,
        call_next: MiddlewareCallback,
        *,
        predicate: MiddlewareCallback
    ) -> None:
        self.call_next = call_next

        self.predicate = predicate

    async def __call__(self, interaction: CommandInteraction) -> None:
        if await self.predicate(interaction):
            await self.call_next(interaction)
        else:
            raise CheckFailure(f'Check {self.predicate} failed for interaction {interaction}')


def check(predicate: MiddlewareCallback) -> MiddlewareDecorator:
    """Create a check for an application command.

    This is a public wrapper over the middleware API to simplify creating
    checks.

    Examples:

        ```python
        from wumpy import interactions
        from wumpy.interactions import InteractionApp, MiddlewareDecorator, CommandInteraction


        # MiddlewareDecorator is a type alias to make the return type easier to
        # annotate and use.
        def on_version(v: int) -> MiddlewareDecorator:
            async def predicate(interaction: CommandInteraction) -> bool:
                return interaction.version == v
            return interactions.check(predicate)


        app = InteractionApp(...)


        @on_version(1)
        @app.command()
        async def ping(interaction: CommandInteraction) -> None:
            \"\"\"Pong!\"\"\"
            await interaction.respond('Pong!')
        ```

    Parameters:
        predicate: A callable that takes the interaction and returns a boolean.

    Returns:
        A decorator to apply to the application command.
    """
    @wraps(predicate)
    def wrapper(command: CommandT) -> CommandT:
        command.push_middleware(partial(CheckMiddleware, predicate=predicate))
        return command
    return wrapper
