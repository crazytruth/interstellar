import random

from insanic.conf import settings

from interstellar.client.events import attach_events
from interstellar.client.channels import InterstellarChannel


class MetadataInjector:

    def __init__(self, func, token):
        self.func = func
        self.token = token

    def __getattr__(self, item):
        return getattr(self.func, item)

    def __call__(self, *args, **kwargs):
        metadata = kwargs.pop('metadata', {})
        if "authorization" not in metadata:
            metadata.update({"authorization": f"{settings.JWT_SERVICE_AUTH['JWT_AUTH_HEADER_PREFIX']} {self.token}"})
        return self.func(*args, **kwargs, metadata=metadata)


def grpc_interface(self, namespace, stub_name, service_method_name=None, *, registry):
    if not stub_name.endswith('Stub'):
        stub_name = f"{stub_name}Stub"

    return GRPCBindContext(
        registry,
        self,
        namespace,
        stub_name,
        service_method_name,
    )


class Channels:
    channels = {}

    @classmethod
    def get_channel(self, service_name, host, port):
        if len(self.channels.get(service_name, [])) < settings.INTERSTELLAR_CLIENT_CHANNEL_COUNT:
            if service_name not in self.channels:
                self.channels[service_name] = []
            channel = InterstellarChannel(host=host, port=port)
            attach_events(channel)
            self.channels[service_name].append(channel)
            return channel
        return random.choice(self.channels[service_name])


class GRPCBindContext:
    __slots__ = ('registry', 'service', 'namespace', 'stub_name', 'service_method_name', 'stub_class', 'stub',)


    def __init__(self, registry, service: 'Service', namespace: str, stub_name: str, service_method_name: str = None):
        self.registry = registry
        self.stub_name = stub_name
        self.service = service
        self.namespace = namespace
        self.service_method_name = service_method_name
        self.stub_class = registry.get_stub(service.service_name, namespace, stub_name, service_method_name)

    # def _wrap_service_authorization(self):
    #     for method in self.registry.service_methods[
    #         (
    #                 self.service.service_name,
    #                 self.namespace,
    #                 self.stub_name
    #         )
    #     ]:
    #         setattr(
    #             self.stub,
    #             method,
    #             MetadataInjector(
    #                 getattr(self.stub, method),
    #                 self.service.service_token
    #             )
    #         )

    def __enter__(self):
        channel = Channels.get_channel(self.service.service_name, self.service.host, self.service.port)

        self.stub = self.stub_class(channel)
        # self._wrap_service_authorization()

        if self.service_method_name:
            return getattr(self.stub, self.service_method_name)
        else:
            return self.stub

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
