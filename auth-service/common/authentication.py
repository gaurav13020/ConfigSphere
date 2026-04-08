import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JiraTokenUser:
    """
    Lightweight user object built from validated JWT claims.
    Not a database model — avoids a DB round-trip on every request.
    """

    is_anonymous = False
    is_authenticated = True

    def __init__(self, payload: dict):
        self.jira_account_id = payload["jira_account_id"]
        self.email = payload["email"]
        self.display_name = payload["display_name"]
        self.role = payload["role"]
        self.jti = payload.get("jti", "")

    def __str__(self):
        return self.email


class JiraJWTAuthentication(BaseAuthentication):
    """
    Validates a Bearer JWT issued by the auth-service.
    Shared JWT_SECRET_KEY means no inter-service call is needed per request.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired. Please log in again.")
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}")

        user = JiraTokenUser(payload)
        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"
