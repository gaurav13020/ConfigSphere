import hashlib
import hmac
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approvals.models import ApprovalRequest
from apps.approvals.serializers import (
    ApprovalRequestSerializer,
    ReviewSerializer,
    SubmitForApprovalSerializer,
)
from apps.approvals.services import ApprovalService
from common.authentication import JiraJWTAuthentication
from common.exceptions import NotFoundError
from common.permissions import IsApprover, IsOperator, IsViewer

logger = logging.getLogger(__name__)


class SubmitForApprovalView(APIView):
    """
    POST /api/v1/config-versions/{id}/submit-for-approval/
    Submits a VALIDATED version for approval and opens a Jira ticket.
    Requires Operator role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsOperator]

    def post(self, request, pk):
        serializer = SubmitForApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor = getattr(request.user, "email", "unknown")
        approval = ApprovalService.submit(
            version_id=pk,
            submitted_by=actor,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(
            ApprovalRequestSerializer(approval).data,
            status=status.HTTP_201_CREATED,
        )


class ApprovalDetailView(APIView):
    """
    GET /api/v1/config-versions/{id}/approval/
    Returns the current approval status for a version.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsViewer]

    def get(self, request, pk):
        try:
            approval = ApprovalRequest.objects.get(config_version_id=pk)
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(f"No approval request found for version {pk}.")
        return Response(ApprovalRequestSerializer(approval).data)


class ApproveView(APIView):
    """
    POST /api/v1/approvals/{id}/approve/
    Manually approves a pending approval request.
    Requires Approver role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsApprover]

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor = getattr(request.user, "email", "unknown")
        approval = ApprovalService.approve(
            approval_id=pk,
            reviewed_by=actor,
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(ApprovalRequestSerializer(approval).data)


class RejectView(APIView):
    """
    POST /api/v1/approvals/{id}/reject/
    Rejects a pending approval request.
    Requires Approver role or above.
    """

    authentication_classes = [JiraJWTAuthentication]
    permission_classes = [IsApprover]

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor = getattr(request.user, "email", "unknown")
        approval = ApprovalService.reject(
            approval_id=pk,
            reviewed_by=actor,
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(ApprovalRequestSerializer(approval).data)


class JiraWebhookView(APIView):
    """
    POST /api/v1/webhooks/jira/?secret=<JIRA_WEBHOOK_SECRET>

    Receives Jira issue transition events and updates ApprovalRequest status.
    Security: shared secret token in query param (Jira Cloud does not support
    HMAC webhook signing natively).

    Configure in Jira:
      Project Settings → Automation → When: Issue transitioned
      Action: Send web request → POST https://<host>/api/v1/webhooks/jira/?secret=<secret>
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Validate shared secret
        provided = request.query_params.get("secret", "")
        expected = settings.JIRA_WEBHOOK_SECRET
        if not expected or not hmac.compare_digest(provided, expected):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data
        logger.debug("Jira webhook payload: %s", payload)

        # Extract issue ID and new status from the transition changelog
        issue = payload.get("issue", {})
        issue_id = issue.get("id", "")

        changelog = payload.get("changelog", {})
        new_status = ""
        for item in changelog.get("items", []):
            if item.get("field") == "status":
                new_status = item.get("toString", "")
                break

        if not issue_id or not new_status:
            logger.warning("Jira webhook missing issue id or status transition: %s", payload)
            return Response({"detail": "No actionable transition found."}, status=status.HTTP_200_OK)

        reviewer = issue.get("fields", {}).get("assignee", {}).get("emailAddress", "jira-webhook")
        ApprovalService.process_jira_webhook(
            issue_id=issue_id,
            new_status=new_status,
            reviewer=reviewer,
        )

        return Response({"detail": "Webhook processed."}, status=status.HTTP_200_OK)
