import os

from interstellar.client.channels import ChannelPool

def grpc_interface(self, namespace, version, stub_name, service_method_name=None, *, registry):
    if not stub_name.endswith('Stub'):
        stub_name = f"{stub_name}Stub"

    return GRPCBindContext(
        registry,
        self,
        namespace,
        version,
        stub_name,
        service_method_name,
    )

class GRPCBindContext:
    __slots__ = ('registry', 'service', 'namespace', 'stub_name', 'service_method_name', 'stub_class', 'stub',)

    def __init__(self, registry, service: 'Service', namespace: str, version: str, stub_name: str, service_method_name: str = None):
        self.registry = registry
        self.stub_name = stub_name
        self.service = service
        self.namespace = namespace
        self.service_method_name = service_method_name
        self.stub_class = registry.get_stub(service.service_name, namespace, version, stub_name, service_method_name)

    def __enter__(self):
        host = "0.0.0.0" if os.environ.get('MMT_ENV') == 'local' else self.service.host
        port = self.service.port + 1000
        channel = ChannelPool.get_channel(self.service.service_name, host, port)

        self.stub = self.stub_class(channel)

        if self.service_method_name:
            return getattr(self.stub, self.service_method_name)
        else:
            return self.stub

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
