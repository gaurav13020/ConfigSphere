from __future__ import annotations

from dataclasses import dataclass, field

from common.constants import ScopeLevel
from common.utils import compute_checksum, merge_payloads
from ..models import ConfigItem, ConfigVersion


@dataclass
class ResolvedLayer:
    """Metadata about a single participating scope layer."""
    scope_level: str
    config_item_id: int
    config_version_id: int
    version_number: int
    checksum: str
    key: str


@dataclass
class ResolvedConfig:
    """
    The final output of hierarchy resolution.

    Fields:
        payload         — merged effective configuration
        checksum        — SHA-256 of the final merged payload (for ETag)
        layers          — ordered list of scopes that contributed (lowest → highest precedence)
        scope_params    — the input scope used for resolution
    """
    payload: dict
    checksum: str
    layers: list[ResolvedLayer] = field(default_factory=list)
    scope_params: dict = field(default_factory=dict)


class HierarchyResolutionService:
    """
    Resolves the effective configuration for a given service scope.

    Resolution algorithm:
      1. Collect active config versions at each applicable scope level.
      2. Order layers by ascending precedence (global < region < group < service).
      3. Shallow-merge payloads: later layers override earlier ones.
      4. Return merged result with provenance metadata.

    Scope lookup strategy:
      - global:  ConfigItem where scope_level=global, key matches, global_name matches
      - region:  ConfigItem where scope_level=region, region_name matches
      - group:   ConfigItem where scope_level=group, group_name matches (if provided)
      - service: ConfigItem where scope_level=service, service_name matches

    For v1 we fetch ALL active config items for the given scope parameters, not
    just items with a specific key. This means the resolved payload is the union
    of ALL keys defined across the hierarchy for this scope — which is what a
    microservice expects when bootstrapping its configuration.

    This is intentional: a service requests its full effective config, not a
    single key at a time. Single-key lookup can be added later as a selector.
    """

    @staticmethod
    def resolve(
        service_name: str | None = None,
        region_name: str | None = None,
        group_name: str | None = None,
        global_name: str = "default",
    ) -> ResolvedConfig:
        layers_data = HierarchyResolutionService._collect_layers(
            service_name=service_name,
            region_name=region_name,
            group_name=group_name,
            global_name=global_name,
        )

        # layers_data is already sorted by ascending precedence
        payloads = [layer_payload for _, layer_payload in layers_data]
        metadata = [layer_meta for layer_meta, _ in layers_data]

        merged = merge_payloads(payloads)
        checksum = compute_checksum(merged)

        return ResolvedConfig(
            payload=merged,
            checksum=checksum,
            layers=metadata,
            scope_params={
                "global_name": global_name,
                "region_name": region_name,
                "group_name": group_name,
                "service_name": service_name,
            },
        )

    @staticmethod
    def _collect_layers(
        service_name: str | None,
        region_name: str | None,
        group_name: str | None,
        global_name: str,
    ) -> list[tuple[ResolvedLayer, dict]]:
        """
        Returns list of (ResolvedLayer, payload) tuples sorted by ascending precedence.
        Each tuple represents one active config item that participates in resolution.
        """
        results: list[tuple[int, ResolvedLayer, dict]] = []

        # Build scope lookup specs: (precedence, scope_level, filter_kwargs)
        scope_specs = [
            (
                ScopeLevel.PRECEDENCE[ScopeLevel.GLOBAL],
                ScopeLevel.GLOBAL,
                {"scope_level": ScopeLevel.GLOBAL, "global_name": global_name},
            ),
        ]

        if region_name:
            scope_specs.append((
                ScopeLevel.PRECEDENCE[ScopeLevel.REGION],
                ScopeLevel.REGION,
                {
                    "scope_level": ScopeLevel.REGION,
                    "global_name": global_name,
                    "region_name": region_name,
                },
            ))

        if region_name and group_name:
            scope_specs.append((
                ScopeLevel.PRECEDENCE[ScopeLevel.GROUP],
                ScopeLevel.GROUP,
                {
                    "scope_level": ScopeLevel.GROUP,
                    "global_name": global_name,
                    "region_name": region_name,
                    "group_name": group_name,
                },
            ))

        if service_name:
            scope_specs.append((
                ScopeLevel.PRECEDENCE[ScopeLevel.SERVICE],
                ScopeLevel.SERVICE,
                {
                    "scope_level": ScopeLevel.SERVICE,
                    "service_name": service_name,
                },
            ))

        for precedence, scope_level, filter_kwargs in scope_specs:
            active_items = (
                ConfigItem.objects.filter(**filter_kwargs, status="active")
                .exclude(active_version__isnull=True)
                .select_related("active_version")
            )

            for item in active_items:
                version: ConfigVersion = item.active_version
                layer_meta = ResolvedLayer(
                    scope_level=scope_level,
                    config_item_id=item.id,
                    config_version_id=version.id,
                    version_number=version.version_number,
                    checksum=version.checksum,
                    key=item.key,
                )
                results.append((precedence, layer_meta, version.payload))

        # Sort by precedence ascending so merge order is global → region → group → service
        results.sort(key=lambda x: x[0])

        return [(meta, payload) for _, meta, payload in results]
