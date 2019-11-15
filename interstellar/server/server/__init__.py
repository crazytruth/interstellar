from typing import TYPE_CHECKING, Callable, Any

from grpclib.protocol import H2Protocol
from grpclib.server import Handler, Server, _Headers

from .handlers import RequestHandler

if TYPE_CHECKING:
    from grpclib import protocol  # noqa


class InterstellarHandler(Handler):

    def accept(
            self,
            stream: 'protocol.Stream',
            headers: _Headers,
            release_stream: Callable[[], Any],
    ) -> None:
        self.__gc_step__()
        handler = RequestHandler(self.mapping, stream, headers, self.codec,
                                 self.dispatch, release_stream)
        self._tasks[stream] = self.loop.create_task(
            handler.handle()
        )


class GRPCServer(Server):

    def _protocol_factory(self) -> H2Protocol:
        self.__gc_step__()
        handler = InterstellarHandler(self._mapping, self._codec, self.__dispatch__,
                                      loop=self._loop)
        self._handlers.add(handler)
        return H2Protocol(handler, self._config, loop=self._loop)
