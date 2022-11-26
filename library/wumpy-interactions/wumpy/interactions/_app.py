import json
import traceback
import re
from contextlib import AsyncExitStack
from contextvars import ContextVar
from types import TracebackType
from typing import (
    Any, AsyncContextManager, Awaitable, Callable, Dict, Optional, Tuple, Type,
    TypeVar, cast, overload, Union, Literal
)

from discord_typings import InteractionData
from typing_extensions import Self
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from wumpy.rest import HTTPXRequester
from wumpy.rest.endpoints import (
    ApplicationCommandEndpoints, InteractionEndpoints
)

from ._models import CommandInteraction, ComponentInteraction, ResponseCallback
from .commands import command_payload, CommandRegistrar, SubcommandGroup, CommandUnion, Command
from .components import ComponentHandler, ComponentCallback

__all__ = (
    'InteractionAppRequester',
    'InteractionApp',
    'get_app',
)


AppT = TypeVar('AppT', bound='InteractionApp')


# Use for the get_app() function below the class. Similar to the get_bot()
# function with the same usage.
_active_app: ContextVar['InteractionApp'] = ContextVar('_active_app')


class InteractionAppRequester(ApplicationCommandEndpoints, InteractionEndpoints, HTTPXRequester):
    """Requester with endpoints used by InteractionApp."""

    __slots__ = ()


