from wumpy.rest import DictRatelimiter
from wumpy.testing.suites import RatelimiterSuite


class TestDictRatelimiter(RatelimiterSuite):
    def get_impl(self) -> DictRatelimiter:
        return DictRatelimiter()
