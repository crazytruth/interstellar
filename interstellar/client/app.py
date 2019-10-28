from functools import partialmethod

from insanic import Insanic
from insanic.conf import settings
from insanic.services import Service

from interstellar.abstracts import AbstractPlugin

from interstellar.client import config as client_config
from interstellar.client.registry import StubRegistry
from interstellar.client.services import grpc_interface

BIND_INTERFACE = "grpc"


class InterstellarClient(AbstractPlugin):
    plugin_name = "INTERSTELLAR_CLIENT"
    app = None
    registry = StubRegistry()

    @classmethod
    def init_app(cls, app: Insanic):
        """
        Initializes client side functionality

        :param app:
        :return:
        """

        # load client specific interstellar configs
        cls.load_config(settings, client_config)
        cls.bind_grpc_interface()
        cls.client_registration()
        super().init_app(app)

    @classmethod
    def client_registration(cls):
        for service in settings.SERVICE_CONNECTIONS:
            packages = cls.registry.scan_grpc_packages(service)
            #     attach stubs to service object
            cls.registry.register(packages)

    @classmethod
    def bind_grpc_interface(cls):
        # setattr(Service, BIND_INTERFACE, partial(grpc_interface, registry=cls.registry))
        Service.grpc = partialmethod(grpc_interface, registry=cls.registry)

    @classmethod
    def unbind_grpc_interface(cls):
        delattr(Service, BIND_INTERFACE)