class InteractionApp:
    """Interaction app for receiving interactions through webhooks."""

    api: InteractionAppRequester
    _verifier: VerifyKey

    application_id: Optional[int]
    _token: Optional[str]

    commands: CommandRegistrar
    components: ComponentHandler

    __slots__ = (
        'api', 'register_commands', 'application_id', '_verifier', '_token',
    )

    def __init__(
            self,
            public_key: str,
            *,
            application_id: Optional[int] = None,
            token: Optional[str] = None,
    ) -> None:
        super().__init__()

        self.api = InteractionAppRequester(token)
        self._verifier = VerifyKey(bytes.fromhex(public_key))

        self.application_id = application_id
        self._token = token

    async def __aenter__(self) -> Self:
        await self.api.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        return await self.api.__aexit__(exc_type, exc_val, exc_tb)

    def authenticate_request(
            self,
            signature: str,
            timestamp: Union[bytes, bytearray],
            body: Union[bytes, bytearray],
    ) -> bool:
        """Authenticate the origin of a request for interactions.

        The purpose of separating this from `process_interaction()` is
        because of the difference in parameters.

        Returns:
            A bool indicating whether it is safe to continue. If this function
            returns `False`, a 401 Unauthorized response code should be
            retuned by the API.
        """
        try:
            self._verifier.verify(timestamp + body, signature=bytes.fromhex(signature))
            return True
        except BadSignatureError:
            return False

    async def process_interaction(self, data: InteractionData, response: ResponseCallback) -> None:
        """Process the interaction from the request by calling callbacks.

        This method returns once all callbacks have finished executing.

        Examples:

            ```python
            from sanic import Blueprint, Request
            from wumpy.interactions import (
                InteractionApp, SanicMiddleware, SanicRequest
            )

            app = InteractionApp(...)
            bp = Blueprint(...)

            verification = SanicMiddleware(...)

            # It is recommended to attach this to a specific blueprint with the
            # route that interactions should go to.
            bp.on_request(verification.verify)

            @bp.route('/interactions')
            async def interactions(request: Request):
                await app.process_interaction(
                    request.json,
                    SanicRequest(request)
                )
            ```

        Parameters:
            data: JSON serialized data received from the request.
            response:
                Response callback which will respond to the original request.
                This can be a callable class or a closure which wraps the
                original request since it is not kept around by the library.
        """
        if data['type'] == 1:  # Ping
            await response({'type': 1}, [])  # Pong

        if data['type'] == 2:
            await self.commands.invoke(
                CommandInteraction.from_data(data, response)
            )
        elif data['type'] == 3:
            await self.components.invoke(
                ComponentInteraction.from_data(data, response),
            )

    # Decorators for registering handlers

    def group(
        self,
        name: str,
        description: str
    ) -> SubcommandGroup:
        """Register and create a slash command group without a callback.

        This is similar to `interactions.group()`, except that it automatically
        registers the command at the same time.

        Parameters:
            name: The name of the command.
            description: The description of the command.

        Returns:
            A registered subcommand group.
        """
        command = SubcommandGroup(name=name, description=description)
        self.add_command(command)  # type: ignore
        return command

    @overload
    def command(
        self,
        type: Callback[P, RT]
    ) -> Command[P, RT]:
        ...

    @overload
    def command(
        self,
        type: CommandType = CommandType.chat_input,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], Command[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.message],
        *,
        name: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], MessageCommand[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.user],
        *,
        name: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], UserCommand[P, RT]]:
        ...

    def command(
        self,
        type: Union[CommandType, Callback[P, RT]] = CommandType.chat_input,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Union[CommandUnion[P, RT], Callable[[Callback[P, RT]], CommandUnion[P, RT]]]:
        """Register and create a new application command through a decorator.

        This is similar to the `@interactions.command()` decorator, except that
        it automatically registers the command at the same time.

        Parameters:
            type: The type of the command. Defaults to a slash command.
            name: The name of the command.
            description: The description of the command.

        Returns:
            A command or function that returns a command. Depending on whether
            the decorator was used with or without parentheses.

        Exceptions:
            ValueError: The type wasn't a CommandType value
        """
        def decorator(func: Callback[P, RT]) -> CommandUnion[P, RT]:
            if type is CommandType.chat_input:
                command = Command(func, name=name, description=description)
            elif type is CommandType.message:
                command = MessageCommand(func, name=name)
            elif type is CommandType.user:
                command = UserCommand(func, name=name)
            else:
                raise ValueError("Unknown value of 'type':", type)

            self.add_command(command)  # type: ignore
            return command

        if callable(type):
            return decorator(type)

        return decorator

    def component(
            self,
            pattern: Union[str, 're.Pattern[str]']
    ) -> Callable[[ComponentCallback], ComponentCallback]:
        """Add a callback to be dispatched when the custom ID is matched.

        Examples:

            ```python
            @app.component(r'upvote-(?P<message_id>)')
            async def process_upvote(interaction: ComponentInteraction, match: re.Match):
                message_id = match.group('message_id')
                await interaction.reply(
                    f'You upvoted message {message_id}',
                    ephemeral=True
                )
            ```

        Parameters:
            pattern: The regex pattern to match custom IDs with.

        Returns:
            A decorator that adds the callback to the list of components.
        """
        def decorator(func: ComponentCallback) -> ComponentCallback:
            nonlocal pattern

            if isinstance(pattern, str):
                pattern = re.compile(pattern)

            self.components.add_component(pattern, func)
            return func
        return decorator

    async def sync_commands(self) -> None:
        """Synchronize the commands with Discord."""
        await self.api.overwrite_global_commands(
            self.application_id, [command_payload(c) for c in self._commands.values()]
        )


@overload
def get_app(*, verify: bool = False) -> InteractionApp:
    ...


@overload
def get_app(subclass: Type[AppT], *, verify: bool = False) -> AppT:
    ...


def get_app(subclass: Type[AppT] = InteractionApp, *, verify: bool = False) -> AppT:
    """Get the currently active interaction application.

    An interaction app is considered active once its' lifespan has been called.

    This allows indepent parts of the code to get access to the active
    application without imports and passing it around unnecessarily. Similar
    to `get_bot()` in the `wumpy-bot` subpackage.

    Parameters:
        subclass: The type of the return type for the type checker.
        verify: Whether to do an `isinstance()` check on the gotten instance.

    Raises:
        RuntimeError: There is no currently active app.
        RuntimeError: If `verify` is True, the `isinstance()` check failed

    Returns:
        The currently active app.
    """
    try:
        instance = _active_app.get()
    except LookupError:
        raise RuntimeError(
            'There is no currently active app; make sure lifespan is enabled'
        ) from None

    if verify and not isinstance(instance, subclass):
        raise RuntimeError(f'Currently active bot is not of type {subclass.__name__!r}')

    return cast(AppT, instance)
