import inspect
from functools import partial
from typing import Any, Dict, Optional, TypeVar

import anyio.abc
from typing_extensions import ParamSpec

from ...errors import CommandSetupError
from ...models import InteractionMember, InteractionUser
from ..base import CommandInteraction
from .base import Callback, CommandCallback
from .option import CommandType

__all__ = ('ContextMenuCommand', 'MessageCommand', 'UserCommand')


P = ParamSpec('P')
RT = TypeVar('RT')


class ContextMenuCommand(CommandCallback[P, RT]):
    """Discord context menu command that gets a user or message.

    Attributes:
        name: Name of the context menu command.
        argument:
            The parameter annotation on the callback. This is used by
            subclasses to get some more information about the type to use.
    """

    argument: Any

    def __init__(self, callback: Callback[P, RT], *, name: Optional[str] = None) -> None:
        super().__init__(callback, name=name)

        self.argument = None

    def _verify_annotation(self, annotation: Any) -> None:
        # The point of this method is to raise TypeErrors if something is wrong
        # about the annotation.
        raise NotImplementedError

    def _set_callback(self, function: Callback[P, RT]) -> None:
        super()._set_callback(function)

        if not inspect.iscoroutinefunction(function):
            raise TypeError("'callback' has to be a coroutine function")

        signature = inspect.signature(function)

        if len(signature.parameters) != 2:
            raise TypeError("'callback' has to have two parameters")

        for param in signature.parameters.values():
            if param.kind is param.kind.KEYWORD_ONLY:
                raise TypeError("The parameters of 'callback' cannot be keyword-only")

            if param.annotation is not param.empty:
                self._verify_annotation(param.annotation)

    def resolve_value(self, interaction: CommandInteraction) -> Optional[Any]:
        """Resolve the single value for the interaction.

        Parameters:
            interaction: The interaction to resolve a value from.

        Returns:
            The single value or None.
        """
        raise NotImplementedError()

    def handle_interaction(self, interaction: CommandInteraction, *, tg: anyio.abc.TaskGroup) -> None:
        """Handle the interaction and call the registered callback.

        If `resolve_value()` returns None the callback is not called.
        """
        value = self.resolve_value(interaction)
        if value is None or self.callback is None:
            return

        tg.start_soon(partial(self._call_wrapped, interaction, value))


class MessageCommand(ContextMenuCommand[P, RT]):
    """Message context menu command.

    Attributes:
        name: Name of the message command.
        argument:
            The parameter annotation on the callback. This isn't really used
            by MessageCommand.
    """

    def _verify_annotation(self, annotation: Any) -> None:
        ...  # TODO: Implement this once there is an InteractionMessage object

    def resolve_value(self, interaction: CommandInteraction) -> Any:
        """Resolve the message to pass to the callback.

        Parameters:
            interaction: The interaction to resolve a value from.

        Returns:
            The message resolved.
        """
        if not interaction.target_id:
            raise CommandSetupError('Message command did not receive target ID.')

        message = interaction.resolved.messages.get(interaction.target_id)

        assert message is not None, 'Discord did not send message data'

        return message

    def to_dict(self) -> Dict[str, Any]:
        """Turn the command into a dictionary to send to Discord."""
        return {**super().to_dict(), 'type': CommandType.message.value}


class UserCommand(ContextMenuCommand[P, RT]):
    """User or member context menu command.

    Attributes:
        name: Name of the user command.
        argument:
            The parameter annotation on the callback. This is used to figure
            out whether a member or user object should be passed.
    """

    def _verify_annotation(self, annotation: Any) -> None:
        if annotation in {CommandInteraction, InteractionUser, InteractionMember}:
            return

        raise TypeError(f"Invalid parameter annotation '{annotation}'")

    def resolve_value(self, interaction: CommandInteraction) -> Optional[Any]:
        """Resolve the user or member to pass to the callback.

        Parameters:
            interaction: The interaction to resolve a user or member from.

        Returns:
            A user or member object depending on what the `argument` attribute
            is set to. If the `argument` attribute is set to a member but
            Discord did not send member data this method will return None.
        """
        if not interaction.target_id:
            raise CommandSetupError('User command did not receive target ID.')

        # ContextMenuCommand saves the argument in preperation for real support
        # of differentiating between InteractionUser and InteractionMember
        if isinstance(self.argument, InteractionUser):
            target = interaction.resolved.users.get(interaction.target_id)
        elif isinstance(self.argument, InteractionMember):
            target = interaction.resolved.members.get(interaction.target_id)
        else:
            raise CommandSetupError("User command's second argument incorrectly annotated")

        return target

    def to_dict(self) -> Dict[str, Any]:
        """Turn the command into a dictionary to send to Discord."""
        return {**super().to_dict(), 'type': CommandType.user.value}
