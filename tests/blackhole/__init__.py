from grpc_test_monkey.monkey_grpc import ApeServiceBase
from grpc_test_monkey.monkey_pb2 import ApeResponse


class PlanetOfTheApes(ApeServiceBase):

    async def GetChimpanzee(self,
                            stream: 'grpclib.server.Stream[grpc_test_monkey.monkey_pb2.ApeRequest, grpc_test_monkey.monkey_pb2.ApeResponse]'):
        request = await stream.recv_message()

        if request.include == "sound":
            response = ApeResponse(id=int(request.id), extra="woo woo ahh ahh")
        else:
            response = ApeResponse(id=int(request.id), extra="i don't know")

        await stream.send_message(response)

    async def GetGorilla(self,
                         stream: 'grpclib.server.Stream[grpc_test_monkey.monkey_pb2.ApeRequest, grpc_test_monkey.monkey_pb2.ApeResponse]'):
        request = await stream.recv_message()

        if request.include == "sound":
            response = ApeResponse(id=int(request.id), extra="raaahhh")
        else:
            response = ApeResponse(id=int(request.id), extra="i don't know")

        await stream.send_message(response)
