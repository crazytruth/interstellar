import asyncio
from typing import Dict, Callable, Any, Optional, TYPE_CHECKING, Type

from aiohttp.web_protocol import RequestHandler
from grpclib.compat import nullcontext
from grpclib.const import Status, Cardinality
from grpclib.encoding.base import CodecBase, GRPC_CONTENT_TYPE
from grpclib.encoding.proto import ProtoCodec
from grpclib.events import _DispatchServerEvents
from grpclib.exceptions import StreamTerminatedError, ProtocolError
from grpclib.metadata import Deadline, decode_metadata, _MetadataLike
from grpclib.server import Stream, _Headers
from grpclib.stream import _RecvType, _SendType
from grpclib.utils import DeadlineWrapper, Wrapper

from insanic import status as http_status
from insanic.conf import settings
from insanic.exceptions import APIException
from insanic.log import error_logger

from interstellar.exceptions import InterstellarError
from interstellar.logging import interstellar_access_log
from interstellar.server.exceptions import InterstellarAbort

if TYPE_CHECKING:
    from grpclib import const, protocol  # noqa


class _DummyService:
    request_service = "?"


dummy_service = _DummyService()


class InterstellarServerStream(Stream):

    def __init__(
            self,
            stream: 'protocol.Stream',
            method_name: str,
            cardinality: Cardinality,
            recv_type: Type[_RecvType],
            send_type: Type[_SendType],
            request_handler: RequestHandler,
            *,
            codec: CodecBase,
            dispatch: _DispatchServerEvents,
            deadline: Optional[Deadline] = None,

    ):
        self.request_handler = request_handler
        super().__init__(
            stream=stream,
            method_name=method_name,
            cardinality=cardinality,
            recv_type=recv_type,
            send_type=send_type,
            codec=codec,
            dispatch=dispatch,
            deadline=deadline
        )

    async def send_trailing_metadata(
            self,
            *,
            status: Status = Status.OK,
            status_message: Optional[str] = None,
            metadata: Optional[_MetadataLike] = None,
    ):
        await super().send_trailing_metadata(status=status, status_message=status_message, metadata=metadata)
        self.request_handler.message = status_message
        self.request_handler.h2_status = 200
        self.request_handler.grpc_status = status
        self.request_handler._log_access(status_message)


