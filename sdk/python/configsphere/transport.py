"""HTTP transport layer for communicating with the Config Server API."""

from datetime import datetime, timezone

import requests

from configsphere.errors import InvalidResponseError, ServerError, ServerUnreachableError
from configsphere.logger import get_logger
from configsphere.models import ConfigLayer, ResolvedConfig, SDKConfig, ScopeParams

logger = get_logger()


class HttpTransport:
    """Stateless HTTP transport — makes requests to the Config Server.

    No caching or retry logic; those responsibilities belong to the cache and poller.
    """

    def __init__(self, config: SDKConfig):
        self._base_url = config.server_url.rstrip("/")
        self._timeout = config.request_timeout_sec
        self._retry_on_status = config.retry_on_status
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"
        if config.auth_token:
            self._session.headers["Authorization"] = config.auth_token

    def fetch_resolved_config(
        self, scope: ScopeParams, etag: str | None
    ) -> tuple[ResolvedConfig | None, str | None]:
        """Fetch resolved config from the server.

        Returns:
            (ResolvedConfig, new_etag) on 200
            (None, existing_etag) on 304
        Raises:
            ServerError on 5xx
            ServerUnreachableError on connection failure
            InvalidResponseError on 4xx or malformed response
        """
        url = f"{self._base_url}/resolved-config/"
        params = self._build_query_params(scope)
        headers = {}
        if etag is not None:
            headers["If-None-Match"] = f'"{etag}"'

        logger.debug("Polling %s with params=%s etag=%s", url, params, etag)

        try:
            resp = self._session.get(
                url, params=params, headers=headers, timeout=self._timeout
            )
        except (requests.ConnectionError, ConnectionError) as exc:
            raise ServerUnreachableError(str(exc)) from exc
        except requests.Timeout as exc:
            raise ServerUnreachableError(f"Request timed out: {exc}") from exc

        if resp.status_code == 304:
            logger.debug("304 Not Modified — config unchanged")
            return None, etag

        if resp.status_code in self._retry_on_status:
            raise ServerError(resp.status_code, resp.text[:500])

        if resp.status_code >= 400:
            raise InvalidResponseError(
                f"Unexpected status {resp.status_code}: {resp.text[:500]}"
            )

        # Parse 200 response
        try:
            body = resp.json()
        except ValueError as exc:
            raise InvalidResponseError(f"Invalid JSON response: {exc}") from exc

        try:
            config = self._parse_response(body)
        except (KeyError, TypeError) as exc:
            raise InvalidResponseError(f"Malformed response body: {exc}") from exc

        new_etag = self._extract_etag(resp)
        logger.debug("Received config checksum=%s etag=%s", config.checksum, new_etag)
        return config, new_etag

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    @staticmethod
    def _build_query_params(scope: ScopeParams) -> dict[str, str]:
        params: dict[str, str] = {"global": scope.global_name}
        if scope.service_name:
            params["service"] = scope.service_name
        if scope.region_name:
            params["region"] = scope.region_name
        if scope.group_name:
            params["group"] = scope.group_name
        return params

    @staticmethod
    def _parse_response(body: dict) -> ResolvedConfig:
        scope_params_raw = body["scope_params"]
        scope_params = ScopeParams(
            service_name=scope_params_raw.get("service_name", ""),
            region_name=scope_params_raw.get("region_name"),
            group_name=scope_params_raw.get("group_name"),
            global_name=scope_params_raw.get("global_name", "default"),
        )
        layers = tuple(
            ConfigLayer(
                scope_level=layer["scope_level"],
                config_item_id=layer["config_item_id"],
                config_version_id=layer["config_version_id"],
                version_number=layer["version_number"],
                checksum=layer["checksum"],
                key=layer["key"],
            )
            for layer in body["layers"]
        )
        return ResolvedConfig(
            payload=body["payload"],
            checksum=body["checksum"],
            layers=layers,
            scope_params=scope_params,
            fetched_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _extract_etag(resp: requests.Response) -> str | None:
        etag = resp.headers.get("ETag")
        if etag:
            return etag.strip('"')
        return None
