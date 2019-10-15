import pytest

from insanic.conf import settings

from interstellar.client import InterstellarClient
from interstellar.server import InterstellarServer


class TestApplicationStart:

    @pytest.fixture()
    def init_interstellar_server(self, insanic_application, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', ["tests.blackhole.PlanetOfTheApes"], raising=False)
        InterstellarServer.init_app(insanic_application)

    @pytest.fixture()
    def init_interstellar_client(self, insanic_application):
        InterstellarClient.init_app(insanic_application)

    @pytest.fixture()
    def running_server(self, loop, insanic_application, test_server):
        return loop.run_until_complete(test_server(insanic_application))

    def test_interstellar_server(self, init_interstellar_server, running_server):
        assert running_server.is_running == True
        assert "interstellar_server" in running_server.app.initialized_plugins
        assert "interstellar_client" not in running_server.app.initialized_plugins

    def test_interstellar_client(self, init_interstellar_client, running_server):
        assert running_server.is_running == True
        assert "interstellar_client" in running_server.app.initialized_plugins
        assert "interstellar_server" not in running_server.app.initialized_plugins

    def test_interstellar_server_client(self, init_interstellar_server, init_interstellar_client, running_server):
        assert running_server.is_running == True
        assert "interstellar_client" in running_server.app.initialized_plugins
        assert "interstellar_server" in running_server.app.initialized_plugins
