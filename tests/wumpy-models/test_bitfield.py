import pytest
from wumpy.models.flags import BaseFlags, BitMask
from wumpy.models.permissions import TriBitMask


class TestMagicMethods:
    def test_equality(self):
        flag, other = BaseFlags(0), BaseFlags(0)

        assert flag == 0
        assert flag == other
        assert not flag == 'a'

    def test_not_equality(self):
        flag, other = BaseFlags(0), BaseFlags(1)

        assert flag != 1
        assert flag != other
        assert flag != 'a'

    def test_convertable(self):
        flag = BaseFlags(123)

        assert int(flag) == 123
        assert float(flag) == 123.0

    def test_hashable(self):
        hash(BaseFlags(0))

    def test_bitwise_and(self):
        a, b = BaseFlags(0b1010), BaseFlags(0b0111)
        assert a & b == BaseFlags(0b0010)

        x, y = BaseFlags(0b0001), 0b1000
        assert x & y == BaseFlags(0b0000)

        with pytest.raises(TypeError):
            BaseFlags(0b1010) & 'a'

    def test_bitwise_xor(self):
        a, b = BaseFlags(0b1100), BaseFlags(0b0111)
        assert a ^ b == BaseFlags(0b1011)

        x, y = BaseFlags(0b1111), 0b1111
        assert x ^ y == BaseFlags(0b0000)

        with pytest.raises(TypeError):
            BaseFlags(0b1100) ^ 'a'

    def test_bitwise_or(self):
        a, b = BaseFlags(0b0001), BaseFlags(0b1000)
        assert a | b == BaseFlags(0b1001)

        x, y = BaseFlags(0b1000), 0b0010
        assert x | y == BaseFlags(0b1010)

        with pytest.raises(TypeError):
            BaseFlags(0b0000) | 'a'


class Flag(BaseFlags):
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

    def test_set_true(self):
        instance = Flag(0)
        instance.red = True

        assert instance == Flag(Flag.red)

    def test_set_false(self):
        instance = Flag(Flag.blue)
        instance.blue = False

        assert instance == Flag(0)

    def test_set_wrong(self):
        instance = Flag(0)

        with pytest.raises(TypeError):
            instance.red = 'red'


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

        print(instance.allow.value, GreenProfile.green)
        print('#' * 10, instance.allow & GreenProfile.green)

        assert instance.green
        assert not instance.orange

        assert instance.violet is None

    def test_instance_set(self):
        instance = GreenProfile(0, 0)

        instance.green = True
        assert instance.allow.green and not instance.deny.green

        instance.red = False
        assert not instance.allow.red and instance.deny.red

    def test_instance_set_none(self):
        instance = GreenProfile(0, GreenProfile.orange)

        instance.orange = None
        assert not instance.allow.orange and not instance.deny.orange

    def test_set_wrong(self):
        instance = GreenProfile(0, 0)

        with pytest.raises(TypeError):
            instance.green = 'green'
