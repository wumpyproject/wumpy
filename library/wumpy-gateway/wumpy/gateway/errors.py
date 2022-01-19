__all__ = ('ConnectionClosed',)


class ConnectionClosed(Exception):
    """Exception indicating that the connection to Discord fully closed.

    This is raised when the connection cannot naturally reconnect and the
    program should exit - which happens if Discord unexpectedly closes the
    socket during the crucial bootstrapping process.

    Additionally, it may also be raised if Discord responded with a special
    error code in the 4000-range - which signals that the connection absolutely
    cannot reconnect such as sending an improper token or intents.
    """
    pass
