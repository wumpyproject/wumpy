from datetime import datetime
from typing import List, Optional, Tuple, Union

import attrs
from discord_typings import (
    EmbedAuthorData, EmbedData, EmbedFieldData, EmbedFooterData,
    EmbedImageData, EmbedThumbnailData
)
from typing_extensions import Self


__all__ = (
    'EmbedThumbnail',
    'EmbedImage',
    'EmbedFooter',
    'EmbedField',
    'EmbedAuthor',
    'Embed',
    'EmbedBuilder',
    'embed_data',
)


@attrs.define(frozen=True)
class EmbedThumbnail:
    url: str
    proxy_url: Optional[str] = attrs.field(default=None, kw_only=True)
    height: Optional[int] = attrs.field(default=None, kw_only=True)
    width: Optional[int] = attrs.field(default=None, kw_only=True)

    @classmethod
    def from_data(cls, data: EmbedThumbnailData) -> Self:
        return cls(
            url=data['url'],
            proxy_url=data.get('proxy_url'),
            height=data.get('height'),
            width=data.get('width')
        )


@attrs.define(frozen=True)
class EmbedImage:
    url: str
    proxy_url: Optional[str] = attrs.field(default=None, kw_only=True)
    height: Optional[int] = attrs.field(default=None, kw_only=True)
    width: Optional[int] = attrs.field(default=None, kw_only=True)

    @classmethod
    def from_data(cls, data: EmbedImageData) -> Self:
        return cls(
            url=data['url'],
            proxy_url=data.get('proxy_url'),
            height=data.get('height'),
            width=data.get('width')
        )


@attrs.define(frozen=True)
class EmbedFooter:
    text: str
    icon_url: Optional[str] = attrs.field(default=None, kw_only=True)
    proxy_icon_url: Optional[str] = attrs.field(default=None, kw_only=True)

    @classmethod
    def from_data(cls, data: EmbedFooterData) -> Self:
        return cls(
            text=data['text'],
            icon_url=data.get('icon_url'),
            proxy_icon_url=data.get('proxy_icon_url')
        )


@attrs.define(frozen=True)
class EmbedField:
    name: str
    value: str
    inline: bool = attrs.field(default=False, kw_only=True)

    @classmethod
    def from_data(cls, data: EmbedFieldData) -> Self:
        return cls(
            name=data['name'],
            value=data['value'],
            inline=data.get('inline', False)
        )


@attrs.define(frozen=True)
class EmbedAuthor:
    name: str
    url: Optional[str] = attrs.field(default=None, kw_only=True)
    icon_url: Optional[str] = attrs.field(default=None, kw_only=True)
    proxy_icon_url: Optional[str] = attrs.field(default=None, kw_only=True)

    @classmethod
    def from_data(cls, data: EmbedAuthorData) -> Self:
        return cls(
            name=data['name'],
            url=data.get('url'),
            icon_url=data.get('icon_url'),
            proxy_icon_url=data.get('proxy_icon_url')
        )


@attrs.define(frozen=True, kw_only=True)
class Embed:
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

    colour: Optional[int] = None
    timestamp: Optional[datetime] = None

    footer: Optional[EmbedFooter] = None
    image: Optional[EmbedImage] = None
    thumbnail: Optional[EmbedThumbnail] = None
    author: Optional[EmbedAuthor] = None
    fields: Tuple[EmbedField, ...] = ()

    @classmethod
    def from_data(cls, data: EmbedData) -> Self:
        timestamp = data.get('timestamp')
        if timestamp is not None:
            timestamp = datetime.fromisoformat(timestamp)

        footer = data.get('footer')
        if footer is not None:
            footer = EmbedFooter.from_data(footer)

        image = data.get('image')
        if image is not None:
            image = EmbedImage.from_data(image)

        thumbnail = data.get('thumbnail')
        if thumbnail is not None:
            thumbnail = EmbedThumbnail.from_data(thumbnail)

        author = data.get('author')
        if author is not None:
            author = EmbedAuthor.from_data(author)

        return cls(
            title=data.get('title'),
            description=data.get('description'),
            url=data.get('url'),
            colour=data.get('color'),
            timestamp=timestamp,

            footer=footer,
            image=image,
            thumbnail=thumbnail,
            author=author,
            fields=tuple(EmbedField.from_data(field) for field in data.get('fields', []))
        )

    @classmethod
    def from_builder(cls, builder: 'EmbedBuilder') -> Self:
        return cls(
            title=builder.title,
            description=builder.description,
            url=builder.url,
            colour=builder.colour,
            timestamp=builder.timestamp,

            footer=builder.footer,
            image=builder.image,
            thumbnail=builder.thumbnail,
            author=builder.author,
            fields=tuple(builder.fields)
        )


