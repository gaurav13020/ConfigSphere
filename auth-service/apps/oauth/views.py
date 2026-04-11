import logging
import secrets

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.oauth.services import JiraOAuthService, JWTService
from apps.users.models import RefreshToken
from apps.users.services import UserSyncService
from common.exceptions import OAuthError, TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)

_oauth_svc = JiraOAuthService()
_jwt_svc = JWTService()
_user_sync_svc = UserSyncService()


def _set_refresh_cookie(response, jti: str):
    response.set_cookie(
        "refresh_token",
        jti,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRY_SECONDS,
    )


class JiraLoginView(APIView):
    """
    GET /api/v1/oauth/jira/login/
    Redirects the browser to the Atlassian OAuth consent screen.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state = secrets.token_urlsafe(32)
        request.session["oauth_state"] = state
        request.session.save()
        url = _oauth_svc.get_authorization_url(state)
        return redirect(url)


class JiraCallbackView(APIView):
    """
    GET /api/v1/oauth/jira/callback/
    Handles the Atlassian OAuth redirect, syncs the user, and issues tokens.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code", "")
        state = request.query_params.get("state", "")
        error = request.query_params.get("error", "")

        if error:
            logger.warning("OAuth error from Jira: %s", error)
            return redirect(
                f"{settings.FRONTEND_URL}/auth/error?reason={error}"
            )

        expected_state = request.session.get("oauth_state", "")
        if not secrets.compare_digest(state, expected_state):
            return redirect(
                f"{settings.FRONTEND_URL}/auth/error?reason=invalid_state"
            )

        try:
            tokens = _oauth_svc.exchange_code(code)
            access_token = tokens["access_token"]

            profile = _oauth_svc.get_user_profile(access_token)
            account_id = profile["accountId"]

            groups = _oauth_svc.get_user_groups(access_token, account_id)
            project_roles = _oauth_svc.get_user_project_roles(access_token, account_id)

            user = _user_sync_svc.sync_user(profile, groups, project_roles)
        except OAuthError as exc:
            logger.error("OAuth callback failed: %s", exc)
            return redirect(
                f"{settings.FRONTEND_URL}/auth/error?reason=oauth_failed"
            )

        jwt_token = _jwt_svc.issue_access_token(user)
        jti, _ = _jwt_svc.issue_refresh_token(user)
        logger.info("JWT issued for %s", user.email)

        response = redirect(
            f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
        )
        _set_refresh_cookie(response, jti)
        return response


class RefreshTokenView(APIView):
    """
    POST /api/v1/oauth/refresh/
    Rotates the refresh token and issues a new access token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        jti = request.COOKIES.get("refresh_token", "")
        if not jti:
            return Response(
                {"error": "authentication_error", "detail": "No refresh token provided."},
                status=401,
            )

        try:
            old_token = _jwt_svc.verify_refresh_token(jti)
        except (TokenExpiredError, TokenInvalidError) as exc:
            response = Response(
                {"error": "authentication_error", "detail": str(exc)}, status=401
            )
            response.delete_cookie("refresh_token")
            return response

        user = old_token.jira_user

        # Rotate: revoke old token before issuing new one
        old_token.revoked = True
        old_token.save(update_fields=["revoked"])

        new_jwt = _jwt_svc.issue_access_token(user)
        new_jti, _ = _jwt_svc.issue_refresh_token(user)

        response = Response({"access_token": new_jwt})
        _set_refresh_cookie(response, new_jti)
        return response


class LogoutView(APIView):
    """
    POST /api/v1/oauth/logout/
    Revokes all active refresh tokens for the current user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        jira_account_id = request.user.jira_account_id
        revoked_count = RefreshToken.objects.filter(
            jira_user__jira_account_id=jira_account_id,
            revoked=False,
        ).update(revoked=True)

        logger.info(
            "Logout: revoked %d refresh token(s) for %s",
            revoked_count,
            jira_account_id,
        )

        response = Response({"detail": "Logged out successfully."})
        response.delete_cookie("refresh_token")
        return response
