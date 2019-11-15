import pytest
import ujson as json

from grpclib.const import Status

from insanic import Insanic
from insanic.conf import settings
from insanic.loading import get_service

from interstellar.exceptions import InterstellarError
from interstellar.logging import get_formatter
from interstellar.client import InterstellarClient
from interstellar.server import InterstellarServer


class TestGRPCServer:
    @pytest.fixture()
    def test_server(self, test_server, loop, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ['tests.blackhole.PlanetOfTheApes',
                                                               'tests.blackhole.PlanetOfTheMonkeys'], raising=False)
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVER_PORT_DELTA', 1, raising=False)

        server = Insanic('test')
        InterstellarServer.init_app(server)

        return loop.run_until_complete(test_server(server))

    async def test_access_logging_on_success(self, insanic_application, monkeypatch, test_server, caplog):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ["tests.blackhole.PlanetOfTheApes"], raising=False)
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = get_service('test')

        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        with service.grpc('monkey', 'ApeService') as stub:
            request = stub.GetChimpanzee.request_type(id="1", include="sound")

            reply = await stub.GetChimpanzee(request)

            assert reply

        assert len(caplog.records) == 1

        generic_formatter = get_formatter('generic')

        generic_log_output = generic_formatter.format(caplog.records[0]).split()

        # example output
        # '[2019-11-12 22:33:50 +0900] - (interstellar.access)[INFO][127.0.0.1:59691]:
        # GRPC http://127.0.0.1:59691/test.v1.ApeService/GetChimpanzee  200|0'

        assert generic_log_output[0]
        assert generic_log_output[3] == "-"
        assert generic_log_output[4].startswith("(interstellar.access)[INFO][127.0.0.1")
        assert generic_log_output[5] == "GRPC"
        assert generic_log_output[6].endswith('/test.v1.ApeService/GetChimpanzee')
        assert generic_log_output[-1] == "200|0"

        json_formatter = get_formatter('json')

        json_log_output = json.loads(json_formatter.format(caplog.records[0]))

        assert list(json_log_output.keys()) == \
               ['correlation_id', 'environment', 'exc_text', 'grpc_status', 'hostname',
                'insanic_version', 'level', 'message', 'method', 'name', 'path',
                'request_service', 'service', 'service_version', 'status',
                'stream_id', 'ts', 'where']

    @pytest.mark.parametrize(
        "exception_type, expected_status, expected_message",
        (
                ("uncaught_exception", Status.UNKNOWN, 'Internal Server Error'),
                ("api_exception", Status.UNKNOWN, 'Internal Server Error'),
                ("grpc_error", Status.INVALID_ARGUMENT, 'bad bad')
        )
    )
    async def test_access_logging_on_error(self, insanic_application, monkeypatch, test_server,
                                           caplog, exception_type, expected_status, expected_message):

        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ["tests.blackhole.PlanetOfTheApes"], raising=False)
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)

        InterstellarClient.init_app(insanic_application)

        service = get_service('test')

        monkeypatch.setattr(service, 'host', test_server.host)
        monkeypatch.setattr(service, 'port', test_server.port + settings.INTERSTELLAR_SERVER_PORT_DELTA)

        try:
            with service.grpc('monkey', 'MonkeyService', 'GetMonkey') as method:
                request = method.request_type(id=exception_type)
                reply = await method(request)

                assert reply
        except InterstellarError as e:

            assert e.status == expected_status
            assert e.message == expected_message

            generic_formatter = get_formatter('generic')

            generic_log_output_lines = generic_formatter.format(caplog.records[-1]).split('\n')
            generic_log_output_access = generic_log_output_lines[0].split()
            assert generic_log_output_access[-1] == f"200|{expected_status.value}"
            # assert generic_log_output_lines[1].startswith('Traceback')
        else:
            assert False, "Didn't raise grpc error"
