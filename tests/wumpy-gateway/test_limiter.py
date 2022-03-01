import sys
from time import perf_counter
from typing import NoReturn
from unittest import mock

import pytest
from discord_gateway import Opcode
from wumpy.gateway.utils import DefaultGatewayLimiter


class SimplerGatewayLimiter(DefaultGatewayLimiter):
    RATE = 3
    PER = 10


class TestGatewayLimiter:
    @pytest.mark.anyio
    async def test_bypass(self) -> None:
        async def sleep(duration: float) -> NoReturn:
            raise RuntimeError("'sleep()' should not have been called")

        async with SimplerGatewayLimiter() as limiter:
            with mock.patch('anyio.sleep', sleep):
                for _ in range(SimplerGatewayLimiter.RATE + 1):
                    async with limiter(Opcode.HEARTBEAT):
                        pass

    @pytest.mark.anyio
    @pytest.mark.skipif(sys.version_info < (3, 8), reason='AsyncMock requires Python 3.8+')
    async def test_wait(self) -> None:
        slept = mock.AsyncMock()

        async with SimplerGatewayLimiter() as limiter:
            with mock.patch('anyio.sleep', slept):
                for _ in range(SimplerGatewayLimiter.RATE + 1):
                    async with limiter(Opcode.PRESENCE_UPDATE):
                        pass

                assert slept.call_count == 1

    @pytest.mark.anyio
    async def test_time_passed(self) -> None:
        async def sleep(duration: float) -> NoReturn:
            raise RuntimeError("'sleep()' should not have been called")

        time = perf_counter()

        def patched():
            return time + SimplerGatewayLimiter.PER * 1.1

        async with SimplerGatewayLimiter() as limiter:
            for _ in range(SimplerGatewayLimiter.RATE):
                async with limiter(Opcode.PRESENCE_UPDATE):
                    pass

            with mock.patch('time.perf_counter', patched), mock.patch('anyio.sleep', sleep):
                async with limiter(Opcode.PRESENCE_UPDATE):
                    pass
