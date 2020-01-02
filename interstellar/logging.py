import logging  # pragma: no cover
import sys

from insanic.log import get_log_level, get_log_queue
from insanic.log.formatters import JSONFormatter

from insanic.scopes import is_docker


def get_formatter(type='json'):
    if type == "json":
        default_formatter = JSONFormatter(
            fmt={
                "level": "%(levelname)s",
                "hostname": "%(hostname)s",
                "where": "%(module)s.%(funcName)s",
                "ts": "%(asctime)s",
                "message": "%(message)s",
                "status": "%(status)s",
                "name": "%(name)s",
                "service": "%(service)s",
                "environment": "%(environment)s",
                "insanic_version": "%(insanic_version)s",
                "service_version": "%(service_version)s",
                "correlation_id": "%(correlation_id)s",
                "exc_text": "%(exc_text)s", "request_service": "%(request_service)s",
                "method": "%(method)s",
                "path": "%(path)s",
                "grpc_status": "%(grpc_status)s",
                "stream_id": "%(stream_id)s"
            },
            datefmt="%Y-%m-%dT%H:%M:%S.%%(msecs)d%z"
        )
    else:
        default_formatter = logging.Formatter(
            fmt="%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: GRPC "
            # "%(cardinality)s "
                "%(scheme)s://%(host)s%(path)s %(message)s %(status)s|%(grpc_status)s",
            datefmt="[%Y-%m-%d %H:%M:%S %z]"
        )
    return default_formatter


def get_handler():
    return logging.StreamHandler(sys.stdout)


# def get_queue_handler(*handlers):
#     from insanic.log.handlers import QueueListenerHandler
#     return QueueListenerHandler(handlers, queue=get_log_queue('interstellar'))


handler = get_handler()
handler.setFormatter(get_formatter("json" if is_docker else "generic"))
# queue_handler = get_queue_handler(handler)

interstellar_access_log = logging.getLogger('interstellar.access')  # pragma: no cover
interstellar_access_log.setLevel(get_log_level())
# interstellar_access_log.addHandler(queue_handler)

interstellar_access_log.addHandler(handler)
