import aiotask_context
import asyncio
import pytest
import uuid

from multidict import MultiDict

from grpclib.events import listen, SendRequest

from insanic import Insanic
from insanic.conf import settings
from insanic.models import to_header_value, User, AnonymousUser
from insanic.services import Service
from insanic.services.utils import context_user

from interstellar.client import InterstellarClient
from interstellar.client.events import interstellar_client_event_send_request
from interstellar.server import InterstellarServer


class TestClientEvents:

    @pytest.fixture(autouse=True)
    def set_task_factory(self, loop):
        loop.set_task_factory(aiotask_context.chainmap_task_factory)

    @pytest.fixture()
    def test_server(self, test_server, loop, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ['tests.blackhole.PlanetOfTheApes'], raising=False)
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVER_PORT_DELTA', 1, raising=False)

        server = Insanic('test')
        InterstellarServer.init_app(server)

        return loop.run_until_complete(test_server(server))

    @pytest.mark.parametrize(
        'request_user',
        (AnonymousUser,
         User(id=uuid.uuid4().hex, level=100, is_authenticated=True))

    )
    async def test_send_request(self, loop, request_user, insanic_application):
        InterstellarClient.init_app(insanic_application)

        correlation_id = uuid.uuid4().hex

        aiotask_context.set(settings.TASK_CONTEXT_CORRELATION_ID, correlation_id)
        aiotask_context.set(settings.TASK_CONTEXT_REQUEST_USER, request_user)

        event = SendRequest(
            method_name="test",
            deadline=None,
            content_type="application/grpc+proto",
            metadata=MultiDict()
        )

        await interstellar_client_event_send_request(event, "some_service")

        assert settings.INTERNAL_REQUEST_USER_HEADER.lower() in event.metadata
        assert event.metadata[settings.INTERNAL_REQUEST_USER_HEADER.lower()] == to_header_value(context_user())

        assert settings.REQUEST_ID_HEADER_FIELD.lower() in event.metadata
        assert event.metadata[settings.REQUEST_ID_HEADER_FIELD.lower()] == correlation_id

        assert "date" in event.metadata
        assert "ip" in event.metadata


