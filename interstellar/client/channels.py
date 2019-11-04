import asyncio
from typing import Optional, Type, Dict

from grpclib.client import Channel, Stream, MultiDict, cast
from grpclib.const import Cardinality
from grpclib.exceptions import GRPCError
from grpclib.stream import _RecvType, _SendType
from grpclib.metadata import Deadline, _MetadataLike, _Metadata

from insanic.conf import settings
from interstellar.exceptions import InterstellarError


class InterstellarStream(Stream):

    # def _raise_for_status(self, headers_map: Dict[str, str]) -> None:
    #     try:
    #         super()._raise_for_status(headers_map)
    #     except GRPCError as e:
    #         raise
    #
    # def _raise_for_grpc_status(self, headers_map: Dict[str, str]):
    #     try:
    #         super()._raise_for_grpc_status(headers_map)
    #     except GRPCError as e:
    #         raise
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
            error_code = headers_map.get(settings.INTERSTELLAR_INSANIC_ERROR_CODE_HEADER, None)
            raise InterstellarError(status=e.status, message=e.message, error_code=error_code)


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
