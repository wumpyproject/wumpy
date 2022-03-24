import inspect
from functools import update_wrapper
from typing import Any, Awaitable, Callable, Generic, TypeVar

from typing_extensions import ParamSpec

from ..utils import _eval_annotations

__all__ = ('CommandCallback',)


P = ParamSpec('P')
RT = TypeVar('RT')


Callback = Callable[P, Awaitable[RT]]


class CommandCallback(Generic[P, RT]):
    """Asynchronous command callback wrapped in middleware."""

    _callback: Callback[P, RT]

    def __init__(self, callback: Callback[P, RT]) -> None:
        super().__init__()

        self.callback = callback

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RT:
        return await self.callback(*args, **kwargs)

    @property
    def callback(self) -> Callback[P, RT]:
        if self._callback is None:
            raise AttributeError(f"{self.__class__.__name__!r} has no currently set callback")

        return self._callback

    @callback.setter
    def callback(self, function: Callback[P, RT]) -> None:
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
        update_wrapper(self, callback)

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
