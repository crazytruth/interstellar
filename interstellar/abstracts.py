import logging

from abc import ABC, abstractmethod

from insanic.log import logger

try:
    from insanic.abstracts import AbstractPlugin
except ImportError:

    class AbstractPlugin(ABC):

        config_imported = False

        @classmethod
        @abstractmethod
        def init_app(cls, app):
            cls.app = app
            app.plugin_initialized(cls.plugin_name.lower(), cls)

        @classmethod
        def logger(cls, level, message, *args, **kwargs):
            """

            :param level: either int or case insensitive string representation of log level
                possible inputs: info, debug, CRITICAL, FATAL, ERROR, WARN, WARNING
            :param message:
            :param args:
            :param kwargs:
            :return:
            """
            if not isinstance(level, int):
                log_level = logging._nameToLevel.get(level.upper(), None)

                if log_level is None:
                    if logger.raiseExceptions:
                        raise TypeError(
                            "Unable to resolve level. Must be one of {}.".format(
                                ", ".join(logging._nameToLevel.keys())))
                    else:
                        return
            else:
                log_level = level

            message = message if message.startswith(f'[{cls.plugin_name}]') else f"[{cls.plugin_name}] {message}"

            logger.log(log_level, message, *args, **kwargs)

        @classmethod
        def load_config(cls, settings_object, config):
            if not cls.config_imported:
                cls._load_config(settings_object, config)
                cls.config_imported = True

        @classmethod
        def _load_config(self, settings_object, config):
            for c in dir(config):
                if c.isupper() and not hasattr(settings_object, c):
                    conf = getattr(config, c)
                    setattr(settings_object, c, conf)
