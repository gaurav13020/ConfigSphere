"""
Integration tests for the resolved-config API endpoint.

Tests hit the actual HTTP layer via Django's test client.
"""

import json

from django.test import TestCase
from django.urls import reverse

from apps.configs.services import ActivationService, ConfigItemService, ConfigVersionService
from common.constants import ScopeLevel


class TestResolvedConfigEndpoint(TestCase):

    def _create_active(self, key, scope_level, payload, **scope_kwargs):
        item = ConfigItemService.create(key=key, scope_level=scope_level, **scope_kwargs)
        version = ConfigVersionService.create(config_item_id=item.id, payload=payload)
        ActivationService.activate(version.id)
        return item

    def test_returns_200_with_empty_payload_for_unknown_service(self):
        url = reverse("resolved-config") + "?service=ghost"
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["payload"] == {}
        assert data["layers"] == []

    def test_returns_merged_payload_across_hierarchy(self):
        self._create_active("global_cfg", ScopeLevel.GLOBAL, {"timeout": 30, "retry": 3})
        self._create_active(
            "service_cfg",
            ScopeLevel.SERVICE,
            {"timeout": 5, "max_conn": 10},
            service_name="payment",
        )

        url = reverse("resolved-config") + "?service=payment"
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()

        assert data["payload"]["timeout"] == 5      # service overrides global
        assert data["payload"]["retry"] == 3        # from global, not overridden
        assert data["payload"]["max_conn"] == 10    # service-only key

    def test_etag_header_present_in_response(self):
        url = reverse("resolved-config") + "?service=any"
        response = self.client.get(url)
        assert "ETag" in response

    def test_checksum_in_response_matches_etag(self):
        self._create_active("cfg", ScopeLevel.GLOBAL, {"k": "v"})
        url = reverse("resolved-config")
        response = self.client.get(url)
        data = response.json()
        etag_value = response["ETag"].strip('"')
        assert data["checksum"] == etag_value

    def test_scope_params_reflected_in_response(self):
        url = reverse("resolved-config") + "?service=orders&region=us-east"
        response = self.client.get(url)
        data = response.json()
        assert data["scope_params"]["service_name"] == "orders"
        assert data["scope_params"]["region_name"] == "us-east"

    def test_layers_ordered_by_ascending_precedence(self):
        self._create_active("k", ScopeLevel.GLOBAL, {"a": 1})
        self._create_active("k", ScopeLevel.REGION, {"a": 2}, region_name="us-west")
        self._create_active("k", ScopeLevel.SERVICE, {"a": 3}, service_name="api")

        url = reverse("resolved-config") + "?service=api&region=us-west"
        response = self.client.get(url)
        data = response.json()

        scope_levels = [l["scope_level"] for l in data["layers"]]
        assert scope_levels == [ScopeLevel.GLOBAL, ScopeLevel.REGION, ScopeLevel.SERVICE]
