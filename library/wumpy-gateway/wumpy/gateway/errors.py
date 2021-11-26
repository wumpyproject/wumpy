__all__ = ('ConnectionClosed',)


class ConnectionClosed(Exception):
    """Exception indicating that the connection to Discord fully closed.

    This is raised when the connection cannot naturally reconnect and the
    program should exit - which happens if Discord unexpectedly closes the
    socket during the crucial bootstrapping process.
    """
    pass
