from grpclib.health.check import ServiceStatus
from grpclib.health.service import Health
from grpclib.server import Server

from insanic.app import Insanic
from insanic.conf import settings

from interstellar.abstracts import AbstractPlugin
from interstellar.server import config
from interstellar.utils import load_class


class InterstellarServer(AbstractPlugin):
    plugin_name = "INTERSTELLAR_SERVER"
    app = None
    # vocabulary beacon == server
    base_beacons = []
    warp_beacon = None
    health_beacons = None

    @classmethod
    def init_app(cls, app: Insanic):
        """
        Initializes application with grpc server functionality

        :param app: Instance of insanic application
        :return:
        """

        cls.load_config(settings, config)

        for s in app.config.INTERSTELLAR_SERVERS:
            if isinstance(s, str):
                klass = load_class(s)
            else:
                klass = s

            cls.base_beacons.append(klass())
            cls.logger('info', f"Loading {klass.__module__}.{klass.__name__} for GRPC serving.")

        if len(cls.base_beacons):
            # only need to initialize grpc servers if there are actual servers to run
            cls.health_beacons = {s: [ServiceStatus()] for s in cls.base_beacons}
            cls.warp_beacon = Server(cls.base_beacons + [Health(cls.health_beacons)])

            # attach start stop listeners
            cls.attach_listeners(app)
            # attach grpc server events
            cls.attach_grpc_server_events(app)
        else:
            cls.logger('warning', f"No GRPC Servers have been initialized.")

        super().init_app(app)

    @classmethod
    def attach_listeners(cls, app: Insanic):

        @app.listener('after_server_start')
        async def after_server_start_start_grpc(app, loop=None, **kwargs):
            if app.config.INTERSTELLAR_SERVER_ENABLED:
                await cls.start(loop=loop)
            else:
                cls.logger("info", f"GRPC_SERVE is turned off")

        @app.listener('before_server_stop')
        async def before_server_stop_stop_grpc(app, loop=None, **kwargs):
            await cls.stop()

    @classmethod
    def attach_grpc_server_events(cls, app):
        from interstellar.server.events import attach_events
        attach_events(cls.warp_beacon)

    @classmethod
    async def start(cls, host=None, port=None, *, reuse_port=True, reuse_address=True, loop=None):
        """
        Start grpc server

        :param host:
        :param port:
        :param reuse_port:
        :param reuse_address:
        :return:
        """

        cls._host = host or settings.INTERSTELLAR_SERVER_HOST
        cls._port = port \
                    or settings.INTERSTELLAR_SERVER_PORT \
                    or cls.app.config.SERVICE_PORT + cls.app.config.INTERSTELLAR_SERVER_PORT_DELTA

        if cls.warp_beacon:

            if loop:
                cls.warp_beacon._loop = loop

            await cls.warp_beacon.start(host=cls._host, port=cls._port, reuse_port=reuse_port,
                                        reuse_address=reuse_address)
            cls.logger('info', f"Serving GRPC from {cls._host}:{cls._port}")
        else:
            cls.logger('warning', f"Did not start GRPC server because server has not been initialized.")

    @classmethod
    async def stop(cls):
        """
        Gracefully stops grpc server

        :return:
        """
        from grpclib.utils import graceful_exit

        cls.logger('info', f"Closing GRPC.")
        if cls.warp_beacon is not None:
            cls.warp_beacon.close()
            await cls.warp_beacon.wait_closed()
        cls.logger('info', f"Closed GRPC.")

    @classmethod
    def reset(cls):
        cls.base_beacons = []
        cls.warp_beacon = None
        cls.health_beacons = None
        cls.app = None
        cls.config_imported = False


# keeping with protoss...

InterstellarWarpBeacon = InterstellarServer
