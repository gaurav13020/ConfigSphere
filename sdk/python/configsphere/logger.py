"""SDK-scoped logger factory. Does NOT configure the root logger."""

import logging


def get_logger(name: str = "configsphere") -> logging.Logger:
    """Return a named logger for the SDK.

    Users control verbosity via:
        logging.getLogger("configsphere").setLevel(logging.DEBUG)
    """
    return logging.getLogger(name)
