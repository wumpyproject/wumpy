import dataclasses
from typing import Callable, TypeVar
from functools import wraps, partial

from .base import CommandCallback, MiddlewareCallback
from ..models import CommandInteraction

__all__ = ('CheckDecorator', 'CheckFailure', 'check')


CommandT = TypeVar('CommandT', bound=CommandCallback)
CheckDecorator = Callable[[CommandT], CommandT]


class CheckFailure(Exception):
    """Raised when a check for an application command fails.

    Checks are encouraged to raise their own subclass of this exception, but it
    will automatically be raised if the check only returned a falsely value.
    """
    pass


@dataclasses.dataclass(frozen=True)
class Check:
    call_next: MiddlewareCallback
    predicate: MiddlewareCallback

    async def __call__(self, interaction: CommandInteraction) -> None:
        if await self.predicate(interaction):
            await self.call_next(interaction)
        else:
            raise CheckFailure(f'Check {self.predicate} failed for interaction {interaction}')


def check(predicate: MiddlewareCallback) -> CheckDecorator:
    """Create a check for an application command.

    This is a public wrapper over the middleware API to simplify creating
    checks.

    Examples:

        ```python
        from wumpy import interactions
        from wumpy.interactions import InteractionApp, CheckDecorator, CommandInteraction

        def in_guild():
            async def predicate(interaction: CommandInteraction) -> bool:
                return interaction.guild_id is not None
            return interactions.check(predicate)


        app = InteractionApp(...)


        @in_guild()
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
        command.push_middleware(partial(Check, predicate=predicate))
        return command
    return wrapper