@attrs.define()
class EmbedBuilder:
    """Discord.py-style embed builder."""

    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = attrs.field(default=None, kw_only=True)

    colour: Optional[int] = attrs.field(default=None, kw_only=True)
    timestamp: Optional[datetime] = attrs.field(default=None, kw_only=True)

    footer: Optional[EmbedFooter] = attrs.field(default=None, kw_only=True)
    image: Optional[EmbedImage] = attrs.field(default=None, kw_only=True)
    thumbnail: Optional[EmbedThumbnail] = attrs.field(default=None, kw_only=True)
    author: Optional[EmbedAuthor] = attrs.field(default=None, kw_only=True)
    fields: List[EmbedField] = attrs.field(factory=list, kw_only=True)

    def set_footer(self, *, text: str, icon_url: Optional[str] = None) -> Self:
        self.footer = EmbedFooter(text=text, icon_url=icon_url, proxy_icon_url=None)
        return self

    def remove_footer(self) -> Self:
        self.footer = None
        return self

    def set_image(self, *, url: str) -> Self:
        self.image = EmbedImage(url=url, proxy_url=None, height=None, width=None)
        return self

    def set_thumbnail(self, *, url: str) -> Self:
        self.thumbnail = EmbedThumbnail(url=url, proxy_url=None, height=None, width=None)
        return self

    def set_author(
        self,
        *,
        name: str,
        url: Optional[str] = None,
        icon_url: Optional[str] = None
    ) -> Self:
        self.author = EmbedAuthor(name=name, url=url, icon_url=icon_url, proxy_icon_url=None)
        return self

    def remove_author(self) -> Self:
        self.author = None
        return self

    def add_field(self, *, name: str, value: str, inline: bool = True) -> Self:
        self.fields.append(EmbedField(name=name, value=value, inline=inline))
        return self

    def insert_field_at(
        self,
        index: int,
        *,
        name: str,
        value: str,
        inline: bool = True
    ) -> Self:
        field = EmbedField(name=name, value=value, inline=inline)
        self.fields.insert(index, field)
        return self

    def clear_fields(self) -> Self:
        self.fields.clear()
        return self

    def remove_field(self, index: int) -> Self:
        try:
            del self.fields[index]
        except IndexError:
            pass

        return self

    def set_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> Self:
        field = EmbedField(name=name, value=value, inline=inline)
        self.fields[index] = field
        return self

    def finalize(self) -> Embed:
        return Embed.from_builder(self)


def embed_data(embed: Union[Embed, EmbedBuilder]) -> EmbedData:
    """Utility function to transform a user-built model into a dictionary.

    Parameter:
        embed: The embed model or builder.

    Returns:
        The data for the embed.
    """
    data: EmbedData = {'fields': []}

    if embed.title is not None:
        data['title'] = embed.title

    if embed.description is not None:
        data['description'] = embed.description

    if embed.url is not None:
        data['url'] = embed.url

    if embed.colour is not None:
        data['color'] = embed.colour

    if embed.timestamp is not None:
        data['timestamp'] = embed.timestamp.isoformat()

    if embed.footer is not None:
        data['footer'] = {
            'text': embed.footer.text,
        }

        if embed.footer.icon_url is not None:
            data['footer']['icon_url'] = embed.footer.icon_url

    if embed.image is not None:
        data['image'] = {'url': embed.image.url}

    if embed.thumbnail is not None:
        data['thumbnail'] = {'url': embed.thumbnail.url}

    if embed.author is not None:
        data['author'] = {'name': embed.author.name}

        if embed.author.url is not None:
            data['author']['url'] = embed.author.url

        if embed.author.icon_url is not None:
            data['author']['icon_url'] = embed.author.icon_url

    for field in embed.fields:
        data['fields'].append({
            'name': field.name,
            'value': field.value,
            'inline': field.inline,
        })

    return data
