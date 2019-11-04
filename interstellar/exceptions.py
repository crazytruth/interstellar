from typing import Optional

from grpclib.const import Status
from grpclib.exceptions import GRPCError

from insanic.errors import GlobalErrorCodes


class InterstellarError(GRPCError):
    status = Status.UNKNOWN
    message = None
    error_code = GlobalErrorCodes.error_unspecified

    def __init__(
            self,
            status: Optional[Status] = None,
            message: Optional[str] = None,
            error_code: Optional[int] = None
    ) -> None:
        message = message or self.message
        status = status or self.status
        super().__init__(status, message)
        self.error_code = error_code or self.error_code


#
# @enum.unique
# class Status(enum.Enum):
#     """Predefined gRPC status codes represented as enum
#
#     See also: https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
#     """
#     #: The operation completed successfully
#     OK = 0
#     #: The operation was cancelled (typically by the caller)
#     CANCELLED = 1
#     #: Generic status to describe error when it can't be described using
#     #: other statuses
#     UNKNOWN = 2
#     #: Client specified an invalid argument
#     INVALID_ARGUMENT = 3
#     #: Deadline expired before operation could complete
#     DEADLINE_EXCEEDED = 4
#     #: Some requested entity was not found
#     NOT_FOUND = 5
#     #: Some entity that we attempted to create already exists
#     ALREADY_EXISTS = 6
#     #: The caller does not have permission to execute the specified operation
#     PERMISSION_DENIED = 7
#     #: Some resource has been exhausted, perhaps a per-user quota, or perhaps
#     #: the entire file system is out of space
#     RESOURCE_EXHAUSTED = 8
#     #: Operation was rejected because the system is not in a state required
#     #: for the operation's execution
#     FAILED_PRECONDITION = 9
#     #: The operation was aborted
#     ABORTED = 10
#     #: Operation was attempted past the valid range
#     OUT_OF_RANGE = 11
#     #: Operation is not implemented or not supported/enabled in this service
#     UNIMPLEMENTED = 12
#     #: Internal errors
#     INTERNAL = 13
#     #: The service is currently unavailable
#     UNAVAILABLE = 14
#     #: Unrecoverable data loss or corruption
#     DATA_LOSS = 15
#     #: The request does not have valid authentication credentials for the
#     #: operation
#     UNAUTHENTICATED = 16


class InvalidArgumentError(InterstellarError):
    status = Status.INVALID_ARGUMENT
    message = "Invalid Argument"
    error_code = GlobalErrorCodes.invalid_usage


class AlreadyExistsError(InterstellarError):
    status = Status.ALREADY_EXISTS
    message = "Already Exists"
    error_code = GlobalErrorCodes.invalid_usage


class PermissionDeniedError(InterstellarError):
    status = Status.PERMISSION_DENIED
    message = "Permission Denied"
    error_code = GlobalErrorCodes.permission_denied


class Unauthenticated(InterstellarError):
    status = Status.UNAUTHENTICATED
    message = "Unauthenticated"
    error_code = GlobalErrorCodes.authentication_credentials_missing
