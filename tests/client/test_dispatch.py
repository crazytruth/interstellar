import pytest

from grpclib.const import Status

from insanic import Insanic
from insanic.conf import settings
from insanic.services import Service

from interstellar.client import InterstellarClient
from interstellar.server import InterstellarServer

from grpclib.exceptions import GRPCError

class TestDispatch:

    @pytest.fixture()
    def test_server(self, test_server, loop, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ['tests.blackhole.PlanetOfTheApes',
                                                               'tests.blackhole.PlanetOfTheMonkeys'], raising=False)
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

        with service.grpc('monkey', 'v1', 'ApeService') as stub:
            request = stub.GetChimpanzee.request_type(id="1", include="sound")

            reply = await stub.GetChimpanzee(request)

            assert reply
            assert reply['extra'] == "woo woo ahh ahh"

    async def test_dispatch_with_service_method(self, insanic_application, monkeypatch, test_server):
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = Service('test')
        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        with service.grpc('monkey', 'v1', 'ApeService', 'GetChimpanzee') as method:
            request = method.request_type(id="1", include="sound")

            reply = await method(request)

            assert reply
            assert reply['extra'] == "woo woo ahh ahh"

    @pytest.mark.parametrize(
        "exception_type, expected_status",
        (
                ("uncaught_exception", Status.UNKNOWN),
                ("api_exception", Status.UNKNOWN),
                ("grpc_error", Status.INVALID_ARGUMENT)
        )
    )
    async def test_dispatch_with_error_on_server(self, insanic_application, monkeypatch, test_server,
                                                 exception_type, expected_status):
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = Service('test')
        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        with pytest.raises(GRPCError):
            try:
                with service.grpc('monkey', 'v1', 'MonkeyService', 'GetMonkey') as method:
                    request = method.request_type(id=exception_type)
                    reply = await method(request)
            except GRPCError as e:
                assert e.status == expected_status

                import traceback
                traceback.print_exc()
                raise

#
# _H2_TO_GRPC_STATUS_MAP = {
#     # 400
#     str(http.HTTPStatus.BAD_REQUEST.value): Status.INTERNAL,
#     # 401
#     str(http.HTTPStatus.UNAUTHORIZED.value): Status.UNAUTHENTICATED,
#     # 403
#     str(http.HTTPStatus.FORBIDDEN.value): Status.PERMISSION_DENIED,
#     # 404
#     str(http.HTTPStatus.NOT_FOUND.value): Status.UNIMPLEMENTED,
#     # 502
#     str(http.HTTPStatus.BAD_GATEWAY.value): Status.UNAVAILABLE,
#     # 503
#     str(http.HTTPStatus.SERVICE_UNAVAILABLE.value): Status.UNAVAILABLE,
#     # 504
#     str(http.HTTPStatus.GATEWAY_TIMEOUT.value): Status.UNAVAILABLE,
#     # 429
#     str(http.HTTPStatus.TOO_MANY_REQUESTS.value): Status.UNAVAILABLE,
# }
