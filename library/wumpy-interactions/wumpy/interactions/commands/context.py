import inspect
from asyncio import iscoroutinefunction
from typing import Any, List, Optional, TypeVar

from typing_extensions import ParamSpec
from wumpy.models import (
    CommandInteractionOption, InteractionMember, Message, User
)

from ..errors import CommandSetupError
from ..models import CommandInteraction
from .base import Callback, CommandCallback

__all__ = ('ContextMenuCommand', 'MessageCommand', 'UserCommand')


P = ParamSpec('P')
RT = TypeVar('RT')


class ContextMenuCommand(CommandCallback[P, RT]):
    """Discord context menu command that gets a user or message.

    Attributes:
        name: Name of the context menu command.
    """

    def __init__(self, callback: Callback[P, RT], *, name: Optional[str] = None) -> None:
        self.name = name

        super().__init__(callback)

    def _verify_annotation(self, annotation: Any) -> None:
        # The point of this method is to raise TypeErrors if something is wrong
        # about the annotation.
        raise NotImplementedError

    def _process_callback(self, callback: Callback[P, RT]) -> None:
        if self.name is None:
            self.name = getattr(callback, '__name__', None)

        if not iscoroutinefunction(callback):
            raise TypeError("'callback' must be an 'async def' function")

        return super()._process_callback(callback)

    def _process_param(self, index: int, param: inspect.Parameter) -> None:
        """Process a parameter of the set callback.

        This method is called for each parameter of the callback when being
        set, allowing for subclasses to hook into the process.

        Parameters:
            index: The index of the parameter.
            param:
                The parameter of the callback. Annotations have been resolved
                and replaced with the actual type.
        """
        if index > 1:
            raise TypeError("'callback' has to have two parameters")

        if param.kind is param.kind.KEYWORD_ONLY:
            raise TypeError("The parameters of 'callback' cannot be keyword-only")

        if param.annotation is param.empty:
            return  # The following code only inspects annotations

        if index == 0:
            if (
                not isinstance(param.annotation, type)
                or not issubclass(param.annotation, CommandInteraction)
            ):
                raise TypeError(
                    "The annotation of the first parameter must be a 'CommandInteraction'"
                )
        else:
            self._verify_annotation(param.annotation)

    def _process_no_params(self, signature: inspect.Signature) -> None:
        raise TypeError("'callback' has to have two parameters")

    def resolve_value(self, interaction: CommandInteraction) -> Optional[Any]:
        """Resolve the single value for the interaction.

        Parameters:
            interaction: The interaction to resolve a value from.

        Returns:
            The single value or None.
        """
        raise NotImplementedError()

    async def _inner_call(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        value = self.resolve_value(interaction)
        if value is None:
            return

        await self.callback(interaction, value)  # type: ignore


class MessageCommand(ContextMenuCommand[P, RT]):
    """Message context menu command.

    Attributes:
        name: Name of the message command.
    """

    def _verify_annotation(self, annotation: Any) -> None:
        if annotation in {CommandInteraction, Message}:
            return

        raise TypeError(f"Invalid parameter annotation '{annotation}'")

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
        if message is None:
            raise RuntimeError('Discord did not send message data for message command')

        return message


class UserCommand(ContextMenuCommand[P, RT]):
    """User or member context menu command.

    Attributes:
        name: Name of the user command.
    """

    _annotation: Optional[Any]

    def __init__(self, callback: Callback[P, RT], *, name: Optional[str] = None) -> None:
        super().__init__(callback, name=name)

        self._annotation = None

    def _verify_annotation(self, annotation: Any) -> None:
        if annotation not in {User, InteractionMember}:
            raise TypeError(f"Invalid parameter annotation '{annotation}'")

        self._annotation = annotation

    def resolve_value(self, interaction: CommandInteraction) -> Optional[Any]:
        """Resolve the user or member to pass to the callback.

        Parameters:
            interaction: The interaction to resolve a user or member from.

        Returns:
            A user or member object depending on the annotation of the
            callback the user command was created with.
        """
        if not interaction.target_id:
            raise CommandSetupError('User command did not receive target ID.')

        if isinstance(self._annotation, User):
            target = interaction.resolved.users.get(interaction.target_id)
        else:
            # self._annotation is InteractionMember
            target = interaction.resolved.members.get(interaction.target_id)

        return target
