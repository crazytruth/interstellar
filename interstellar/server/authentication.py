import jwt

from grpclib.exceptions import GRPCError, Status

from insanic.authentication.handlers import jwt_service_decode_handler
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

    def get_jwt_value(self):
        auth = self.metadata.get('authorization', b'').split()

        if not auth or str(auth[0].lower()) != self.auth_header_prefix:
            return None

        if len(auth) == 1:
            self._raise('No credentials provided.')
        elif len(auth) > 2:
            self._raise("Credentials should not contain spaces.")

        return {"token": auth[1]}

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

        jwt_value = self.get_jwt_value()
        if jwt_value is None:
            self._raise("Request token not found in request.")

        payload = self.try_decode_jwt(**jwt_value)

        service = RequestService(is_authenticated=True, **payload)

        if not service.is_valid:
            self._raise(f"Invalid request to {settings.SERVICE_NAME}")

        return user, service

    async def authentication_error_handler(self, stream):
        raise GRPCError(Status.UNAUTHENTICATED,
                        self.error_message if self.error_message else "Unknown Authorization Error.")

    def try_decode_jwt(self, **jwt_value):
        try:
            payload = jwt_service_decode_handler(**jwt_value)
        except jwt.DecodeError:
            self._raise("Error decoding signature.")
        except jwt.InvalidTokenError:
            self._raise("Invalid token.")
        else:
            return payload
