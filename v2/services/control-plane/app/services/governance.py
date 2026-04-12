from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.constants import (
    ChangeRequestStatus,
    JobStatus,
    JobType,
    PROPOSED_REVISION,
    RequestType,
    ReviewDecision,
    RollbackStatus,
    SyncStatus,
)
from configsphere_shared.events import ImplementRequestedEvent, JiraSyncRequestedEvent, RollbackRequestedEvent
from configsphere_shared.models import (
    ConfigChangeAction,
    ConfigChangeComment,
    ConfigChangeRequest,
    ConfigChangeRevision,
    ConfigNode,
    ConfigNodeVersion,
    JiraSyncEvent,
    PropagationJob,
    RollbackRequest,
    Service,
)
from .kafka import KafkaPublisher


def _ensure_latest_revision(request: ConfigChangeRequest, revision_id: uuid.UUID) -> None:
    if request.current_revision_id != revision_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only latest revision can be reviewed or implemented")


def _require_request_status(request: ConfigChangeRequest, allowed: set[ChangeRequestStatus]) -> None:
    if request.status not in allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Request status {request.status} is not allowed")


def create_change_request(
    db: Session,
    service_id: uuid.UUID,
    target_config_node_id: uuid.UUID,
    request_type: RequestType,
    assigned_reviewer_id: uuid.UUID | None,
    created_by: uuid.UUID,
    kafka: KafkaPublisher | None = None,
) -> ConfigChangeRequest:
    request = ConfigChangeRequest(
        service_id=service_id,
        target_config_node_id=target_config_node_id,
        request_type=request_type,
        status=ChangeRequestStatus.DRAFT,
        assigned_reviewer_id=assigned_reviewer_id,
        created_by=created_by,
    )
    db.add(request)
    db.flush()
    db.add(
        ConfigChangeAction(
            request_id=request.request_id,
            actor_id=created_by,
            action_type="CREATE",
        )
    )
    sync_event = JiraSyncEvent(
            request_id=request.request_id,
            event_type="CREATE_ISSUE",
            payload_json={"request_id": str(request.request_id)},
            sync_status=SyncStatus.PENDING,
        )
    db.add(sync_event)
    db.flush()
    if kafka:
        kafka.publish(
            "jira-sync-events",
            JiraSyncRequestedEvent(
                sync_event_id=sync_event.sync_event_id,
                correlation_id=str(sync_event.sync_event_id),
                created_at=datetime.utcnow(),
            ).model_dump(mode="json"),
        )
    return request


def create_revision(
    db: Session,
    payload_store: ConfigPayloadStore,
    request: ConfigChangeRequest,
    node: ConfigNode,
    service: Service,
    proposed_overrides: dict[str, str],
    change_note: str | None,
    created_by: uuid.UUID,
) -> ConfigChangeRevision:
    if len(proposed_overrides) > service.max_keys_per_node:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposed overrides exceed max keys")
    for key, value in proposed_overrides.items():
        if len(value) > service.max_value_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Value for {key} exceeds max size")

    current_number = db.scalar(
        select(ConfigChangeRevision.revision_number)
        .where(ConfigChangeRevision.request_id == request.request_id)
        .order_by(ConfigChangeRevision.revision_number.desc())
        .limit(1)
    ) or 0

    active_version = db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == node.active_version_id))
    current_doc = payload_store.get_document_by_id("NODE", str(node.config_node_id), active_version.document_id)
    current_config = dict(current_doc["materializedConfig"])
    current_overrides = dict(current_doc.get("localOverrides", {}))
    parent_config: dict[str, str] = {}
    if node.parent_config_node_id:
        parent_node = db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == node.parent_config_node_id))
        if parent_node and parent_node.active_version_id:
            parent_version = db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == parent_node.active_version_id))
            if parent_version:
                parent_doc = payload_store.get_document_by_id("NODE", str(parent_node.config_node_id), parent_version.document_id)
                if parent_doc:
                    parent_config = dict(parent_doc["materializedConfig"])

    effective_config = dict(parent_config)
    effective_config.update(proposed_overrides)

    inherited_changes = {
        key: {"before": current_overrides[key], "after": parent_config[key]}
        for key in current_overrides
        if key not in proposed_overrides and key in parent_config and current_overrides[key] != parent_config[key]
    }

    if len(effective_config) > service.max_keys_per_node:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposed config exceeds max keys")
    for key, value in effective_config.items():
        if len(value) > service.max_value_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Value for {key} exceeds max size")

    diff = {
        "added": {k: v for k, v in proposed_overrides.items() if k not in current_overrides},
        "removed": {
            k: v
            for k, v in current_overrides.items()
            if k not in proposed_overrides and k not in parent_config
        },
        "changed": {
            k: {"before": current_overrides[k], "after": proposed_overrides[k]}
            for k in proposed_overrides
            if k in current_overrides and current_overrides[k] != proposed_overrides[k]
        },
        "inherited": inherited_changes,
    }

    revision_number = current_number + 1
    document_id = payload_store.put_document(
        "REQUEST",
        str(request.request_id),
        str(revision_number),
        {
            "documentType": PROPOSED_REVISION,
            "requestId": str(request.request_id),
            "revisionId": "pending",
            "serviceId": str(service.service_id),
            "configNodeId": str(node.config_node_id),
            "path": node.path,
            "materializedConfig": effective_config,
            "localOverrides": proposed_overrides,
            "overrideKeys": sorted(proposed_overrides.keys()),
            "keyCount": len(effective_config),
            "baseTreeVersion": service.current_tree_version,
            "createdAt": datetime.utcnow().isoformat(),
        },
    )
    revision = ConfigChangeRevision(
        request_id=request.request_id,
        revision_number=revision_number,
        proposed_document_id=document_id,
        diff_summary_json=diff,
        base_tree_version=service.current_tree_version,
        change_note=change_note,
        created_by=created_by,
    )
    db.add(revision)
    db.flush()
    request.current_revision_id = revision.revision_id
    if request.status in {ChangeRequestStatus.APPROVED, ChangeRequestStatus.CHANGES_REQUESTED}:
        request.status = ChangeRequestStatus.DRAFT
        request.approved_at = None
    db.add(request)
    db.add(
        ConfigChangeAction(
            request_id=request.request_id,
            revision_id=revision.revision_id,
            actor_id=created_by,
            action_type="CREATE_REVISION",
            note=change_note,
        )
    )
    return revision


