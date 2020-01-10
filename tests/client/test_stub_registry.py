from grpclib.client import ServiceMethod

from interstellar.client.registry import StubRegistry


class TestStubRegistry:

    def test_stub_registry_init(self):
        registry = StubRegistry()
        assert registry.stubs == {}

    def test_stub_register(self):
        registry = StubRegistry()

        registry.register(['grpc-test-monkey-v1'])
        registry.register(['grpc-test-monkey-v2'])

        assert "test" in registry.stubs
        assert "monkey" in registry.stubs['test']
        assert 'v1' in registry.stubs['test']['monkey']
        assert 'v2' in registry.stubs['test']['monkey']

    def test_get_stub_class(self):
        registry = StubRegistry()
        registry.register(['grpc-test-monkey-v1'])

        stub = registry.get_stub('test', 'monkey', 'v1', 'ApeService')

        assert stub
        assert stub.__name__.endswith('Stub')

    def test_get_stub_method(self):
        registry = StubRegistry()
        registry.register(['grpc-test-monkey-v1'])

        stub = registry.get_stub('test', 'monkey', 'v1', 'ApeService', 'GetChimpanzee')

        assert stub
        assert stub.__name__.endswith('Stub')
