import pytest

from interstellar.server import InterstellarServer


@pytest.fixture(autouse=True)
def reset_interstellar_server():
    yield

    InterstellarServer.reset()
