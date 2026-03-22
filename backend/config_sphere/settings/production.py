from .base import *  # noqa: F401, F403

DEBUG = False

# In production, set ALLOWED_HOSTS via environment
import os  # noqa: E402

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
