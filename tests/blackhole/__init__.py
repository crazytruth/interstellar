from grpclib.exceptions import GRPCError

from insanic.exceptions import APIException

from interstellar.exceptions import InvalidArgumentError

from grpc_test_monkey.monkey_grpc import ApeServiceBase, MonkeyServiceBase
from grpc_test_monkey.monkey_pb2 import ApeResponse, MonkeyResponse


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


class PlanetOfTheMonkeys(MonkeyServiceBase):

    async def GetMonkey(self,
                        stream: 'grpclib.server.Stream[grpc_test_monkey.monkey_pb2.MonkeyRequest, grpc_test_monkey.monkey_pb2.MonkeyResponse]'):

        request = await stream.recv_message()

        if request.id == "uncaught_exception":
            raise Exception("Something Broke")
        elif request.id == "api_exception":
            raise APIException("help")
        elif request.id == "grpc_error":
            raise InvalidArgumentError(message="bad bad")

        response = MonkeyResponse()
        await stream.send_message(response)
