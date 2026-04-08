from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class AuthServiceError(Exception):
    pass


class OAuthError(AuthServiceError):
    pass


class TokenExpiredError(AuthServiceError):
    pass


class TokenInvalidError(AuthServiceError):
    pass


def custom_exception_handler(exc, context):
    if isinstance(exc, OAuthError):
        return Response(
            {"error": "oauth_error", "detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, (TokenExpiredError, TokenInvalidError)):
        return Response(
            {"error": "authentication_error", "detail": str(exc)},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return exception_handler(exc, context)
