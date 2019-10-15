from grpclib.events import RecvRequest
from multidict import MultiDict

from insanic.conf import settings
from insanic.models import User, RequestService

from interstellar.server.authentication import GRPCAuthentication
from interstellar.server.events import interstellar_server_event_recv_request


class TestServerEvents:

    async def test_server_event_recv_request(self, monkeypatch):
        monkeypatch.setattr(settings, 'SERVICE_NAME', 'test', raising=False)

        event = RecvRequest(
            content_type="application/grpc+proto",
            deadline=None,
            method_name="/test.v1.ApeService/GetChimpanzee",
            method_func=None,
            metadata=MultiDict(
                {
                    settings.INTERNAL_REQUEST_USER_HEADER: 'id=;level=-1;is_authenticated=0',
                    "x-insanic-request-id": "unknown",
                    "authorization": "MSA eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
                                     ".eyJzb3VyY2UiOiJ0ZXN0IiwiYXVkIjoidGVzdCI"
                                     "sInNvdXJjZV9pcCI6IjE5Mi4xNjguMi45OSIsImR"
                                     "lc3RpbmF0aW9uX3ZlcnNpb24iOiIwLjAuMSJ9.jA"
                                     "u9Im6JkQaeM_4ZhfIJVBod7Vhos-rw3EgUl7S2B6U",
                    "date": 'Fri, 11 Oct 19 11:59:16 +0000',
                    "ip": "a"
                }
            )
        )

        await interstellar_server_event_recv_request(event)

        assert "auth" in event.metadata
        assert isinstance(event.metadata['auth'], GRPCAuthentication)
        assert event.metadata['auth'].error_message is None, event.metadata['auth'].error_message

        assert settings.INTERSTELLAR_SERVER_METADATA_USER in event.metadata
        assert isinstance(event.metadata[settings.INTERSTELLAR_SERVER_METADATA_USER], User)

        assert settings.INTERSTELLAR_SERVER_METADATA_SERVICE in event.metadata
        assert isinstance(event.metadata[settings.INTERSTELLAR_SERVER_METADATA_SERVICE], RequestService)
