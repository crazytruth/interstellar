from interstellar.exceptions import InterstellarError


class InterstellarAbort(InterstellarError):
    status = None

    def __init__(
            self,
            h2_status: int,
            grpc_status=None,
            grpc_message=None
    ) -> None:
        self.h2_status = h2_status
        super().__init__(status=grpc_status, message=grpc_message)
