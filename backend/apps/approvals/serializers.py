from rest_framework import serializers
from apps.approvals.models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "config_version",
            "jira_issue_key",
            "jira_issue_url",
            "status",
            "submitted_by",
            "reviewed_by",
            "submission_notes",
            "review_comment",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = fields


class SubmitForApprovalSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")
