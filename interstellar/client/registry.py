import importlib
import inspect

from collections import namedtuple
from typing import Collection

from grpclib.client import ServiceMethod

from insanic.exceptions import ImproperlyConfigured


def is_grpc_module(m):
    return inspect.ismodule(m) and m.__name__.startswith('grpc_')


def is_stub(m):
    return inspect.isclass(m) and not inspect.isabstract(m) and m.__name__.endswith('Stub')


def is_service_method(m):
    return isinstance(m, ServiceMethod)


GRPCStubMethod = namedtuple('GRPCStubMethod', ['stub_class', 'method'])


class StubRegistry():

    def __init__(self):
        self.stubs = {}
        self.service_methods = {}

    def register(self, packages: Collection[str]):
        """
        Loads stubs from modules

        :param namespace:
        :param packages:
        :return:
        """
        for package_name in packages:
            self._load_package(package_name)

    def _load_package(self, package_name: str) -> dict:
        """
        loads the package name

        :param package_name:
        :return: returns loaded package with stub_name: and method class
        """
        prefix, service, namespace = package_name.split('-')

        gp = importlib.import_module("_".join([prefix, service, namespace]))

        try:
            _, module = inspect.getmembers(gp, is_grpc_module)[0]
        except KeyError:
            raise RuntimeError(f'Error while loading {package_name}. '
                               f'Could not find module ending with "_grpc".')

        if service not in self.stubs:
            self.stubs[service] = {}

        if namespace not in self.stubs[service]:
            self.stubs[service][namespace] = {}

        for class_name, StubClass in inspect.getmembers(module, is_stub):
            self.stubs[service][namespace].update({class_name: StubClass})

            for stub_name, service_method in inspect.getmembers(StubClass(None), is_service_method):
                composite_key = (service, namespace, class_name)

                if composite_key not in self.service_methods:
                    self.service_methods[composite_key] = []

                self.service_methods[composite_key].append(stub_name)

    def get_stub(self, service_name, namespace, stub_name, service_method_name=None):
        if not service_name in self.stubs:
            raise ImproperlyConfigured(f"No packages have been installed for service {service_name}.")

        if not namespace in self.stubs[service_name]:
            raise ImproperlyConfigured(f"No packages with namespace {namespace} for service: {service_name}.")

        if not stub_name.endswith('Stub'):
            stub_name = f"{stub_name}Stub"

        if not stub_name in self.stubs[service_name][namespace]:
            raise ImproperlyConfigured(f"Stub, {stub_name}, does not exist for grpc-{service_name}-{namespace}."
                                       f"Please check the protobuf definition.")

        if service_method_name is not None:
            if service_method_name not in self.service_methods[(service_name, namespace, stub_name)]:
                raise ImproperlyConfigured(f"Service Method does not exist for stub, {stub_name}. "
                                           f"Please check the protobuf definition.")

        return self.stubs[service_name][namespace][stub_name]
