from datetime import datetime, timezone

from wumpy.models import Model, Snowflake


def test_instantiation() -> None:
    model = Model(344404945359077377)
    assert model.id == 344404945359077377


def test_hashable() -> None:
    d = {Model(344404945359077377): True}
    assert d[Model(344404945359077377)]


def test_conversion() -> None:
    id_ = 344404945359077377
    m = Model(id_)

    assert int(m) == id_
    assert float(m) == float(id_)
    assert complex(m) == complex(id_)
    assert bin(m) == bin(id_)  # __index__


def test_equal() -> None:
    assert Model(344404945359077377) == 344404945359077377

    assert Model(344404945359077377) == Model(344404945359077377)
    assert not Model(344404945359077377) == 'Bluenix#7543'
    assert not Model(344404945359077377) == Model(841509053422632990)


def test_not_equal() -> None:
    assert Model(344404945359077377) != 841509053422632990

    assert Model(344404945359077377) != Model(841509053422632990)
    assert Model(344404945359077377) != 'Bluenix#7543'
    assert not Model(344404945359077377) != Model(344404945359077377)


def test_created_at() -> None:
    dt = datetime.fromtimestamp(1502182937.708, timezone.utc)
    assert Model(344404945359077377).created_at == dt


def test_snowflake_info() -> None:
    m = Snowflake(175928847299117063)

    assert m.worker_id == 1
    assert m.process_id == 0
    assert m.process_increment == 7


def test_snowflake_from_datetime() -> None:
    dt = datetime.fromtimestamp(1462015105796 / 1000)
    assert Snowflake.from_datetime(dt) == Snowflake(175928847298985984)
