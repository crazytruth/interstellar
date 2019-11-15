import pytest

from insanic import Insanic
from insanic.conf import settings
from insanic.services import ServiceRegistry

from interstellar.client.channels import ChannelPool

@pytest.fixture(autouse=True, scope="session")
def initialize_settings():
    settings.configure(MMT_ENV="test")


@pytest.fixture()
def insanic_application():
    app = Insanic('interstellar')
    yield app


@pytest.fixture(autouse=True)
def reset_registry():
    ServiceRegistry.reset()


@pytest.fixture(scope='function', autouse=True)
def stop_queue_listener_handler():
    yield

    from interstellar.logging import interstellar_access_log

    if hasattr(interstellar_access_log.handlers[0], '_listener'):
        if interstellar_access_log.handlers[0]._listener._thread:
            interstellar_access_log.handlers[0].stop()


@pytest.fixture(autouse=True)
def reset_channel_pool():
    yield
    ChannelPool.reset()
