import inspect

from grpclib.client import ServiceMethod


def is_grpc_module(m):
    return inspect.ismodule(m) and m.__name__.startswith('grpc_')


def is_stub(m):
    return inspect.isclass(m) and not inspect.isabstract(m) and m.__name__.endswith('Stub')


def is_service_method(m):
    return isinstance(m, ServiceMethod)