def add_comment(db: Session, request: ConfigChangeRequest, revision_id: uuid.UUID | None, author_id: uuid.UUID, body: str) -> None:
    db.add(
        ConfigChangeComment(
            request_id=request.request_id,
            revision_id=revision_id,
            author_id=author_id,
            body=body,
        )
    )


def submit_request(db: Session, request: ConfigChangeRequest, actor_id: uuid.UUID, note: str | None, kafka: KafkaPublisher | None = None) -> ConfigChangeRequest:
    if not request.current_revision_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request requires at least one revision before submission")
    request.status = ChangeRequestStatus.SUBMITTED
    request.submitted_at = datetime.utcnow()
    db.add(request)
    db.add(ConfigChangeAction(request_id=request.request_id, revision_id=request.current_revision_id, actor_id=actor_id, action_type="SUBMIT", note=note))
    sync_event = JiraSyncEvent(
        request_id=request.request_id,
        event_type="UPDATE_STATUS",
        payload_json={"status": request.status.value},
        sync_status=SyncStatus.PENDING,
    )
    db.add(sync_event)
    db.flush()
    if kafka:
        kafka.publish(
            "jira-sync-events",
            JiraSyncRequestedEvent(
                sync_event_id=sync_event.sync_event_id,
                correlation_id=str(sync_event.sync_event_id),
                created_at=datetime.utcnow(),
            ).model_dump(mode="json"),
        )
    return request


