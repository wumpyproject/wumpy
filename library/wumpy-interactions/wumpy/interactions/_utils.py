import functools
from typing import Any, Callable, Dict, Awaitable

import anyio

def _eval_annotations(obj: Callable) -> Dict[str, Any]:
    """Eval a callable's annotations.

    This is primarily a backport of Python 3.10's `get_annotations()`
    method implemented by Larry Hastings:
    https://github.com/python/cpython/commit/74613a46fc79cacc88d3eae4105b12691cd4ba20

    Parameters:
        obj: The received callable to evaluate

    Returns:
        A dictionary of parameter name to its annotation.
    """
    unwrapped = obj
    while True:
        if hasattr(unwrapped, '__wrapped__'):
            unwrapped = unwrapped.__wrapped__
            continue
        if isinstance(unwrapped, functools.partial):
            unwrapped = unwrapped.func
            continue
        break

    annotations = getattr(unwrapped, '__annotations__', None)
    eval_globals = getattr(unwrapped, '__globals__', None)

    if annotations is None or not annotations:
        return {}

    if not isinstance(annotations, dict):
        raise ValueError(f'{unwrapped!r}.__annotations__ is neither a dict nor None')

    try:
        return {
            key: value if not isinstance(value, str) else eval(value, eval_globals)
            for key, value in annotations.items()
        }
    except (NameError, SyntaxError) as e:
        raise ValueError(f'Could not evaluate the annotations of {unwrapped!r}') from e


async def _done_callback(
    func: Callable[[], Awaitable[Any]],
    callback: Callable[[], Any]
) -> None:
    await func()

    # It is a deliberate design decision to not use a try/finally block here,
    # we only want to call the callback if func() was successful.
    callback()


async def race(*functions: Callable[[], Awaitable[Any]]) -> None:
    """Race several coroutine functions against each other.

    This function will return when the first of the functions complete, by
    cancelling all other functions. This means that only functions that can
    properly handle cancellation should be used with this function.

    This code was copied from `wumpy.gateway`'s similar utils.

    Parameters:
        functions: The functions to race against each other.
    """
    if not functions:
        raise ValueError("race() missing at least 1 required positional argument")

    async with anyio.create_task_group() as tg:
        for func in functions:
            tg.start_soon(functools.partial(_done_callback, func, tg.cancel_scope.cancel))
