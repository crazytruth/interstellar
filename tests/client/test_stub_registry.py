from grpclib.client import ServiceMethod

from interstellar.client.registry import StubRegistry


class TestStubRegistry:

    def test_stub_registry_init(self):
        registry = StubRegistry()
        assert registry.stubs == {}

    def test_stub_register(self):
        registry = StubRegistry()

        registry.register(['grpc-test-monkey'])

        assert "test" in registry.stubs
        assert "monkey" in registry.stubs['test']

    def test_get_stub_class(self):
        registry = StubRegistry()
        registry.register(['grpc-test-monkey'])

        stub = registry.get_stub('test', 'monkey', 'ApeService')

        assert stub
        assert stub.__name__.endswith('Stub')

    def test_get_stub_method(self):
        registry = StubRegistry()
        registry.register(['grpc-test-monkey'])

        stub = registry.get_stub('test', 'monkey', 'ApeService', 'GetChimpanzee')

        assert stub
        assert stub.__name__.endswith('Stub')
