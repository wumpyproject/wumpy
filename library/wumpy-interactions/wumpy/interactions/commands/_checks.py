from functools import wraps
from typing import Awaitable, Callable, TypeVar, cast
from typing_extensions import ParamSpec

from .._models import CommandInteraction

__all__ = (
    'middleware',
    'CheckFailure',
    'check',
)


P = ParamSpec('P')
RT = TypeVar('RT')


def middleware(
        func: Callable[[CommandInteraction], Awaitable[object]],
) -> Callable[[Callable[P, Awaitable[RT]]], Callable[P, Awaitable[RT]]]:
    """Helper-decorator to apply a function to wrap a callback.

    The benefit of using this over a custom decorator is that it does not
    interfere with the command decorator.

    Parameters:
        func:
            Function to call before the final callback, which takes the
            interaction. The return type is ignored.

    Returns:
        A decorator which wraps the command callback.
    """
    def middleware_decorator(
            callback: Callable[P, Awaitable[RT]]
    ) -> Callable[P, Awaitable[RT]]:
        @wraps(callback)
        async def callback_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            await func(cast(CommandInteraction, args[0]))
            return await callback(*args, **kwargs)
        return callback_wrapper
    return middleware_decorator


class CheckFailure(Exception):
    """Raised when a check for an application command fails.

    Checks are encouraged to raise their own subclass of this exception, but it
    will automatically be raised if the check only returned a falsely value.
    """

    interaction: CommandInteraction
    predicate: Callable[[CommandInteraction], Awaitable[bool]]

    def __init__(
            self,
            interaction: CommandInteraction,
            predicate: Callable[[CommandInteraction], Awaitable[bool]]
    ) -> None:
        super().__init__(f'Check {self.predicate} failed for interaction {interaction}')

        self.interaction = interaction
        self.predicate = predicate


def check(
        predicate: Callable[[CommandInteraction], Awaitable[bool]],
) -> Callable[[Callable[P, Awaitable[RT]]], Callable[P, Awaitable[RT]]]:
    """Create a check for an application command.

    This is a helper decorator which only executes the command if the passed
    predicate returns a truthy value. The benefit of using this over a custom
    decorator is that it does not interfere with the command decorator.

    Examples:

        ```python
        from typing import Callable

        from wumpy import interactions
        from wumpy.interactions import InteractionApp, CommandInteraction


        async def on_version(v: int) -> Callable[[CommandInteraction], bool]:
            async def predicate(interaction: CommandInteraction) -> bool:
                return interaction.version == v
            return predicate


        app = InteractionApp(...)


        @app.command()
        @interactions.check(on_version(1))
        async def ping(interaction: CommandInteraction) -> None:
            \"\"\"Pong!\"\"\"
            await interaction.respond('Pong!')
        ```

    Parameters:
        predicate: A callable that takes the interaction and returns a boolean.

    Returns:
        A decorator to apply to the application command.
    """
    # While these functions are usually named 'decorator' and 'inner' or
    # 'wrapper', by using more descriptive names their repr:s (which show up
    # when printed) become more useful when debugging
    def check_decorator(callback: Callable[P, Awaitable[RT]]) -> Callable[P, Awaitable[RT]]:
        @wraps(callback)
        async def check_command_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            inter = cast(CommandInteraction, args[0])

            if await predicate(inter) is False:
                raise CheckFailure(inter, predicate)

            return await callback(*args, **kwargs)
        return check_command_wrapper
    return check_decorator
