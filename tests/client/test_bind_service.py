import pytest

from grpclib.client import ServiceMethod

from insanic.conf import settings
from insanic.exceptions import ImproperlyConfigured
from insanic.services import Service

from interstellar.client import InterstellarClient


class TestBindService:

    @pytest.fixture(autouse=True)
    def clean_service_class(self):
        yield

        InterstellarClient.unbind_grpc_interface()

    async def test_bind_service(self, monkeypatch):
        monkeypatch.setattr(settings, 'SERVICE_CONNECTIONS', ['test', 'second'], raising=False)
        InterstellarClient.bind_grpc_interface()
        InterstellarClient.client_registration()

        service = Service('test')

        stub = service.grpc("monkey", "v1", "ApeService")
        assert stub

        service2 = Service("second")
        assert service2.grpc

    async def test_bind_after_service_object_init(self):
        service = Service('test')

        with pytest.raises(AttributeError):
            method = service.grpc

        InterstellarClient.bind_grpc_interface()

        with service.grpc("monkey", "v1", "ApeService") as stub:
            assert stub

        with service.grpc('monkey', "v1", 'ApeService', 'GetChimpanzee') as method:
            assert method
            assert isinstance(method, ServiceMethod)

    def test_bind_error(self):
        service = Service('test')

        InterstellarClient.bind_grpc_interface()

        # this should not exist
        with pytest.raises(TypeError):
            with service.grpc('primate') as stub:
                pass
        with pytest.raises(TypeError):
            with service.grpc('monkey', 'v1') as stub:
                pass

        # stub doesn't exist
        with pytest.raises(ImproperlyConfigured):
            with service.grpc('monkey', 'v1', 'PrimateService') as stub:
                assert stub

        # service method doesn't exist
        with pytest.raises(ImproperlyConfigured):
            with service.grpc('monkey', 'v1', 'ApeService', 'GetOrangutan') as method:
                assert method

        # service version doesn't exist
        with pytest.raises(ImproperlyConfigured):
            with service.grpc('monkey', "v3", 'ApeService', 'GetChimpanzee') as method:
                pass
