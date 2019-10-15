import asyncio
from grpclib.events import listen, RecvRequest
from grpclib.server import Server

from interstellar.server import InterstellarServer
from interstellar.server.events import interstellar_server_event_recv_request

from insanic.conf import settings


class TestInterstellarServerInit:

    def test_init_without_servers(self, insanic_application):

        InterstellarServer.init_app(insanic_application)

        assert InterstellarServer.config_imported is True
        assert "interstellar_server" in insanic_application.initialized_plugins
        assert insanic_application.initialized_plugins['interstellar_server'] is InterstellarServer

        from interstellar.server import config

        for c in dir(config):
            if c.isupper():
                assert hasattr(settings, c)

    def test_init_with_servers(self, insanic_application, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ["tests.blackhole.PlanetOfTheApes"])

        InterstellarServer.init_app(insanic_application)

        assert InterstellarServer.app is insanic_application
        assert InterstellarServer.config_imported is True
        assert "interstellar_server" in insanic_application.initialized_plugins
        assert insanic_application.initialized_plugins['interstellar_server'] is InterstellarServer

        from interstellar.server import config

        for c in dir(config):
            if c.isupper():
                assert hasattr(settings, c)

        assert InterstellarServer.health_beacons is not None
        assert InterstellarServer.warp_beacon is not None
        assert isinstance(InterstellarServer.warp_beacon, Server)
        assert "after_server_start_start_grpc" in [l.__name__ for l in
                                                   insanic_application.listeners['after_server_start']]
        assert "before_server_stop_stop_grpc" in [l.__name__ for l in
                                                  insanic_application.listeners['before_server_stop']]
        assert InterstellarServer.warp_beacon.__dispatch__._listeners[RecvRequest] == [
            interstellar_server_event_recv_request]


class TestInterstellarServerStartStop:

    async def test_start_stop_no_servers(self, insanic_application, unused_port, monkeypatch):
        InterstellarServer.init_app(insanic_application)

        await InterstellarServer.start('0.0.0.0', unused_port, reuse_address=False, reuse_port=False)

        await InterstellarServer.stop()

    async def test_start_stop(self, insanic_application, unused_port, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ["tests.blackhole.PlanetOfTheApes"])
        InterstellarServer.init_app(insanic_application)

        await InterstellarServer.start('0.0.0.0', unused_port, reuse_address=False, reuse_port=False)

        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect(('127.0.0.1', int(unused_port)))
            s.shutdown(2)
        except:
            raise
        finally:
            await InterstellarServer.stop()

        assert len(InterstellarServer.warp_beacon._server.sockets) == 0
