def loader(_, data):
    assert data.get('passed') is True

    return lambda _: _
