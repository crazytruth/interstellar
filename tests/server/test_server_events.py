from grpclib.client import Channel

from insanic.conf import settings

from interstellar.server import InterstellarServer

from grpc_test_monkey.monkey_grpc import MonkeyServiceBase, MonkeyServiceStub
from grpc_test_monkey.monkey_pb2 import MonkeyResponse


class Planet(MonkeyServiceBase):

    async def GetMonkey(self, stream: 'grpclib.server.Stream[grpc_test_monkey.monkey_pb2.MonkeyRequest, '
                                      'grpc_test_monkey.monkey_pb2.MonkeyResponse]'):
        request = await stream.recv_message()

        response = MonkeyResponse(id=int(request.id), extra=request.monkey * 2)

        await stream.send_message(response)


class TestServerEvents:

    async def test_event_receive_message(self, insanic_application, unused_port, monkeypatch):
        monkeypatch.setattr(settings, 'INTERSTELLAR_SERVERS', [Planet], raising=False)

        InterstellarServer.init_app(insanic_application)

        await InterstellarServer.start('0.0.0.0', int(unused_port))

        channel = Channel('127.0.0.1', unused_port)

        stub = MonkeyServiceStub(channel)
        request = stub.GetMonkey.request_type(id="1", monkey="hello")
        try:
            response = await stub.GetMonkey(request)
        except:
            import traceback
            traceback.print_exc()

        assert response.id == 1
        assert response.extra == "hellohello"

        await InterstellarServer.stop()
