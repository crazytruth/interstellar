import pytest

from insanic import Insanic
from insanic.conf import settings


@pytest.fixture(autouse=True, scope="session")
def initialize_settings():
    settings.configure(MMT_ENV="test")


@pytest.fixture()
def insanic_application():
    app = Insanic('interstellar')
    yield app
