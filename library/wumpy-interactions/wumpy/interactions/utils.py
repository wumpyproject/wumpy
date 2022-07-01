import functools
from typing import Any, Callable, Dict, Optional, Union

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from wumpy.rest import MISSING

__all__ = ('DiscordRequestVerifier', 'MISSING')


class DiscordRequestVerifier:
    """Thin wrapper over PyNaCl's Ed25519 verifier.

    This is designed to verify Discord interactions requests. See the
    documentation for middlewares for specific libraries wrapping this class.
    """

    def __init__(self, public_key: str) -> None:
        self._verifier = VerifyKey(bytes.fromhex(public_key))

    def verify(
        self,
        signature: str,
        timestamp: Union[str, bytes],
        body: Union[str, bytes, bytearray]
    ) -> bool:
        """Verify the signature of a request.

        Parameters:
            signature: The `X-Signature-Ed25519` header signature.
            timestamp: The `X-Signature-Timestamp` header value.
            body:
                The request body data. This can be either a string, bytes or
                bytearray (although they are all converted into `bytes`).

        Returns:
            Whether the signature is valid. If this returns `False` you should
            respond with a 401 Unauthorized.
        """
        if isinstance(timestamp, str):
            timestamp = timestamp.encode('utf-8')

        if isinstance(body, str):
            body = body.encode('utf-8')

        message = bytes(timestamp + body)

        try:
            self._verifier.verify(message, signature=bytes.fromhex(signature))
            return True
        except BadSignatureError:
            return False


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


class State:
    """An object which allows setting arbitrary attributes."""

    __state: Dict[str, Any]

    __slots__ = ('__state',)

    def __init__(self, state: Optional[Dict[str, Any]] = None) -> None:
        super().__setattr__('__state', state.copy() if state is not None else {})

    def __setattr__(self, key: str, value: Any) -> None:
        self.__state[key] = value

    def __getattr__(self, key: str) -> Any:
        try:
            return self.__state[key]
        except KeyError:
            raise AttributeError(
                f'{self.__class__.__name__!r} object has no attribute {key!r}'
            ) from None

    def __delattr__(self, key: str) -> None:
        try:
            del self.__state[key]
        except KeyError:
            raise AttributeError(key) from None
