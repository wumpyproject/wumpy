import inspect
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

from typing_extensions import ParamSpec

from ..models import CommandInteraction
from ..utils import _eval_annotations

__all__ = ('CommandCallback',)


P = ParamSpec('P')
RT = TypeVar('RT')


Callback = Callable[P, Awaitable[RT]]
MiddlewareCallback = Callable[[CommandInteraction], Awaitable[object]]
MiddlewareCallbackT = TypeVar('MiddlewareCallbackT', bound=MiddlewareCallback)
Middleware = Callable[[MiddlewareCallback], MiddlewareCallback]


class CommandCallback(Generic[P, RT]):
    """Asynchronous command callback wrapped in middleware."""

    _invoke_stack: MiddlewareCallback

    # The reason this is Optional[...] is because slash commands can have
    # subcommand groups and subcommands which means the slash command itself
    # cannot be called meaning that they have no callback.
    _callback: Optional[Callback[P, RT]]

    __slots__ = ('_invoke_stack', '_callback')

    def __init__(self, callback: Optional[Callback[P, RT]] = None) -> None:
        self._invoke_stack = self._inner_call

        self.callback = callback

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RT:
        return await self.callback(*args, **kwargs)

    @property
    def callback(self) -> Callback[P, RT]:
        if self._callback is None:
            raise AttributeError(f"{self.__class__.__name__!r} has no currently set callback")

        return self._callback

    @callback.setter
    def callback(self, function: Optional[Callback[P, RT]]) -> None:
        if function is None:
            self._callback = function
            return

        self._callback = function
        self._process_callback(function)

    def _process_callback(self, callback: Callback[P, RT]) -> None:
        """Process a callback being set.

        This is called first out of all available methods and is used to call
        the other methods by default. If this method is overriden it is
        important to call the super method.

        Parameters:
            callback: The callback being set.
        """
        signature = inspect.signature(callback)
        annotations = _eval_annotations(callback)

        for i, param in enumerate(signature.parameters.values()):
            annotation = annotations.get(param.name, param.empty)

            self._process_param(i, param.replace(annotation=annotation))

        # We piggyback on inspect's Parameter.empty sentinel value
        return_type = annotations.get('return', inspect.Parameter.empty)

        if return_type is not inspect.Parameter.empty:
            self._process_return_type(return_type)

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
        ...

    def _process_return_type(self, annotation: Any) -> None:
        """Process the extracted return type of the callback.

        This is only called if the callback is a return type.

        Parameters:
            annotation: The annotation of the function's return type.
        """
        ...

    async def _inner_call(self, interaction: CommandInteraction) -> None:
        await self.callback(interaction)

    async def invoke(self, interaction: CommandInteraction) -> None:
        """Invoke the command callback with the given interaction.

        Compared to directly calling the subcommand, this will invoke
        middlewares in order, such that checks and cooldowns are executed.

        Parameters:
            interaction: The interaction to invoke the command with.
        """
        if self.callback is None:
            raise AttributeError("'callback' is not set to a function")

        await self._invoke_stack(interaction)

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
                An instance of the `Middleware` namedtuple with a callback and
                dictionary of options to pass it when calling it.

        Returns:
            The returned callback of the middleware. This is the object that
            is returned when `middleware` is called.
        """
        called = middleware(self._invoke_stack)
        self._invoke_stack = called
        return called