def cancel_request(db: Session, request: ConfigChangeRequest, actor_id: uuid.UUID, note: str | None, kafka: KafkaPublisher | None = None) -> ConfigChangeRequest:
    if request.status in {ChangeRequestStatus.IMPLEMENTING, ChangeRequestStatus.IMPLEMENTED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Implemented requests cannot be canceled")
    request.status = ChangeRequestStatus.REJECTED
    db.add(request)
    db.add(
        ConfigChangeAction(
            request_id=request.request_id,
            revision_id=request.current_revision_id,
            actor_id=actor_id,
            action_type="CANCEL",
            note=note,
        )
    )
    sync_event = JiraSyncEvent(
        request_id=request.request_id,
        event_type="UPDATE_STATUS",
        payload_json={"status": request.status.value, "reason": "CANCELED"},
        sync_status=SyncStatus.PENDING,
    )
    db.add(sync_event)
    db.flush()
    if kafka:
        kafka.publish(
            "jira-sync-events",
            JiraSyncRequestedEvent(
                sync_event_id=sync_event.sync_event_id,
                correlation_id=str(sync_event.sync_event_id),
                created_at=datetime.utcnow(),
            ).model_dump(mode="json"),
        )
    return request


def review_request(
    db: Session,
    request: ConfigChangeRequest,
    revision_id: uuid.UUID,
    decision: ReviewDecision,
    reviewer_id: uuid.UUID,
    note: str | None,
    kafka: KafkaPublisher | None = None,
) -> ConfigChangeRequest:
    _ensure_latest_revision(request, revision_id)
    if request.status not in {ChangeRequestStatus.SUBMITTED, ChangeRequestStatus.IN_REVIEW, ChangeRequestStatus.CHANGES_REQUESTED, ChangeRequestStatus.DRAFT}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request cannot be reviewed in current state")

    if decision == ReviewDecision.REQUEST_CHANGES:
        request.status = ChangeRequestStatus.CHANGES_REQUESTED
    elif decision == ReviewDecision.APPROVE:
        request.status = ChangeRequestStatus.APPROVED
        request.approved_at = datetime.utcnow()
    elif decision == ReviewDecision.REJECT:
        request.status = ChangeRequestStatus.REJECTED
    else:
        request.status = ChangeRequestStatus.IN_REVIEW
    db.add(request)
    db.add(
        ConfigChangeAction(
            request_id=request.request_id,
            revision_id=revision_id,
            actor_id=reviewer_id,
            action_type=decision.value,
            note=note,
        )
    )
    from configsphere_shared.models import ConfigRevisionReview

    db.add(
        ConfigRevisionReview(
            request_id=request.request_id,
            revision_id=revision_id,
            reviewer_id=reviewer_id,
            decision=decision,
            note=note,
        )
    )
    sync_event = JiraSyncEvent(
        request_id=request.request_id,
        event_type="UPDATE_STATUS",
        payload_json={"status": request.status.value, "decision": decision.value},
        sync_status=SyncStatus.PENDING,
    )
    db.add(sync_event)
    db.flush()
    if kafka:
        kafka.publish(
            "jira-sync-events",
            JiraSyncRequestedEvent(
                sync_event_id=sync_event.sync_event_id,
                correlation_id=str(sync_event.sync_event_id),
                created_at=datetime.utcnow(),
            ).model_dump(mode="json"),
        )
    return request


def implement_request(
    db: Session,
    request: ConfigChangeRequest,
    service: Service,
    actor_id: uuid.UUID,
    kafka: KafkaPublisher,
) -> PropagationJob:
    if request.status != ChangeRequestStatus.APPROVED or not request.current_revision_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only approved requests may be implemented")

    revision = db.scalar(
        select(ConfigChangeRevision).where(ConfigChangeRevision.revision_id == request.current_revision_id)
    )
    if revision.base_tree_version != service.current_tree_version:
        request.status = ChangeRequestStatus.CONFLICTED
        db.add(request)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Revision is stale and must be rebased")

    existing_job = db.scalar(
        select(PropagationJob).where(
            PropagationJob.service_id == service.service_id,
            PropagationJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]),
        )
    )
    if existing_job:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already has an active propagation job")

    request.status = ChangeRequestStatus.IMPLEMENTING
    db.add(request)
    job = PropagationJob(
        request_id=request.request_id,
        revision_id=revision.revision_id,
        service_id=request.service_id,
        target_config_node_id=request.target_config_node_id,
        job_type=JobType.IMPLEMENT,
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.flush()
    event = ImplementRequestedEvent(
        request_id=request.request_id,
        revision_id=revision.revision_id,
        service_id=request.service_id,
        target_config_node_id=request.target_config_node_id,
        correlation_id=str(job.job_id),
        created_at=datetime.utcnow(),
    )
    kafka.publish("config-implement-requests", event.model_dump(mode="json"))
    return job


def create_rollback_request(
    db: Session,
    service_id: uuid.UUID,
    target_config_node_id: uuid.UUID,
    target_version_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> RollbackRequest:
    rollback = RollbackRequest(
        service_id=service_id,
        target_config_node_id=target_config_node_id,
        target_version_id=target_version_id,
        status=RollbackStatus.REQUESTED,
        requested_by=actor_id,
    )
    db.add(rollback)
    db.flush()
    return rollback


def approve_rollback(db: Session, rollback: RollbackRequest, actor_id: uuid.UUID) -> RollbackRequest:
    rollback.status = RollbackStatus.APPROVED
    rollback.approved_by = actor_id
    db.add(rollback)
    return rollback


def implement_rollback(
    db: Session,
    rollback: RollbackRequest,
    request_owner: uuid.UUID,
    kafka: KafkaPublisher,
) -> PropagationJob:
    if rollback.status != RollbackStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rollback must be approved before implementation")

    request = ConfigChangeRequest(
        service_id=rollback.service_id,
        target_config_node_id=rollback.target_config_node_id,
        request_type=RequestType.ROLLBACK,
        status=ChangeRequestStatus.IMPLEMENTING,
        created_by=request_owner,
        current_revision_id=None,
    )
    db.add(request)
    db.flush()
    revision = ConfigChangeRevision(
        request_id=request.request_id,
        revision_number=1,
        proposed_document_id=str(rollback.target_version_id),
        diff_summary_json={},
        base_tree_version=0,
        created_by=request_owner,
    )
    db.add(revision)
    db.flush()
    request.current_revision_id = revision.revision_id
    db.add(request)

    job = PropagationJob(
        request_id=request.request_id,
        revision_id=revision.revision_id,
        service_id=rollback.service_id,
        target_config_node_id=rollback.target_config_node_id,
        job_type=JobType.ROLLBACK,
        status=JobStatus.PENDING,
    )
    rollback.status = RollbackStatus.IMPLEMENTING
    db.add_all([job, rollback])
    db.flush()
    event = RollbackRequestedEvent(
        rollback_request_id=rollback.rollback_request_id,
        request_id=request.request_id,
        revision_id=revision.revision_id,
        service_id=rollback.service_id,
        target_config_node_id=rollback.target_config_node_id,
        correlation_id=str(job.job_id),
        created_at=datetime.utcnow(),
    )
    kafka.publish("config-implement-requests", event.model_dump(mode="json"))
    return job
