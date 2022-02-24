from typing import Union

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

__all__ = ('DiscordRequestVerifier',)


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
