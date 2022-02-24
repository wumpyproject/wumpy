from typing import TYPE_CHECKING

import pytest
from wumpy.rest import DictRatelimiter


if TYPE_CHECKING:
    from wumpy.testing.suites import RatelimiterSuite
else:
    __mod = pytest.importorskip(
        'wumpy.testing.suites', reason='Wumpy-testing is required for the ratelimiter tests'
    )
    RatelimiterSuite = __mod.RatelimiterSuite
    del __mod


class TestDictRatelimiter(RatelimiterSuite):
    def get_impl(self) -> DictRatelimiter:
        return DictRatelimiter()
