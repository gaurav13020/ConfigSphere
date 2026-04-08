from django.urls import path
from apps.approvals.views import ApproveView, JiraWebhookView, RejectView

urlpatterns = [
    path("approvals/<int:pk>/approve/", ApproveView.as_view(), name="approval-approve"),
    path("approvals/<int:pk>/reject/", RejectView.as_view(), name="approval-reject"),
    path("webhooks/jira/", JiraWebhookView.as_view(), name="jira-webhook"),
]
