"""Exception hierarchy for the ConfigSphere SDK."""


class ConfigSphereError(Exception):
    """Base exception for all ConfigSphere SDK errors."""


class ServerUnreachableError(ConfigSphereError):
    """Raised when the config server cannot be reached (connection refused, DNS failure)."""


class ServerError(ConfigSphereError):
    """Raised when the server returns a 5xx response."""

    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Server returned {status_code}: {body}")


class InvalidResponseError(ConfigSphereError):
    """Raised when the server response is malformed or missing required fields."""


class ConfigNotAvailableError(ConfigSphereError):
    """Raised when cache is empty and server is unreachable (cold start failure)."""


class ClientClosedError(ConfigSphereError):
    """Raised when an operation is attempted after client.close()."""
