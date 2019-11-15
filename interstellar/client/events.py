import aiotask_context

from functools import partial
from grpclib.events import listen, SendMessage, RecvMessage, SendRequest, RecvInitialMetadata, RecvTrailingMetadata

from insanic.conf import settings
from insanic.models import to_header_value, RequestService
from insanic.services.utils import context_user, context_correlation_id
from insanic.utils.datetime import get_utc_datetime

from insanic.scopes import get_my_ip


async def interstellar_client_event_send_request(event: SendRequest, service_name: str) -> None:
    """
    https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.SendRequest

    :param event:
    :param event.metadata: (mutable) - invocation metadata
    :param event.method_name: (read_only) - RPC's method name
    :param event.deadline: (read-only) - request's Deadline
    :param event.content_type: (read-only) - request's content type
    :return:
    """
    # inject user information to request headers
    user = context_user()
    event.metadata.update({settings.INTERNAL_REQUEST_USER_HEADER.lower(): to_header_value(user)})

    service = dict(
        source=settings.SERVICE_NAME,
        aud=service_name,
        source_ip=get_my_ip(),
        destination_version="0.0.1",
    )

    service = to_header_value(service)

    event.metadata.update({settings.INTERNAL_REQUEST_SERVICE_HEADER.lower(): service})

    # inject correlation_id to headers
    correlation_id = context_correlation_id()
    event.metadata.update({settings.REQUEST_ID_HEADER_FIELD.lower(): correlation_id})

    event.metadata.update({"date": get_utc_datetime().strftime("%a, %d %b %y %T %z")})

    # inject ip
    remote_addr = aiotask_context.get(settings.TASK_CONTEXT_REMOTE_ADDR, "unknown")
    event.metadata.update({"ip": remote_addr})


# async def interstellar_client_event_send_message(event: SendMessage) -> None:
#     """
#     https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.SendMessage
#
#     :param event.message: (mutable) - message to send
#     :return:
#     """
#     # print('interstellar_client_event_send_message')
#     pass


# async def interstellar_client_event_recv_message(event: RecvMessage) -> None:
#     """
#     https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvMessage
#
#     :param event.message: (mutable) - received message
#     :return:
#     """
#     # print('interstellar_client_event_recv_message')
#     pass

# async def interstellar_client_event_recv_initial_metadata(event: RecvInitialMetadata) -> None:
#     """
#     Dispatches after headers with initial metadata were received from the server
#
#     https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvInitialMetadata
#
#     :param event.metadata: (mutable) initial metadata
#     :return:
#     """
#     # print("interstellar_client_event_recv_initial_metadata")
#     pass


# async def interstellar_client_event_recv_trailing_metadata(event: RecvTrailingMetadata):
#     """
#     Dispatches after trailers with trailing metadata were received from the server
#
#     https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvTrailingMetadata
#
#     :param event.metadata: (mutable) trailing metadata
#     :return:
#     """
#     # print("interstellar_client_event_recv_trailing_metadata")
#     pass


def attach_events(channel, service_name=""):
    # common events
    # listen(channel, SendMessage, interstellar_client_event_send_message)
    # listen(channel, RecvMessage, interstellar_client_event_recv_message)
    # client side events
    listen(channel, SendRequest, partial(interstellar_client_event_send_request, service_name=service_name))
    # listen(channel, RecvInitialMetadata, interstellar_client_event_recv_initial_metadata)
    # listen(channel, RecvTrailingMetadata, interstellar_client_event_recv_trailing_metadata)

# events are called in this order
# interstellar_client_event_send_request
# interstellar_client_event_send_message
# interstellar_server_event_recv_request
# interstellar_server_event_recv_message
# actual handler
# interstellar_server_event_send_initial_metadata
# interstellar_server_event_send_message
# interstellar_server_event_send_trailing_metadata
# interstellar_client_event_recv_initial_metadata
# interstellar_client_event_recv_message
# interstellar_client_event_recv_trailing_metadata
