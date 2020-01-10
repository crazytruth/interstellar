import importlib
import inspect
import pkg_resources

from typing import Collection

from insanic.exceptions import ImproperlyConfigured

from interstellar.client.utils import is_grpc_module, is_service_method, is_stub


class StubRegistry():

    def __init__(self):
        self.stubs = {}
        self.service_methods = {}

    def scan_grpc_packages(self, service_name=None):

        all_grpc_client_packages = [p.key for p in pkg_resources.working_set if p.key.startswith('grpc-')]

        if service_name:
            # to include extra '-' at the end
            search_packages = ['grpc', service_name, '']
            search_for = "-".join(search_packages)
            return [p for p in all_grpc_client_packages if p.startswith(search_for)]
        else:
            return all_grpc_client_packages

    def register(self, packages: Collection[str]):
        """
        Loads stubs from modules

        :param namespace:
        :param packages:
        :return:
        """
        for package_name in packages:
            self._load_package(package_name)

    def _load_package(self, package_name: str) -> None:
        """
        loads the package name

        :param package_name:
        :return: returns loaded package with stub_name: and method class
        """

        package_info, version = package_name.rsplit('-', 1)
        package_info = package_info.split('-')
        service = package_info[1]
        namespace = package_info[2] if len(package_info) > 2 else service

        gp = importlib.import_module(package_name.replace('-', '_'))

        try:
            _, module = inspect.getmembers(gp, is_grpc_module)[0]
        except KeyError:
            raise RuntimeError(f'Error while loading {package_name}. '
                               f'Could not find module ending with "_grpc".')
        except IndexError as e:
            raise e

        if service not in self.stubs:
            self.stubs[service] = {}

        if namespace not in self.stubs[service]:
            self.stubs[service][namespace] = {}

        if version not in self.stubs[service][namespace]:
            self.stubs[service][namespace][version] = {}

        for class_name, StubClass in inspect.getmembers(module, is_stub):

            self.stubs[service][namespace][version].update({class_name: StubClass})

            for stub_name, service_method in inspect.getmembers(StubClass(None), is_service_method):
                composite_key = (service, namespace, version, class_name)

                if composite_key not in self.service_methods:
                    self.service_methods[composite_key] = []

                self.service_methods[composite_key].append(stub_name)

    def get_stub(self, service_name: str, namespace: str, version: str, stub_name: str, service_method_name: str = None):
        """

        :param service_name:
        :param namespace:
        :param stub_name:
        :param service_method_name:
        :return:
        """
        if not service_name in self.stubs:
            raise ImproperlyConfigured(f"No packages have been installed for service {service_name}.")

        if not namespace in self.stubs[service_name]:
            raise ImproperlyConfigured(f"No packages with namespace {namespace} for service: {service_name}.")

        if not stub_name.endswith('Stub'):
            stub_name = f"{stub_name}Stub"

        if not version in self.stubs[service_name][namespace]:
            package_name = f"grpc-{service_name}{f'-{namespace}' if service_name!=namespace else ''}"
            raise ImproperlyConfigured(f"Version does not exist for {package_name}. "
                                       f"Please check the protobuf definition.")

        if not stub_name in self.stubs[service_name][namespace][version]:
            raise ImproperlyConfigured(f"Stub, {stub_name}, does not exist for grpc-{service_name}-{namespace}."
                                       f"Please check the protobuf definition.")

        if service_method_name is not None:
            if service_method_name not in self.service_methods[(service_name, namespace, version, stub_name)]:
                raise ImproperlyConfigured(f"Service Method does not exist for stub, {stub_name}. "
                                           f"Please check the protobuf definition.")

        return self.stubs[service_name][namespace][version][stub_name]