class RequestHandler:
    __slots__ = ('mapping', 'h2_stream', 'headers', 'headers_map',
                 'codec', 'dispatch', 'release_stream', 'metadata',
                 'deadline', 'method_name', 'method', 'content_type',
                 'h2_status', 'grpc_status', 'message')

    def __init__(self,
                 mapping: Dict[str, 'const.Handler'],
                 _stream: 'protocol.Stream',
                 headers: _Headers,
                 codec: CodecBase,
                 dispatch: _DispatchServerEvents,
                 release_stream: Callable[[], Any]) -> None:

        self.mapping = mapping
        self.h2_stream = _stream
        self.headers = headers
        self.codec = codec
        self.dispatch = dispatch
        self.release_stream = release_stream

        self.headers_map = dict(headers)
        self.content_type = None
        self.deadline = None
        self.method_name = None
        self.method = None
        self.metadata = None

        self.h2_status = None
        self.grpc_status = None
        self.message = ''

    async def handle(self):

        try:
            self._verify_protocol()
            self.metadata = decode_metadata(self.headers)
            await self._handle_request(self.metadata)
        except InterstellarAbort as e:
            self.h2_status = e.h2_status
            self.grpc_status = e.status
            self.message = e.message
            await self._abort(e.h2_status, e.status, e.message)
            return
        except ProtocolError as e:
            self.h2_status = http_status.HTTP_500_INTERNAL_SERVER_ERROR
            self.grpc_status = Status.INTERNAL
            self.message = "Protocal Application Error. This will need attention!"
            self._log_access(self.message, exc_info=e)
        except Exception as e:
            self.h2_status = http_status.HTTP_500_INTERNAL_SERVER_ERROR
            self.grpc_status = Status.INTERNAL
            self.message = "Protocal Application Error. This will need attention!"
            self._log_access(self.message, exc_info=e)
        finally:
            self.release_stream()

    def _log_access(self, message: Optional[str] = "", exc_info: Optional[Exception] = None):
        log_extra = {}
        for k, v in self.headers_map.items():
            if k.startswith(":"):
                log_extra.update({k[1:]: v})

        log_extra.update({"host": log_extra.get('authority', '?')})

        log_extra.update({"status": self.h2_status or http_status.HTTP_500_INTERNAL_SERVER_ERROR})

        grpc_status = self.grpc_status or Status.UNKNOWN

        if isinstance(grpc_status, Status):
            grpc_status = grpc_status.value

        log_extra.update({"grpc_status": grpc_status})

        log_extra.update({"request_service": self.headers_map.get(settings.INTERNAL_REQUEST_SERVICE_HEADER, "?")})
        log_extra.update({"correlation_id": self.headers_map.get(settings.REQUEST_ID_HEADER_FIELD, "?")})
        log_extra.update({"stream_id": self.h2_stream.id})
        try:
            log_extra.update({"deadline": self.deadline})
        except AttributeError:
            log_extra.update({"deadline": "0"})

        message = message or self.message

        if exc_info:
            interstellar_access_log.error(message, extra=log_extra, exc_info=exc_info)
        else:
            interstellar_access_log.info(message, extra=log_extra)

    async def _abort(self,
                     h2_status: int,
                     grpc_status: Optional[Status] = None,
                     grpc_message: Optional[str] = None, ) -> None:

        headers = [(':status', str(h2_status))]
        if grpc_status is not None:
            headers.append(('grpc-status', str(grpc_status.value)))
        if grpc_message is not None:
            headers.append(('grpc-message', grpc_message))

        await self.h2_stream.send_headers(headers, end_stream=True)
        if self.h2_stream.closable:
            self.h2_stream.reset_nowait()

    def _verify_protocol(self):
        if self.headers_map.get(':method', "") != 'POST':
            raise InterstellarAbort(405)

        self.content_type = self.headers_map.get('content-type')
        if self.content_type is None:
            raise InterstellarAbort(415, Status.UNKNOWN,
                                    'Missing content-type header')

        base_content_type, _, sub_type = self.content_type.partition('+')
        sub_type = sub_type or ProtoCodec.__content_subtype__
        if (
                base_content_type != GRPC_CONTENT_TYPE
                or sub_type != self.codec.__content_subtype__
        ):
            raise InterstellarAbort(415, Status.UNKNOWN,
                                    'Unacceptable content-type header')

        if self.headers_map.get('te') != 'trailers':
            raise InterstellarAbort(400, Status.UNKNOWN,
                                    'Required "te: trailers" header is missing')

        self.method_name = self.headers_map.get(':path')
        if self.method_name is None:
            raise InterstellarAbort(200, Status.UNIMPLEMENTED,
                                    'Method not found')

        self.method = self.mapping.get(self.method_name)
        if self.method is None:
            raise InterstellarAbort(200, Status.UNIMPLEMENTED,
                                    'Method not found')

        try:
            self.deadline = Deadline.from_headers(self.headers)
        except ValueError:
            raise InterstellarAbort(200, Status.UNKNOWN,
                                    'Invalid grpc-timeout header')

    async def _handle_request(self, metadata) -> None:

        async with InterstellarServerStream(
                stream=self.h2_stream,
                method_name=self.method_name,
                cardinality=self.method.cardinality,
                recv_type=self.method.request_type,
                send_type=self.method.reply_type,
                request_handler=self,
                codec=self.codec,
                dispatch=self.dispatch,
                deadline=self.deadline
        ) as stream:
            if self.deadline is None:
                wrapper = self.h2_stream.wrapper = Wrapper()
                deadline_wrapper = nullcontext()
            else:
                wrapper = self.h2_stream.wrapper = DeadlineWrapper()
                deadline_wrapper = wrapper.start(self.deadline)

            try:
                with deadline_wrapper, wrapper:
                    stream.metadata, method_func = await self.dispatch.recv_request(
                        metadata,
                        self.method.func,
                        method_name=self.method_name,
                        deadline=self.deadline,
                        content_type=self.content_type
                    )
                    await method_func(stream)
            except asyncio.TimeoutError:
                if wrapper.cancel_failed:
                    raise InterstellarError(status=Status.DEADLINE_EXCEEDED, message='Failed to handle cancellation')
                elif wrapper.cancelled:
                    raise InterstellarError(status=Status.DEADLINE_EXCEEDED, message='Deadline exceeded')
                else:
                    raise
            except StreamTerminatedError as err:
                if wrapper.cancel_failed:
                    raise
                else:
                    error_logger.info('Request was cancelled: %s', err)
                    raise
            except APIException as err:
                error_logger.warning("An APIException was raised. Please use a InterstellarError "
                                     "to raise your exceptions.")
                raise

# GRPC_HTTP_STATUS_MAP = OrderedDict([
#     (GRPCStatus.OK, status.HTTP_200_OK),
#     (GRPCStatus.CANCELLED, status.HTTP_499_CLIENT_CLOSED_REQUEST),
#     (GRPCStatus.UNKNOWN, status.HTTP_500_INTERNAL_SERVER_ERROR),
#     (GRPCStatus.INVALID_ARGUMENT, status.HTTP_400_BAD_REQUEST),
#     (GRPCStatus.DEADLINE_EXCEEDED, status.HTTP_504_GATEWAY_TIMEOUT),
#     (GRPCStatus.NOT_FOUND, status.HTTP_404_NOT_FOUND),
#     (GRPCStatus.ALREADY_EXISTS, status.HTTP_409_CONFLICT),
#     (GRPCStatus.PERMISSION_DENIED, status.HTTP_403_FORBIDDEN),
#     (GRPCStatus.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED),
#     (GRPCStatus.RESOURCE_EXHAUSTED, status.HTTP_429_TOO_MANY_REQUESTS),
#     (GRPCStatus.FAILED_PRECONDITION, status.HTTP_400_BAD_REQUEST),
#     (GRPCStatus.ABORTED, status.HTTP_409_CONFLICT),
#     (GRPCStatus.OUT_OF_RANGE, status.HTTP_400_BAD_REQUEST),
#     (GRPCStatus.UNIMPLEMENTED, status.HTTP_501_NOT_IMPLEMENTED),
#     (GRPCStatus.INTERNAL, status.HTTP_500_INTERNAL_SERVER_ERROR),
#     (GRPCStatus.UNAVAILABLE, status.HTTP_503_SERVICE_UNAVAILABLE),
#     (GRPCStatus.DATA_LOSS, status.HTTP_500_INTERNAL_SERVER_ERROR)
# ])
