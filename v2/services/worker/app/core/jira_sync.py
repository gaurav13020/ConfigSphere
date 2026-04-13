from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.constants import ChangeRequestStatus, SyncStatus
from configsphere_shared.models import (
    ConfigChangeRequest,
    ConfigNode,
    JiraSyncEvent,
    Service,
    User,
)
from .jira_client import JiraClient

logger = logging.getLogger(__name__)


class JiraSyncProcessor:
    def __init__(self, db: Session, jira: JiraClient) -> None:
        self.db = db
        self.jira = jira

    def process_event(self, sync_event_id: uuid.UUID) -> None:
        event = self.db.scalar(
            select(JiraSyncEvent).where(JiraSyncEvent.sync_event_id == sync_event_id)
        )
        if not event:
            logger.warning("JiraSyncEvent %s not found", sync_event_id)
            return
        if event.sync_status != SyncStatus.PENDING:
            logger.info("JiraSyncEvent %s already processed (%s)", sync_event_id, event.sync_status)
            return

        try:
            if event.event_type == "CREATE_ISSUE":
                self._handle_create_issue(event)
            elif event.event_type == "UPDATE_STATUS":
                self._handle_update_status(event)
            else:
                logger.warning("Unknown event type %s for sync event %s", event.event_type, sync_event_id)
                return

            event.sync_status = SyncStatus.SUCCESS
            self.db.add(event)
            self.db.commit()
        except Exception:
            logger.exception("Failed to process JiraSyncEvent %s", sync_event_id)
            self.db.rollback()
            event.sync_status = SyncStatus.FAILED
            self.db.add(event)
            self.db.commit()

    def _handle_create_issue(self, event: JiraSyncEvent) -> None:
        request = self.db.scalar(
            select(ConfigChangeRequest).where(
                ConfigChangeRequest.request_id == event.request_id
            )
        )
        if not request:
            raise ValueError(f"Change request {event.request_id} not found")

        creator = self.db.scalar(select(User).where(User.user_id == request.created_by))
        service = self.db.scalar(select(Service).where(Service.service_id == request.service_id))
        target_node = self.db.scalar(
            select(ConfigNode).where(ConfigNode.config_node_id == request.target_config_node_id)
        )

        summary = (
            f"[ConfigSphere] Change Request – {service.service_name} / {target_node.path}"
        )
        description = (
            f"Change Request ID: {request.request_id}\n"
            f"Service: {service.service_name}\n"
            f"Target Node: {target_node.path}\n"
            f"Request Type: {request.request_type.value}\n"
            f"Status: {request.status.value}\n"
            f"\n"
            f"--- Requester Details ---\n"
            f"Name: {creator.display_name}\n"
            f"Email: {creator.email}\n"
            f"User ID: {creator.user_id}\n"
            f"\n"
            f"Created At: {request.created_at.isoformat()}\n"
        )
        if request.assigned_reviewer_id:
            reviewer = self.db.scalar(
                select(User).where(User.user_id == request.assigned_reviewer_id)
            )
            if reviewer:
                description += f"Assigned Reviewer: {reviewer.display_name} ({reviewer.email})\n"

        issue_key, issue_id = self.jira.create_issue(summary, description)

        if issue_key:
            request.jira_issue_key = issue_key
            request.jira_issue_id = issue_id
            event.jira_issue_key = issue_key
            self.db.add(request)
            self.db.add(event)
            logger.info(
                "Linked Jira issue %s to change request %s",
                issue_key,
                request.request_id,
            )

    def _handle_update_status(self, event: JiraSyncEvent) -> None:
        request = self.db.scalar(
            select(ConfigChangeRequest).where(
                ConfigChangeRequest.request_id == event.request_id
            )
        )
        if not request or not request.jira_issue_key:
            logger.info(
                "Skipping status update — no Jira issue linked for request %s",
                event.request_id,
            )
            return

        payload = event.payload_json or {}
        new_status = payload.get("status", "")

        transition_id = self.jira.transition_map.get(new_status)
        if transition_id:
            self.jira.transition_issue(request.jira_issue_key, transition_id)
            logger.info(
                "Transitioned Jira %s to %s for request %s",
                request.jira_issue_key,
                new_status,
                request.request_id,
            )
        else:
            logger.info(
                "No Jira transition configured for status %s, skipping transition",
                new_status,
            )

        self.jira.add_comment(
            request.jira_issue_key,
            f"Change request status updated to {new_status} in ConfigSphere.",
        )
        event.jira_issue_key = request.jira_issue_key
