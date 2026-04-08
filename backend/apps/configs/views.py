import dataclasses

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audits.services import AuditService
from common.authentication import JiraJWTAuthentication
from common.constants import AuditEventType, VersionStatus
from common.exceptions import NotFoundError
from common.permissions import IsAdmin, IsApprover, IsOperator, IsViewer
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
    SchemaValidationService,
)


# ── ConfigItem ───────────────────────────────────────────────────────────────

class ConfigItemListCreateView(APIView):
    authentication_classes = [JiraJWTAuthentication]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOperator()]
        return [IsViewer()]

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
    authentication_classes = [JiraJWTAuthentication]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdmin()]
        if self.request.method == "PUT":
            return [IsOperator()]
        return [IsViewer()]

    def get(self, request, pk):
        try:
            item = ConfigItem.objects.select_related("schema", "active_version").get(pk=pk)
        except ConfigItem.DoesNotExist:
            raise NotFoundError(f"ConfigItem with id={pk} does not exist.")
        return Response(ConfigItemSerializer(item).data)

    def put(self, request, pk):
        try:
            item = ConfigItem.objects.get(pk=pk)
        except ConfigItem.DoesNotExist:
            raise NotFoundError(f"ConfigItem with id={pk} does not exist.")
        
        serializer = ConfigItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        item.key = d.get("key", item.key)
        item.scope_level = d.get("scope_level", item.scope_level)
        item.global_name = d.get("global_name", item.global_name)
        item.description = d.get("description", item.description)
        
        # Set scope fields based on scope_level (use empty string for unused levels)
        if item.scope_level in ['region', 'group', 'service']:
            item.region_name = d.get("region_name", item.region_name)
        else:
            item.region_name = ""
            
        if item.scope_level in ['group', 'service']:
            item.group_name = d.get("group_name", item.group_name)
        else:
            item.group_name = ""
            
        if item.scope_level == 'service':
            item.service_name = d.get("service_name", item.service_name)
        else:
            item.service_name = ""
        
        if "schema_id" in d:
            item.schema_id = d["schema_id"]
        
        item.save()
        return Response(ConfigItemSerializer(item).data)

    def delete(self, request, pk):
        try:
            item = ConfigItem.objects.get(pk=pk)
        except ConfigItem.DoesNotExist:
            raise NotFoundError(f"ConfigItem with id={pk} does not exist.")
        
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── ConfigVersion ────────────────────────────────────────────────────────────

class ConfigVersionListCreateView(APIView):
    """
    GET  /api/v1/config-items/{id}/versions/  — list versions for an item
    POST /api/v1/config-items/{id}/versions/  — create a new version
    """

    authentication_classes = [JiraJWTAuthentication]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOperator()]
        return [IsViewer()]

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
    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsViewer]

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
    Requires Approver role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsApprover]

    def post(self, request, pk):
        # If an ApprovalRequest exists for this version it must be APPROVED
        from apps.approvals.models import ApprovalRequest, ApprovalStatus
        from common.exceptions import ActivationError
        try:
            approval = ApprovalRequest.objects.get(config_version_id=pk)
            if approval.status != ApprovalStatus.APPROVED:
                raise ActivationError(
                    f"Version has a pending approval request (status={approval.status}). "
                    f"It must be approved before activation. "
                    f"Jira: {approval.jira_issue_key or 'ticket not yet created'}"
                )
        except ApprovalRequest.DoesNotExist:
            pass  # No approval request — Approver can activate directly

        actor = getattr(request.user, "email", request.data.get("actor"))
        version = ActivationService.activate(version_id=pk, actor=actor)
        return Response(ConfigVersionSerializer(version).data)


class ValidateConfigVersionView(APIView):
    """
    POST /api/v1/config-versions/{id}/validate/
    Validates a DRAFT version and moves it to VALIDATED if validation passes.
    Requires Operator role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsOperator]

    def post(self, request, pk):
        try:
            version = ConfigVersion.objects.select_related("config_item", "config_item__schema").get(pk=pk)
        except ConfigVersion.DoesNotExist:
            raise NotFoundError(f"ConfigVersion with id={pk} does not exist.")

        actor = getattr(request.user, "email", request.data.get("actor"))
        
        # If already validated, just return success
        if version.status == VersionStatus.VALIDATED:
            return Response(ConfigVersionSerializer(version).data)
        
        # If not draft, cannot validate
        if version.status != VersionStatus.DRAFT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Version is {version.status}, not draft. Cannot validate.")
        
        # Validate the payload against schema
        if version.config_item.schema is not None:
            valid, error_msg = SchemaValidationService.validate(version.payload, version.config_item.schema)
            if valid:
                version.status = VersionStatus.VALIDATED
                version.validation_error = ""
                version.save(update_fields=['status', 'validation_error'])
                
                AuditService.record(
                    event_type=AuditEventType.VALIDATION_PASSED,
                    actor=actor,
                    config_item_id=version.config_item_id,
                    config_version_id=version.id,
                    metadata={"version_number": version.version_number},
                )
            else:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(f"Validation failed: {error_msg}")
        else:
            # No schema, just move to validated
            version.status = VersionStatus.VALIDATED
            version.save(update_fields=['status'])
        
        return Response(ConfigVersionSerializer(version).data)


class ArchiveConfigVersionView(APIView):
    """
    POST /api/v1/config-versions/{id}/archive/
    Archives an ACTIVE version. Requires Approver role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsApprover]

    def post(self, request, pk):
        try:
            version = ConfigVersion.objects.select_related("config_item").get(pk=pk)
        except ConfigVersion.DoesNotExist:
            raise NotFoundError(f"ConfigVersion with id={pk} does not exist.")

        actor = getattr(request.user, "email", request.data.get("actor"))
        
        if version.status != VersionStatus.ACTIVE:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Version is {version.status}, not active. Cannot archive.")
        
        version.status = VersionStatus.ARCHIVED
        version.save(update_fields=['status'])
        
        AuditService.record(
            event_type=AuditEventType.VERSION_ARCHIVED,
            actor=actor,
            config_item_id=version.config_item_id,
            config_version_id=version.id,
            metadata={"version_number": version.version_number},
        )
        
        return Response(ConfigVersionSerializer(version).data)


# ── Resolved config ──────────────────────────────────────────────────────────

class ResolvedConfigView(APIView):
    """
    GET /api/v1/resolved-config/?service=payment&region=us-west&group=checkout&global=default

    Returns the merged effective configuration for a given scope.
    Supports ETag via checksum in response — clients can send If-None-Match later.
    Requires Viewer role or above (microservices use a service-account JWT).
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsViewer]

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
