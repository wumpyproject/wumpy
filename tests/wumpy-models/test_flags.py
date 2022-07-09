import pytest
from wumpy.models._flags import BitMask, DiscordFlags
from wumpy.models._permissions import TriBitMask


class TestMagicMethods:
    def test_equality(self):
        flag, other = DiscordFlags(0), DiscordFlags(0)

        assert flag == 0
        assert flag == other
        assert not flag == 'a'

    def test_not_equality(self):
        flag, other = DiscordFlags(0), DiscordFlags(1)

        assert flag != 1
        assert flag != other
        assert flag != 'a'

    def test_convertable(self):
        flag = DiscordFlags(123)

        assert int(flag) == 123
        assert float(flag) == 123.0

    def test_hashable(self):
        assert hash(DiscordFlags(0)) == hash(DiscordFlags(0))
        assert hash(DiscordFlags(123)) != hash(DiscordFlags(321))

    def test_bitwise_and(self):
        a, b = DiscordFlags(0b1010), DiscordFlags(0b0111)
        assert a & b == DiscordFlags(0b0010)

        x, y = DiscordFlags(0b0001), 0b1000
        assert x & y == DiscordFlags(0b0000)

        with pytest.raises(TypeError):
            DiscordFlags(0b1010) & 'a'

    def test_bitwise_xor(self):
        a, b = DiscordFlags(0b1100), DiscordFlags(0b0111)
        assert a ^ b == DiscordFlags(0b1011)

        x, y = DiscordFlags(0b1111), 0b1111
        assert x ^ y == DiscordFlags(0b0000)

        with pytest.raises(TypeError):
            DiscordFlags(0b1100) ^ 'a'

    def test_bitwise_or(self):
        a, b = DiscordFlags(0b0001), DiscordFlags(0b1000)
        assert a | b == DiscordFlags(0b1001)

        x, y = DiscordFlags(0b1000), 0b0010
        assert x | y == DiscordFlags(0b1010)

        with pytest.raises(TypeError):
            DiscordFlags(0b0000) | 'a'


class Flag(DiscordFlags):
    red = BitMask(1 << 0)
    orange = BitMask(1 << 1)
    yellow = BitMask(1 << 2)
    green = BitMask(1 << 3)
    blue = BitMask(1 << 4)
    indigo = BitMask(1 << 5)
    violet = BitMask(1 << 6)


class TestBitMask:
    def test_type_get(self):
        assert Flag.yellow == 1 << 2
        assert Flag.blue == 1 << 4

    def test_instance_get(self):
        instance = Flag(Flag.red | Flag.blue)

        assert instance.red
        assert instance.blue


class GreenProfile:
    # Colour combinations that green can be with in a flag
    def __init__(self, allow: int, deny: int) -> None:
        self.allow = Flag(allow)
        self.deny = Flag(deny)

    red = TriBitMask(1 << 0)
    orange = TriBitMask(1 << 1)
    yellow = TriBitMask(1 << 2)
    green = TriBitMask(1 << 3)
    blue = TriBitMask(1 << 4)
    indigo = TriBitMask(1 << 5)
    violet = TriBitMask(1 << 6)


class TestTriBitMask:
    def test_type_get(self):
        assert GreenProfile.green == 1 << 3
        assert GreenProfile.blue == 1 << 4

    def test_instance_get(self):
        instance = GreenProfile(
            GreenProfile.green | GreenProfile.blue,
            GreenProfile.red | GreenProfile.orange
        )

        assert instance.green
        assert not instance.orange

        assert instance.violet is None
