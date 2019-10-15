import pytest

from insanic import Insanic
from insanic.conf import settings
from insanic.services import Service

from interstellar.client import InterstellarClient
from interstellar.server import InterstellarServer


class TestDispatch:
    @pytest.fixture()
    def test_server(self, test_server, loop, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ['tests.blackhole.PlanetOfTheApes'], raising=False)
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVER_PORT_DELTA', 1, raising=False)

        server = Insanic('test')
        InterstellarServer.init_app(server)

        return loop.run_until_complete(test_server(server))

    async def test_dispatch_with_stub(self, insanic_application, monkeypatch, test_server):
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = Service('test')
        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        with service.grpc('monkey', 'ApeService') as stub:
            request = stub.GetChimpanzee.request_type(id="1", include="sound")

            reply = await stub.GetChimpanzee(request)

            assert reply
            assert reply.extra == "woo woo ahh ahh"

    async def test_dispatch_with_service_method(self, insanic_application, monkeypatch, test_server):
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = Service('test')
        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        with service.grpc('monkey', 'ApeService', 'GetChimpanzee') as method:
            request = method.request_type(id="1", include="sound")

            reply = await method(request)

            assert reply
            assert reply.extra == "woo woo ahh ahh"
