import pytest

from grpclib.events import RecvRequest
from multidict import MultiDict

from insanic.conf import settings
from insanic.models import User, RequestService

from interstellar import config as common_config
from interstellar.server import InterstellarServer, config
from interstellar.server.authentication import GRPCAuthentication
from interstellar.server.events import interstellar_server_event_recv_request


class TestServerEvents:

    @pytest.fixture()
    def init_config(self):
        InterstellarServer._load_config(settings, common_config)
        InterstellarServer.load_config(settings, config)

    async def test_server_event_recv_request(self, monkeypatch, init_config):
        monkeypatch.setattr(settings, 'SERVICE_NAME', 'test', raising=False)
        # monkeypatch.setattr(settings, 'INTERNAL_REQUEST_SERVICE_HEADER', 'x-insanic-request-service', raising=False)

        event = RecvRequest(
            content_type="application/grpc+proto",
            deadline=None,
            method_name="/test.v1.ApeService/GetChimpanzee",
            method_func=None,
            metadata=MultiDict(
                {
                    settings.INTERNAL_REQUEST_USER_HEADER: 'id=;level=-1;is_authenticated=0',
                    "x-insanic-request-id": "unknown",
                    settings.INTERNAL_REQUEST_SERVICE_HEADER: "source=test;aud=test;source_ip=127.0.0.1;destination_version=0.0.1",
                    "date": 'Fri, 11 Oct 19 11:59:16 +0000',
                    "ip": "a"
                }
            )
        )

        await interstellar_server_event_recv_request(event)

        assert event.__interrupted__ is False

        assert settings.INTERSTELLAR_SERVER_METADATA_USER in event.metadata
        assert isinstance(event.metadata[settings.INTERSTELLAR_SERVER_METADATA_USER], User)

        assert settings.INTERSTELLAR_SERVER_METADATA_SERVICE in event.metadata
        assert isinstance(event.metadata[settings.INTERSTELLAR_SERVER_METADATA_SERVICE], RequestService)
