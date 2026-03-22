from __future__ import annotations

"""
Read-side query helpers (selectors).

Selectors are pure query functions — no writes, no side effects.
Views and other consumers call selectors for list/detail reads,
and services for writes/mutations.

This separation keeps query logic out of both views (fat views)
and service classes (which should focus on business rules).
"""

from django.db.models import QuerySet

from .models import ConfigItem, ConfigVersion


def get_config_items(
    scope_level: str | None = None,
    service_name: str | None = None,
    region_name: str | None = None,
    key: str | None = None,
) -> QuerySet[ConfigItem]:
    qs = ConfigItem.objects.select_related("schema", "active_version")
    if scope_level:
        qs = qs.filter(scope_level=scope_level)
    if service_name:
        qs = qs.filter(service_name=service_name)
    if region_name:
        qs = qs.filter(region_name=region_name)
    if key:
        qs = qs.filter(key=key)
    return qs


def get_config_versions_for_item(item_id: int) -> QuerySet[ConfigVersion]:
    return ConfigVersion.objects.filter(config_item_id=item_id).order_by("-version_number")
