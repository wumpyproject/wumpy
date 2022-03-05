from typing import Dict, Union
from urllib.parse import quote as urlquote

__all__ = ('Route',)


class Route:
    """A route that a request should be made to.

    Containing information such as the endpoint, and parameters to use. Mainly
    used to figure out ratelimit handling. If the request made should have a
    request body this should be passed to the requester.

    Attributes:
        method: The HTTP method to use.
        path: The path to the endpoint, concatenated to the `BASE` url.
        params:
            The parameters to format into the path, separated to allow easier
            ratelimit handling.
    """

    method: str
    path: str
    params: Dict[str, Union[str, int]]

    __slots__ = ('method', 'path', 'params')

    BASE = 'https://discord.com/api/v10'

    def __init__(self, method: str, path: str, **params: Union[str, int]) -> None:
        self.method = method
        self.path = path

        self.params = params

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Route) and self.endpoint == other.endpoint

    def __repr__(self) -> str:
        return f'<Route {self.endpoint}>'

    def __str__(self) -> str:
        return self.endpoint

    def __hash__(self) -> int:
        return hash(self.endpoint)

    @property
    def url(self) -> str:
        """Return a complete, formatted url that a request should be made to."""
        return self.BASE + self.path.format_map(
            # Replace special characters with the %xx escapes
            {k: urlquote(v) if isinstance(v, str) else v for k, v in self.params.items()}
        )

    @property
    def endpoint(self) -> str:
        """Return the Discord endpoint this route will request."""
        return f'{self.method} {self.path}'

    @property
    def major_params(self) -> str:
        """Return a string of the formatted major parameters."""
        param = (
            self.params.get('webhook_id')
            or self.params.get('channel_id')
            or self.params.get('guild_id')
        )

        if param:
            # TODO: Discord handles messages over 14 days differently in terms
            # of ratelimiting because it is more costly.
            return f':{param}'

        return ''
