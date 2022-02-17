from wumpy.models import AllowedMentions


def test_equal() -> None:
    assert AllowedMentions() == AllowedMentions()
    assert not AllowedMentions() == 'AllowedMentions'


def test_instantion() -> None:
    am = AllowedMentions(everyone=False, users=(123,), roles=(456,), replied_user=True)
    assert am.everyone is False
    assert am.users == (123,)
    assert am.roles == (456,)
    assert am.replied_user is True


def test_none() -> None:
    assert AllowedMentions.none() == {
        'parse': [],
        'replied_user': False,
    }


def test_all() -> None:
    assert AllowedMentions.all() == {
        'parse': ['everyone', 'users', 'roles'],
        'replied_user': True,
    }


def test_bitwise_or() -> None:
    a = AllowedMentions(everyone=False, replied_user=True)
    b = AllowedMentions(everyone=True, users=[123, 456, 789])
    assert a | b == AllowedMentions(everyone=True, users=[123, 456, 789], replied_user=True)


def test_replace() -> None:
    replaced = AllowedMentions(everyone=False, roles=[123]).replace(everyone=True)
    assert replaced == AllowedMentions(everyone=True, roles=[123])
