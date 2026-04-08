import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
import requests
from django.conf import settings

from apps.users.models import JiraUser, RefreshToken
from common.exceptions import OAuthError, TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)

JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
JIRA_API_ME = "https://api.atlassian.com/me"
JIRA_ACCESSIBLE_RESOURCES = "https://api.atlassian.com/oauth/token/accessible-resources"


class JiraOAuthService:
    """Handles all communication with Atlassian OAuth 2.0 (3LO) endpoints."""

    def get_authorization_url(self, state: str) -> str:
        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.JIRA_CLIENT_ID,
            "scope": "read:me read:account offline_access read:jira-user",
            "redirect_uri": settings.JIRA_REDIRECT_URI,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
        return f"{JIRA_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        try:
            resp = requests.post(
                JIRA_TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "client_id": settings.JIRA_CLIENT_ID,
                    "client_secret": settings.JIRA_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.JIRA_REDIRECT_URI,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.error("Jira token exchange failed: %s", exc)
            raise OAuthError("Failed to exchange authorization code with Jira.") from exc

    def get_user_profile(self, access_token: str) -> dict:
        """
        Fetch the authenticated user's Atlassian profile and normalize to a
        consistent shape. The /me endpoint returns snake_case keys
        (account_id, name) while the Jira REST API uses camelCase
        (accountId, displayName) — we normalize to camelCase here.
        """
        try:
            resp = requests.get(
                JIRA_API_ME,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "accountId": data.get("account_id", data.get("accountId", "")),
                "email": data.get("email", ""),
                "displayName": data.get("name", data.get("displayName", "")),
                "picture": data.get("picture", ""),
            }
        except requests.RequestException as exc:
            logger.error("Jira /me fetch failed: %s", exc)
            raise OAuthError("Failed to fetch user profile from Jira.") from exc

    def _get_cloud_id(self, access_token: str) -> str:
        """
        OAuth 2.0 (3LO) tokens must call the Jira REST API via the Atlassian
        API gateway using a cloudId, not directly against the site URL.
        Returns the cloudId for the first accessible Jira resource.
        """
        resp = requests.get(
            JIRA_ACCESSIBLE_RESOURCES,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        resources = resp.json()
        if not resources:
            raise OAuthError("No accessible Jira resources found for this account.")
        return resources[0]["id"]

    def _jira_api(self, access_token: str, path: str, params: dict = None) -> requests.Response:
        """Make an authenticated call to the Jira REST API via the gateway."""
        cloud_id = self._get_cloud_id(access_token)
        return requests.get(
            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3{path}",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

    def get_user_groups(self, access_token: str, account_id: str) -> list[str]:
        """Return the list of Jira group names the user belongs to."""
        try:
            resp = self._jira_api(access_token, "/user/groups", {"accountId": account_id})
            resp.raise_for_status()
            return [g["name"] for g in resp.json()]
        except requests.RequestException as exc:
            logger.warning("Could not fetch Jira groups for %s: %s", account_id, exc)
            return []

    def get_user_project_roles(self, access_token: str, account_id: str) -> list[str]:
        """Return Jira project role names the user holds in the configured project."""
        try:
            resp = self._jira_api(
                access_token,
                f"/project/{settings.JIRA_PROJECT_KEY}/role",
            )
            resp.raise_for_status()
            role_urls: dict = resp.json()

            matched_roles = []
            cloud_id = self._get_cloud_id(access_token)
            headers = {"Authorization": f"Bearer {access_token}"}

            for role_name, role_url in role_urls.items():
                # role_url may be a site URL — rewrite to gateway URL
                if "atlassian.net" in role_url:
                    path = role_url.split("/rest/api/3", 1)[-1]
                    role_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3{path}"

                role_resp = requests.get(role_url, headers=headers, timeout=10)
                if role_resp.ok:
                    actors = role_resp.json().get("actors", [])
                    actor_ids = [
                        a.get("actorUser", {}).get("accountId")
                        for a in actors
                        if a.get("type") == "atlassian-user-role-actor"
                    ]
                    if account_id in actor_ids:
                        matched_roles.append(role_name)

            return matched_roles
        except requests.RequestException as exc:
            logger.warning("Could not fetch Jira project roles for %s: %s", account_id, exc)
            return []


class JWTService:
    """Issues and validates JWTs and server-side refresh tokens."""

    def issue_access_token(self, user: JiraUser) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "jira_account_id": user.jira_account_id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.configsphere_role,
            "iat": now,
            "exp": now + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRY_SECONDS),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def issue_refresh_token(self, user: JiraUser) -> tuple[str, RefreshToken]:
        """
        Creates a server-side RefreshToken record and returns its jti.
        The jti is what we store in the client's httpOnly cookie.
        """
        jti = str(uuid.uuid4())
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            seconds=settings.JWT_REFRESH_TOKEN_EXPIRY_SECONDS
        )
        token = RefreshToken.objects.create(
            jti=jti,
            jira_user=user,
            expires_at=expires_at,
        )
        return jti, token

    def verify_access_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Access token has expired.")
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"Invalid access token: {exc}") from exc

    def verify_refresh_token(self, jti: str) -> RefreshToken:
        try:
            token = RefreshToken.objects.select_related("jira_user").get(
                jti=jti, revoked=False
            )
        except RefreshToken.DoesNotExist:
            raise TokenInvalidError("Refresh token not found or already revoked.")

        if token.expires_at < datetime.now(tz=timezone.utc):
            token.revoked = True
            token.save(update_fields=["revoked"])
            raise TokenExpiredError("Refresh token has expired. Please log in again.")

        return token
