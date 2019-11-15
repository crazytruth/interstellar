import random

from typing import Optional, Type, Dict

from grpclib.client import Channel, Stream, MultiDict, cast
from grpclib.const import Cardinality
from grpclib.exceptions import GRPCError
from grpclib.stream import _RecvType, _SendType
from grpclib.metadata import Deadline, _MetadataLike, _Metadata

from insanic.conf import settings
from interstellar.client.events import attach_events
from interstellar.exceptions import InterstellarError


class ChannelPool:
    channels = {}

    @classmethod
    def get_channel(cls, service_name, host, port):
        if len(cls.channels.get(service_name, [])) < settings.INTERSTELLAR_CLIENT_CHANNEL_COUNT:
            if service_name not in cls.channels:
                cls.channels[service_name] = []
            channel = InterstellarChannel(host=host, port=port)
            attach_events(channel, service_name)
            cls.channels[service_name].append(channel)
            return channel
        return random.choice(cls.channels[service_name])

    @classmethod
    def reset(cls):
        cls.channels = {}


class InterstellarStream(Stream):

    async def recv_initial_metadata(self) -> None:

        try:
            result = await super().recv_initial_metadata()
        except GRPCError as e:

            raise
        else:
            return result

    def _raise_for_grpc_status(self, headers_map: Dict[str, str]):
        try:
            super()._raise_for_grpc_status(headers_map)
        except GRPCError as e:
            raise InterstellarError(status=e.status, message=e.message)


class InterstellarChannel(Channel):

    def request(
            self,
            name: str,
            cardinality: Cardinality,
            request_type: Type[_SendType],
            reply_type: Type[_RecvType],
            *,
            timeout: Optional[float] = None,
            deadline: Optional[Deadline] = None,
            metadata: Optional[_MetadataLike] = None,
    ) -> Stream[_SendType, _RecvType]:
        if timeout is not None and deadline is None:
            deadline = Deadline.from_timeout(timeout)
        elif timeout is not None and deadline is not None:
            deadline = min(Deadline.from_timeout(timeout), deadline)

        metadata = cast(_Metadata, MultiDict(metadata or ()))

        return InterstellarStream(self, name, metadata, cardinality,
                                  request_type, reply_type, codec=self._codec,
                                  dispatch=self.__dispatch__, deadline=deadline)
