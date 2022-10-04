from contextvars import ContextVar, Token
from types import TracebackType
from typing import Optional, Type

from typing_extensions import Self

from ._errors import RequestException

__all__ = (
    'RatelimiterContext',
    'abort_if_ratelimited',
)


_abort_if_ratelimited: ContextVar[bool] = ContextVar('_abort_if_ratelimited', default=False)


class RatelimiterContext:
    """Ratelimiting context variables for the request made.

    This class provides attributes which are gotten from underlying context
    variables at instantiation time. These context variables allow
    transparently configuring ratelimiting without adding a bunch of parameters
    to each request - nor having to change the signature of ratelimiters for
    every update.

    It is adviced that all ratelimiters implement all of these behaviours. If
    some configuration cannot be implemented the ratelimiter should raise an
    error to signal to the developer that this configuration cannot be used.

    An instance of this class can be safely passed to a different context
    without having attributes change, thus an instance of this represents the
    current state at a certain point in time.

    Examples:

        ```python
        ctx = RatelimiterContext()
        print(ctx.abort_if_ratelimited)
        ```

    Attributes:
        abort_if_ratelimited:
            Abort the request if it will hit ratelimits.

            This ratelimiting configuration is what powers the context manager
            of the same name (`abort_if_ratelimited()`). It allows the user to
            specify that they wish to abort requests if they get ratelimited.
    """

    abort_if_ratelimited: bool

    def __new__(cls) -> Self:
        self = super().__new__(cls)

        self.abort_if_ratelimited = _abort_if_ratelimited.get()

        return self


class _AbortRatelimitsManager:

    _aborted: Optional[bool]
    _previous: Token

    def __init__(self) -> None:
        self._aborted = None

    def __enter__(self) -> Self:
        self._previous = _abort_if_ratelimited.set(True)

        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]] = None,
            exc_val: Optional[BaseException] = None,
            traceback: Optional[TracebackType] = None
    ) -> Optional[bool]:
        _abort_if_ratelimited.reset(self._previous)

        if isinstance(exc_val, RequestException) and exc_val.status_code in {408, 429}:
            self._aborted = True
            return True

        self._aborted = False

    @property
    def aborted(self) -> bool:
        if self._aborted is None:
            raise RuntimeError(
                "Cannot access 'aborted' before 'abort_if_ratelimited()' has been exited"
            )

        return self._aborted


def abort_if_ratelimited() -> _AbortRatelimitsManager:
    """Abort requests if they are ratelimited.

    This function returns a context manager, that when entered, will abort any
    requests if they will be ratelimited. Useful for skipping somewhat
    pointless requests that you don't want to wait for.

    !!! info
        The global ratelimit of all requests is always abided. This function
        is for ignoring larger route-specific ratelimits.

    The way this is implemented is by catching the `Ratelimited` exception.
    That means that not all code inside of this context manager will run if the
    request gets ratelimited. Therefore, if you want to use the result of the
    request this code needs to be placed inside of the context manager.

    If you want to know whether the requests were aborted, you can check the
    `aborted` attribute on the context manager:

    ```python
    with abort_if_ratelimited() as abort_ratelimits:
        user = await api.fetch_user(344404945359077377)
        print(f"Found user {user['name']}#{user['discriminator]}")

    # Note that 'user' may or may not be defined here, depending on whether the
    # request was aborted or not. That's why we print inside of the context
    # manager.

    if abort_ratelimits.aborted:
        # Since the request was aborted, the above print did not get to run
        print('Skipped fetching because of ratelimits')
    ```

    For more complex situations, you can also nest this to only abort subset of
    requests at a time. This allows you to compose requests that get aborted on
    their own without aborting all requests inside of the parent.

    !!! note
        This function does not skip the ratelimiter, rather, it aborts the
        request *if* the ratelimiter wants to wait. You cannot use this to
        force requests to bypass the ratelimiter.

    Returns:
        A context manager which skips requests if they will be ratelimited.
    """
    return _AbortRatelimitsManager()
