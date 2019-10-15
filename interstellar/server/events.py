from grpclib.events import RecvRequest, SendInitialMetadata, SendTrailingMetadata, SendMessage, RecvMessage, listen
from grpclib.exceptions import GRPCError, Status

from interstellar.server.authentication import GRPCAuthentication


async def interstellar_server_event_recv_request(event: RecvRequest):
    authentication = GRPCAuthentication(event.metadata)
    try:
        user, service = authentication.authenticate()
    except GRPCError as e:
        event.interrupt()
    else:
        event.metadata.update({"request_user": user})
        event.metadata.update({"request_service": service})
    finally:
        event.metadata.update({"auth": authentication})

    print("interstellar_server_event_recv_request")


async def interstellar_server_event_send_initial_metadata(event: SendInitialMetadata):
    print("interstellar_server_event_send_initial_metadata")


async def interstellar_server_event_send_trailing_metadata(event: SendTrailingMetadata):
    print("interstellar_server_event_send_trailing_metadata")


async def interstellar_server_event_send_message(event: SendMessage):
    print('interstellar_server_event_send_message')


async def interstellar_server_event_recv_message(event: RecvMessage):
    print('interstellar_server_event_recv_message')


def attach_events(server):
    listen(server, RecvRequest, interstellar_server_event_recv_request)
    listen(server, SendInitialMetadata, interstellar_server_event_send_initial_metadata)
    listen(server, SendTrailingMetadata, interstellar_server_event_send_trailing_metadata)
    listen(server, SendMessage, interstellar_server_event_send_message)
    listen(server, RecvMessage, interstellar_server_event_recv_message)

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
