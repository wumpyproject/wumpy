"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from types import TracebackType
from typing import Optional, Type

import anyio

__all__ = ('RateLimit',)


class RateLimit(anyio.Lock):
    """An API rate limit lock and default implementation of the Lock protocol."""

    deferred: bool

    event: anyio.Event

    def __init__(self, event: anyio.Event) -> None:
        self.deferred = False
        self.event = event

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        if not self.deferred:
            self.release()

    def defer(self) -> None:
        """Defer the lock from releasing during the next __aexit__.

        This is used to release the lock later on, while still exiting.
        """
        self.deferred = True

    def acquire_nowait(self) -> None:
        """Acquire the lock, without blocking."""
        self.deferred = False  # Reset the value

        return super().acquire_nowait()
