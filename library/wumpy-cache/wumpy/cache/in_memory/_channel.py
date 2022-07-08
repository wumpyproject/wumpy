import collections
from typing import (
    Any, Deque, Dict, FrozenSet, Mapping, Optional, SupportsInt, Type, Union
)

from discord_typings import (
    ChannelData, MessageCreateData, MessageDeleteBulkData, MessageDeleteData,
    MessageUpdateData
)
from wumpy.models import Category, Message, TextChannel, Thread, VoiceChannel

from ._base import BaseMemoryCache, Channel

__all__ = (
    'ChannelMemoryCache',
    'MessageMemoryCache',
)


AllChannels = Union[Channel, Category, Thread]


class ChannelMemoryCache(BaseMemoryCache):
    _channels: Dict[int, AllChannels]

    CHANNELS: Mapping[int, Type[AllChannels]] = {
        0: TextChannel,
        2: VoiceChannel,
        4: Category,
        5: TextChannel,
        10: Thread,
        11: Thread,
        12: Thread,
        13: VoiceChannel,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._channels = {}

    def _process_create_channel(self, data: ChannelData, *, return_old: bool = True) -> None:
        cls = self.CHANNELS[data['type']]
        # The type checker doesn't understand the relation between data['type']
        # and the class returned so it thinks that any channel data may be
        # passed to any channel class.
        channel = cls.from_data(data)  # type: ignore
        self._channels[channel.id] = channel
        return

    def _process_channel_update(
            self,
            data: ChannelData,
            *,
            return_old: bool = True
    ) -> Optional[AllChannels]:
        old = self._process_channel_delete(data, return_old=return_old)
        self._process_create_channel(data, return_old=return_old)
        return old

    def _process_channel_delete(
        self,
        data: ChannelData,
        *,
        return_old: bool = True
    ) -> Optional[AllChannels]:
        return self._channels.pop(int(data['id']), None)

    async def get_channel(self, channel: SupportsInt) -> Optional[AllChannels]:
        return self._channels.get(int(channel))

    async def get_thread(self, thread: SupportsInt) -> Optional[Thread]:
        channel = self.get_channel(thread)
        if isinstance(channel, Thread):
            return channel

        return None

    async def get_category(self, category: SupportsInt) -> Optional[Category]:
        channel = await self.get_channel(category)
        if isinstance(channel, Category):
            return channel

        return None


class MessageMemoryCache(BaseMemoryCache):
    _messages: Deque[Message]

    def __init__(self, *args: Any, max_messages: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._messages = collections.deque(maxlen=max_messages)

    def _process_message_create(
            self,
            data: MessageCreateData,
            *,
            return_old: bool = True
    ) -> None:
        m = Message.from_data(data)
        self._messages.append(m)

    def _process_message_update(
            self,
            data: MessageUpdateData,
            *,
            return_old: bool = True
    ) -> Optional[Message]:
        old = self._process_message_delete(data, return_old=return_old)
        self._process_message_create(data, return_old=return_old)
        return old

    def _process_message_delete(
            self,
            data: MessageDeleteData,
            *,
            return_old: bool = True
    ) -> Optional[Message]:
        if return_old:
            id_ = int(data['id'])

            found = [msg for msg in self._messages if msg == id_]
            if found:
                return found[0]

        return None

    def _process_message_delete_bulk(
        self,
        data: MessageDeleteBulkData,
        *,
        return_old: bool = True
    ) -> FrozenSet[Message]:
        if return_old:
            ids = set([int(id_) for id_ in data['ids']])

            found = [msg for msg in self._messages if msg.id in ids]
            return frozenset(found)

        return frozenset()

    async def get_message(
        self,
        channel: Optional[SupportsInt],
        message: SupportsInt
    ) -> Optional[Message]:
        id_ = int(message)
        found = [msg for msg in self._messages if msg == id_]
        if found:
            return found[0]

        return None
