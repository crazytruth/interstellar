from grpclib.exceptions import GRPCError, Status

from insanic.conf import settings
from insanic.models import User, RequestService


class GRPCAuthentication:

    def __init__(self, metadata: "MultiDict"):
        self.metadata = metadata
        self.error_message = None

    def _raise(self, message):
        self.error_message = message
        raise GRPCError(Status.UNAUTHENTICATED, self.error_message)

    @property
    def auth_header_prefix(self):
        return settings.JWT_SERVICE_AUTH['JWT_AUTH_HEADER_PREFIX'].lower()

    def get_service(self):
        try:
            request_service = self.metadata[settings.INTERNAL_REQUEST_SERVICE_HEADER.lower()]
        except KeyError:
            return None
        else:
            service_params = {}

            for f in request_service.split(';'):
                if f:
                    k, v = f.split('=')
                    service_params.update({k: v})
            return service_params

    def get_user(self):

        try:
            request_user = self.metadata[settings.INTERNAL_REQUEST_USER_HEADER.lower()]
        except KeyError:
            return None
        else:
            user_params = {"id": "", "level": -1}
            for f in request_user.split(';'):
                if f:
                    k, v = f.split('=')
                    user_params.update({k: v})
            return user_params

    def authenticate(self):

        user_params = self.get_user()
        if user_params is None:
            self._raise("Request user not found in request.")

        user = User(**user_params)

        service_params = self.get_service()
        if service_params is None:
            self._raise("Request service not found in request.")

        try:
            service = RequestService(is_authenticated=True, **service_params)
        except TypeError:
            self._raise("Invalid service payload.")

        if not service.is_valid:
            self._raise(f"Invalid request to {settings.SERVICE_NAME}")

        return user, service

    async def authentication_error_handler(self, stream):
        raise GRPCError(Status.UNAUTHENTICATED,
                        self.error_message if self.error_message else "Unknown Authorization Error.")

