import aiotask_context

from grpclib.events import listen, SendMessage, RecvMessage, SendRequest, RecvInitialMetadata, RecvTrailingMetadata

from insanic.conf import settings
from insanic.models import to_header_value
from insanic.services.utils import context_user, context_correlation_id
from insanic.utils.datetime import get_utc_datetime


async def interstellar_client_event_send_request(event: SendRequest) -> None:
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

    # inject correlation_id to headers
    correlation_id = context_correlation_id()
    event.metadata.update({settings.REQUEST_ID_HEADER_FIELD.lower(): correlation_id})

    event.metadata.update({"date": get_utc_datetime().strftime("%a, %d %b %y %T %z")})

    # inject ip
    remote_addr = aiotask_context.get(settings.TASK_CONTEXT_REMOTE_ADDR, "unknown")
    event.metadata.update({"ip": remote_addr})


async def interstellar_client_event_send_message(event: SendMessage) -> None:
    """
    https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.SendMessage

    :param event.message: (mutable) - message to send
    :return:
    """
    print('interstellar_client_event_send_message')


async def interstellar_client_event_recv_message(event: RecvMessage) -> None:
    """
    https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvMessage

    :param event.message: (mutable) - received message
    :return:
    """
    print('interstellar_client_event_recv_message')


async def interstellar_client_event_recv_initial_metadata(event: RecvInitialMetadata) -> None:
    """
    Dispatches after headers with initial metadata were received from the server

    https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvInitialMetadata

    :param event.metadata: (mutable) initial metadata
    :return:
    """
    print("interstellar_client_event_recv_initial_metadata")


async def interstellar_client_event_recv_trailing_metadata(event: RecvTrailingMetadata):
    """
    Dispatches after trailers with trailing metadata were received from the server

    https://grpclib.readthedocs.io/en/latest/events.html#grpclib.events.RecvTrailingMetadata

    :param event.metadata: (mutable) trailing metadata
    :return:
    """
    print("interstellar_client_event_recv_trailing_metadata")


def attach_events(channel):
    # common events
    listen(channel, SendMessage, interstellar_client_event_send_message)
    listen(channel, RecvMessage, interstellar_client_event_recv_message)
    # client side events
    listen(channel, SendRequest, interstellar_client_event_send_request)
    listen(channel, RecvInitialMetadata, interstellar_client_event_recv_initial_metadata)
    listen(channel, RecvTrailingMetadata, interstellar_client_event_recv_trailing_metadata)

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
