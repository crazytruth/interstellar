# -*- coding: utf-8 -*-

"""Console script for interstellar."""
import sys
import click
import logging
import pkg_resources

from interstellar.client.registry import StubRegistry

from grpclib.reflection.service import ServerReflection


@click.group()
def cli():
    logging.disable(logging.CRITICAL)
    sys.path.insert(0, '')


@cli.command()
@click.argument('package_name', nargs=-1)
def reflection(package_name=None):
    """This describes the services installed in the environment."""

    registry = StubRegistry()
    if package_name == ():
        click.echo("Installed Packages")
        click.echo("==================")
        # list all packages

        packages = registry.scan_grpc_packages()

        for i, p in enumerate(sorted(packages)):
            version = _get_package_version(p)
            click.echo(f"{i + 1}. {p}=={version}")
    else:
        # get reflection on packages defined
        click.echo("Reflecting")

        reflection = ServerReflection(_service_names=[])
        for p in package_name:
            packs = registry._load_package(p)

        for service_name, namespace_dict in registry.stubs.items():
            for namespace, stub_dict in namespace_dict.items():
                for stub_name, stub in stub_dict.items():
                    init_stub = stub(None)

                    for sm in registry.service_methods[(service_name, namespace, stub.__name__)]:
                        service_method = getattr(init_stub, sm)
                        click.echo(service_method.reply_type.DESCRIPTOR.file.serialized_pb)
                        click.echo(service_method.request_type.DESCRIPTOR.file.serialized_pb)


from grpclib.reflection.service import ServerReflection


def _get_package_version(package_name):
    for p in pkg_resources.working_set:
        if p.key == package_name:
            return p.version
