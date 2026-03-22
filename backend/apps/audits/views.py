from rest_framework import generics
from rest_framework.filters import OrderingFilter

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventListView(generics.ListAPIView):
    """Read-only paginated list of audit events. Filter by event_type or config_item."""

    serializer_class = AuditEventSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = AuditEvent.objects.all()
        event_type = self.request.query_params.get("event_type")
        config_item_id = self.request.query_params.get("config_item_id")

        if event_type:
            qs = qs.filter(event_type=event_type)
        if config_item_id:
            qs = qs.filter(config_item_id_ref=config_item_id)

        return qs
