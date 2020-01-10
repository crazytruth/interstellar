import random
from functools import wraps

from typing import Optional, Type, Dict

from grpclib.client import Channel, Stream, MultiDict, cast
from grpclib.const import Cardinality
from grpclib.exceptions import GRPCError
from grpclib.stream import _RecvType, _SendType
from grpclib.metadata import Deadline, _MetadataLike, _Metadata

from insanic.conf import settings
from interstellar.client.events import attach_events
from interstellar.exceptions import InterstellarError

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message import Message
import time


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


def convert_message_to_dict(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        def get_json_response_from_protobuf_message(message):
            """

            :param message: protobuf message object
            :type message: Message
            :return: dict
            """

            if not isinstance(message, Message):
                # TODO: discuss which one is better between None and empty dict. or raise error?
                return None

            converted_data = {}
            for item in dir(message):
                field = getattr(type(message), item)
                if hasattr(field, 'DESCRIPTOR') and isinstance(field.DESCRIPTOR, FieldDescriptor):
                    attribute = getattr(message, field.DESCRIPTOR.name)

                    if not isinstance(attribute, Message):
                        converted_data[item] = attribute
                    else:
                        converted_data[item] = get_json_response_from_protobuf_message(attribute)

            return converted_data

        reslut = await func(*args, **kwargs)
        start = time.time()
        result = get_json_response_from_protobuf_message(reslut)
        print(time.time() - start)
        return result
    return wrapper


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

    @convert_message_to_dict
    async def recv_message(self):
        return await super().recv_message()


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
