import asyncio

from typing import Dict, Callable, Any, Optional, TYPE_CHECKING

from insanic.conf import settings
from insanic.errors import GlobalErrorCodes

from grpclib.compat import nullcontext
from grpclib.const import Status
from grpclib.events import _DispatchServerEvents
from grpclib.exceptions import StreamTerminatedError, ProtocolError
from grpclib.metadata import Deadline, decode_metadata
from grpclib.protocol import H2Protocol
from grpclib.server import Handler, Server, Stream, _Headers
from grpclib.encoding.base import GRPC_CONTENT_TYPE, CodecBase
from grpclib.encoding.proto import ProtoCodec
from grpclib.utils import DeadlineWrapper, Wrapper

from interstellar.exceptions import InterstellarError
from interstellar.server.log import interstellar_server_access_log, \
    interstellar_server_error_log, \
    interstellar_server_log

if TYPE_CHECKING:
    from grpclib import const, protocol  # noqa


async def _abort(
        h2_stream: 'protocol.Stream',
        h2_status: int,
        grpc_status: Optional[Status] = None,
        grpc_message: Optional[str] = None,
        error_code: Optional[int] = None
) -> None:
    headers = [(':status', str(h2_status))]
    if grpc_status is not None:
        headers.append(('grpc-status', str(grpc_status.value)))
    if grpc_message is not None:
        headers.append(('grpc-message', grpc_message))
    if error_code is not None:
        headers.append((settings.INTERSTELLAR_INSANIC_ERROR_CODE_HEADER, error_code))

    await h2_stream.send_headers(headers, end_stream=True)
    if h2_stream.closable:
        h2_stream.reset_nowait()


async def interstellar_request_handler(
        mapping: Dict[str, 'const.Handler'],
        _stream: 'protocol.Stream',
        headers: _Headers,
        codec: CodecBase,
        dispatch: _DispatchServerEvents,
        release_stream: Callable[[], Any],
) -> None:
    try:
        headers_map = dict(headers)

        if headers_map[':method'] != 'POST':
            await _abort(_stream, 405)
            return

        content_type = headers_map.get('content-type')
        if content_type is None:
            await _abort(_stream, 415, Status.UNKNOWN,
                         'Missing content-type header',
                         int(GlobalErrorCodes.error_unspecified.value))
            return

        base_content_type, _, sub_type = content_type.partition('+')
        sub_type = sub_type or ProtoCodec.__content_subtype__
        if (
                base_content_type != GRPC_CONTENT_TYPE
                or sub_type != codec.__content_subtype__
        ):
            await _abort(_stream, 415, Status.UNKNOWN,
                         'Unacceptable content-type header',
                         int(GlobalErrorCodes.error_unspecified.value))
            return

        if headers_map.get('te') != 'trailers':
            await _abort(_stream, 400, Status.UNKNOWN,
                         'Required "te: trailers" header is missing',
                         int(GlobalErrorCodes.error_unspecified.value))
            return

        method_name = headers_map[':path']
        method = mapping.get(method_name)
        if method is None:
            await _abort(_stream, 200, Status.UNIMPLEMENTED,
                         'Method not found',
                         int(GlobalErrorCodes.method_not_allowed.value))
            return

        try:
            deadline = Deadline.from_headers(headers)
        except ValueError:
            await _abort(_stream, 200, Status.UNKNOWN,
                         'Invalid grpc-timeout header',
                         int(GlobalErrorCodes.invalid_usage.value))
            return

        metadata = decode_metadata(headers)

        async with Stream(
                _stream, method_name, method.cardinality,
                method.request_type, method.reply_type,
                codec=codec, dispatch=dispatch, deadline=deadline
        ) as stream:

            if deadline is None:
                wrapper = _stream.wrapper = Wrapper()
                deadline_wrapper = nullcontext()
            else:
                wrapper = _stream.wrapper = DeadlineWrapper()
                deadline_wrapper = wrapper.start(deadline)

            try:
                with deadline_wrapper, wrapper:
                    stream.metadata, method_func = await dispatch.recv_request(
                        metadata,
                        method.func,
                        method_name=method_name,
                        deadline=deadline,
                        content_type=content_type,
                    )
                    await method_func(stream)
            except asyncio.TimeoutError:
                if wrapper.cancel_failed:
                    interstellar_server_error_log.exception('Failed to handle cancellation')
                    raise InterstellarError(Status.DEADLINE_EXCEEDED)
                elif wrapper.cancelled:
                    interstellar_server_error_log.info('Deadline exceeded')
                    raise InterstellarError(Status.DEADLINE_EXCEEDED)
                else:
                    interstellar_server_error_log.exception('Timeout occurred')
                    raise
            except StreamTerminatedError as err:
                if wrapper.cancel_failed:
                    interstellar_server_error_log.exception('Failed to handle cancellation')
                    raise
                else:
                    assert wrapper.cancelled
                    interstellar_server_error_log.info('Request was cancelled: %s', err)
                    raise
            except Exception:
                interstellar_server_error_log.exception('Application error')
                raise
    except ProtocolError:
        interstellar_server_error_log.exception('Application error')
    except Exception as e:
        interstellar_server_error_log.exception('Server error')
    finally:
        release_stream()


class InterstellarHandler(Handler):

    def accept(
            self,
            stream: 'protocol.Stream',
            headers: _Headers,
            release_stream: Callable[[], Any],
    ) -> None:
        self.__gc_step__()
        self._tasks[stream] = self.loop.create_task(
            interstellar_request_handler(self.mapping, stream, headers, self.codec,
                                         self.dispatch, release_stream)
        )


class GRPCServer(Server):

    def _protocol_factory(self) -> H2Protocol:
        self.__gc_step__()
        handler = InterstellarHandler(self._mapping, self._codec, self.__dispatch__,
                                      loop=self._loop)
        self._handlers.add(handler)
        return H2Protocol(handler, self._config, loop=self._loop)
