import dataclasses
from typing import Literal, Optional
from urllib.parse import parse_qs, urlencode, urlsplit

from discord_typings.resources.channel import AttachmentData
from typing_extensions import Self

from .base import Model

__all__ = ('Asset', 'Attachment')


@dataclasses.dataclass(frozen=True)
class Asset:

    url: str

    BASE = 'https://cdn.discordapp.com'

    __slots__ = ('url',)

    @classmethod
    def from_path(cls, path: str) -> Self:
        return cls(cls.BASE + path)

    def replace(
        self,
        *,
        fmt: Optional[Literal['jpeg', 'jpg', 'png', 'webp', 'gif', 'json']] = None,
        size: Optional[int] = None
    ) -> Self:
        url = urlsplit(self.url)
        path = url.path
        query = url.query

        if size is not None:
            if not (4096 >= size >= 16):
                raise ValueError('size argument must be between 16 and 4096.')

            elif size & (size - 1) != 0:
                # All powers of two only have one bit set: 1000
                # if we subtract 1, then (0111) AND it we should get 0 (0000).
                raise ValueError('size argument must be a power of two.')

            query = parse_qs(url.query)
            query['size'] = [str(size)]
            query = urlencode(query, doseq=True)

        if fmt is not None:
            if fmt not in {'jpeg', 'jpg', 'png', 'webp', 'gif', 'json'}:
                raise ValueError(
                    "Image format must be one of: 'jpeg', 'jpg', 'png', 'webp', "
                    "'gif, or 'json' (for Lottie)"
                )

            destination, _, _ = path.rpartition('.')
            path = f'{destination}.{fmt}'

        return self.__class__(f'{url.scheme}://{url.netloc}{path}?{query}')


@dataclasses.dataclass(frozen=True, eq=False)
class Attachment(Model):
    filename: str
    content_type: Optional[str]
    description: Optional[str]

    size: int
    url: str
    proxy_url: str

    height: Optional[int]
    width: Optional[int]
    ephemeral: bool

    @classmethod
    def from_data(cls, data: AttachmentData) -> Self:
        return cls(
            id=int(data['id']),
            filename=data['filename'],
            content_type=data.get('content_type'),
            description=data.get('description'),

            size=int(data['size']),
            url=data['url'],
            proxy_url=data['proxy_url'],

            height=data.get('height'),
            width=data.get('width'),
            ephemeral=data.get('ephemeral', False)
        )
