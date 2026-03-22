import dataclasses

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audits.services import AuditService
from common.constants import AuditEventType
from common.exceptions import NotFoundError
from .models import ConfigItem, ConfigVersion
from .selectors import get_config_items, get_config_versions_for_item
from .serializers import (
    ConfigItemCreateSerializer,
    ConfigItemSerializer,
    ConfigVersionCreateSerializer,
    ConfigVersionSerializer,
    ResolvedConfigSerializer,
)
from .services import (
    ActivationService,
    ConfigItemService,
    ConfigVersionService,
    HierarchyResolutionService,
)


# ── ConfigItem ───────────────────────────────────────────────────────────────

class ConfigItemListCreateView(APIView):
    def get(self, request):
        items = get_config_items(
            scope_level=request.query_params.get("scope_level"),
            service_name=request.query_params.get("service_name"),
            region_name=request.query_params.get("region_name"),
            key=request.query_params.get("key"),
        )
        return Response(ConfigItemSerializer(items, many=True).data)

    def post(self, request):
        serializer = ConfigItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        item = ConfigItemService.create(
            key=d["key"],
            scope_level=d["scope_level"],
            global_name=d.get("global_name", "default"),
            region_name=d.get("region_name"),
            group_name=d.get("group_name"),
            service_name=d.get("service_name"),
            schema_id=d.get("schema_id"),
            description=d.get("description", ""),
            created_by=d.get("created_by"),
        )
        return Response(ConfigItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ConfigItemDetailView(APIView):
    def get(self, request, pk):
        try:
            item = ConfigItem.objects.select_related("schema", "active_version").get(pk=pk)
        except ConfigItem.DoesNotExist:
            raise NotFoundError(f"ConfigItem with id={pk} does not exist.")
        return Response(ConfigItemSerializer(item).data)


# ── ConfigVersion ────────────────────────────────────────────────────────────

class ConfigVersionListCreateView(APIView):
    """
    GET  /api/v1/config-items/{id}/versions/  — list versions for an item
    POST /api/v1/config-items/{id}/versions/  — create a new version
    """

    def get(self, request, item_pk):
        versions = get_config_versions_for_item(item_pk)
        return Response(ConfigVersionSerializer(versions, many=True).data)

    def post(self, request, item_pk):
        serializer = ConfigVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        version = ConfigVersionService.create(
            config_item_id=item_pk,
            payload=d["payload"],
            change_summary=d.get("change_summary", ""),
            created_by=d.get("created_by"),
        )
        return Response(ConfigVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class ConfigVersionDetailView(APIView):
    def get(self, request, pk):
        try:
            version = ConfigVersion.objects.select_related("config_item").get(pk=pk)
        except ConfigVersion.DoesNotExist:
            raise NotFoundError(f"ConfigVersion with id={pk} does not exist.")
        return Response(ConfigVersionSerializer(version).data)


# ── Activation ───────────────────────────────────────────────────────────────

class ActivateConfigVersionView(APIView):
    """
    POST /api/v1/config-versions/{id}/activate/
    Body: { "actor": "optional-username" }
    """

    def post(self, request, pk):
        actor = request.data.get("actor")
        version = ActivationService.activate(version_id=pk, actor=actor)
        return Response(ConfigVersionSerializer(version).data)


# ── Resolved config ──────────────────────────────────────────────────────────

class ResolvedConfigView(APIView):
    """
    GET /api/v1/resolved-config/?service=payment&region=us-west&group=checkout&global=default

    Returns the merged effective configuration for a given scope.
    Supports ETag via checksum in response — clients can send If-None-Match later.
    """

    def get(self, request):
        service_name = request.query_params.get("service")
        region_name = request.query_params.get("region")
        group_name = request.query_params.get("group")
        global_name = request.query_params.get("global", "default")

        resolved = HierarchyResolutionService.resolve(
            service_name=service_name,
            region_name=region_name,
            group_name=group_name,
            global_name=global_name,
        )

        # Lightweight audit — only log service-level fetches to avoid noise
        if service_name:
            AuditService.record(
                event_type=AuditEventType.RESOLVED_CONFIG_FETCHED,
                metadata={
                    "service": service_name,
                    "region": region_name,
                    "group": group_name,
                    "checksum": resolved.checksum,
                },
            )

        # Convert dataclass to dict for serialization
        resolved_dict = {
            "payload": resolved.payload,
            "checksum": resolved.checksum,
            "layers": [dataclasses.asdict(layer) for layer in resolved.layers],
            "scope_params": resolved.scope_params,
        }

        serializer = ResolvedConfigSerializer(data=resolved_dict)
        serializer.is_valid()  # always valid — we built the data ourselves

        response = Response(serializer.data)
        response["ETag"] = f'"{resolved.checksum}"'
        return response
