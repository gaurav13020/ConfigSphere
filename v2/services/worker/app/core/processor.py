from __future__ import annotations

from collections import deque
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.constants import (
    ACTIVE_VERSION,
    CANDIDATE_VERSION,
    ChangeRequestStatus,
    JobStatus,
    JobType,
    RollbackStatus,
    VersionStatus,
)
from configsphere_shared.models import (
    ConfigChangeRequest,
    ConfigChangeRevision,
    ConfigNode,
    ConfigNodeVersion,
    PropagationJob,
    RollbackRequest,
    Service,
)


class PropagationProcessor:
    def __init__(self, db: Session, payload_store: ConfigPayloadStore) -> None:
        self.db = db
        self.payload_store = payload_store

    def process_job(self, job_id: UUID) -> None:
        job = self.db.scalar(select(PropagationJob).where(PropagationJob.job_id == job_id))
        if not job:
            raise ValueError(f"Propagation job {job_id} not found")

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.attempt_count += 1
        self.db.add(job)
        self.db.flush()

        try:
            if job.job_type == JobType.IMPLEMENT:
                self._process_implement(job)
            else:
                self._process_rollback(job)
            job.status = JobStatus.SUCCEEDED
            job.finished_at = datetime.utcnow()
            self.db.add(job)
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            retry_db = self.db
            failed_job = retry_db.scalar(select(PropagationJob).where(PropagationJob.job_id == job_id))
            failed_job.status = JobStatus.FAILED
            failed_job.error_message = str(exc)
            failed_job.finished_at = datetime.utcnow()
            retry_db.add(failed_job)
            if failed_job.job_type == JobType.IMPLEMENT:
                request = retry_db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == failed_job.request_id))
                if request:
                    request.status = ChangeRequestStatus.FAILED
                    retry_db.add(request)
            retry_db.commit()

    def _process_implement(self, job: PropagationJob) -> None:
        request = self.db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == job.request_id))
        revision = self.db.scalar(select(ConfigChangeRevision).where(ConfigChangeRevision.revision_id == job.revision_id))
        service = self.db.scalar(select(Service).where(Service.service_id == job.service_id))
        target_node = self.db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == job.target_config_node_id))

        if not request or not revision or not service or not target_node:
            raise ValueError("Propagation job references missing records")

        if revision.base_tree_version != service.current_tree_version:
            request.status = ChangeRequestStatus.CONFLICTED
            self.db.add(request)
            self.db.flush()
            raise ValueError("Revision is stale")

        active_target_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == target_node.active_version_id))
        active_doc = self.payload_store.get_document_by_id("NODE", str(target_node.config_node_id), active_target_version.document_id)
        proposed_doc = self.payload_store.get_document_by_id("REQUEST", str(request.request_id), revision.proposed_document_id)
        if not proposed_doc:
            proposed_doc = self.payload_store.get_document("REQUEST", str(request.request_id), str(revision.revision_number))
        if not active_doc or not proposed_doc:
            raise ValueError("Active or proposed document missing")

        new_materialized = dict(proposed_doc["materializedConfig"])
        local_overrides = dict(proposed_doc.get("localOverrides", {}))
        override_keys = sorted(proposed_doc.get("overrideKeys", local_overrides.keys()))
        changed_keys = self._diff_keys(active_doc["materializedConfig"], new_materialized)
        self._validate_payload(service, new_materialized)

        new_tree_version = service.current_tree_version + 1
        new_version = self._create_candidate_version(
            service=service,
            node=target_node,
            tree_version=new_tree_version,
            payload={
                "documentType": ACTIVE_VERSION,
                "serviceId": str(service.service_id),
                "configNodeId": str(target_node.config_node_id),
                "path": target_node.path,
                "materializedConfig": new_materialized,
                "localOverrides": local_overrides,
                "overrideKeys": override_keys,
                "keyCount": len(new_materialized),
                "createdAt": datetime.utcnow().isoformat(),
            },
            created_from_request_id=request.request_id,
            created_from_revision_id=revision.revision_id,
        )

        activation_map = {target_node.config_node_id: new_version.version_id}
        self._propagate_descendants(service, target_node, new_materialized, changed_keys, new_tree_version, activation_map)
        self._activate_versions(service, activation_map)

        request.status = ChangeRequestStatus.IMPLEMENTED
        request.implemented_at = datetime.utcnow()
        self.db.add(request)

    def _process_rollback(self, job: PropagationJob) -> None:
        rollback = self.db.scalar(
            select(RollbackRequest).where(RollbackRequest.target_config_node_id == job.target_config_node_id, RollbackRequest.status == RollbackStatus.IMPLEMENTING)
        )
        request = self.db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == job.request_id))
        service = self.db.scalar(select(Service).where(Service.service_id == job.service_id))
        target_node = self.db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == job.target_config_node_id))
        target_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == rollback.target_version_id))
        target_doc = self.payload_store.get_document_by_id("NODE", str(target_node.config_node_id), target_version.document_id)
        current_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == target_node.active_version_id))
        current_doc = self.payload_store.get_document_by_id("NODE", str(target_node.config_node_id), current_version.document_id)

        new_tree_version = service.current_tree_version + 1
        changed_keys = self._diff_keys(current_doc["materializedConfig"], target_doc["materializedConfig"])
        rollback_version = self._create_candidate_version(
            service=service,
            node=target_node,
            tree_version=new_tree_version,
            payload={
                "documentType": ACTIVE_VERSION,
                "serviceId": str(service.service_id),
                "configNodeId": str(target_node.config_node_id),
                "path": target_node.path,
                "materializedConfig": dict(target_doc["materializedConfig"]),
                "localOverrides": dict(target_doc.get("localOverrides", {})),
                "overrideKeys": list(target_doc.get("overrideKeys", [])),
                "keyCount": len(target_doc["materializedConfig"]),
                "createdAt": datetime.utcnow().isoformat(),
            },
            created_from_request_id=request.request_id,
            created_from_revision_id=job.revision_id,
            created_from_rollback_id=rollback.rollback_request_id,
            version_status=VersionStatus.ROLLED_BACK,
        )
        activation_map = {target_node.config_node_id: rollback_version.version_id}
        self._propagate_descendants(
            service,
            target_node,
            dict(target_doc["materializedConfig"]),
            changed_keys,
            new_tree_version,
            activation_map,
        )
        self._activate_versions(service, activation_map)
        rollback.status = RollbackStatus.ROLLED_BACK
        request.status = ChangeRequestStatus.IMPLEMENTED
        request.implemented_at = datetime.utcnow()
        self.db.add_all([rollback, request])

    def _diff_keys(self, before: dict[str, str], after: dict[str, str]) -> list[str]:
        keys = set(before.keys()) | set(after.keys())
        return sorted([key for key in keys if before.get(key) != after.get(key)])

    def _validate_payload(self, service: Service, payload: dict[str, str]) -> None:
        if len(payload) > service.max_keys_per_node:
            raise ValueError("Payload exceeds max key count")
        for key, value in payload.items():
            if len(value) > service.max_value_size:
                raise ValueError(f"Value for {key} exceeds max size")

    def _create_candidate_version(
        self,
        *,
        service: Service,
        node: ConfigNode,
        tree_version: int,
        payload: dict,
        created_from_request_id: UUID | None,
        created_from_revision_id: UUID | None,
        created_from_rollback_id: UUID | None = None,
        version_status: VersionStatus = VersionStatus.PENDING,
    ) -> ConfigNodeVersion:
        document_id = self.payload_store.put_document(
            "NODE",
            str(node.config_node_id),
            str(tree_version),
            payload,
        )
        version = ConfigNodeVersion(
            config_node_id=node.config_node_id,
            service_id=service.service_id,
            tree_version=tree_version,
            document_id=document_id,
            version_status=version_status,
            created_from_request_id=created_from_request_id,
            created_from_revision_id=created_from_revision_id,
            created_from_rollback_id=created_from_rollback_id,
        )
        self.db.add(version)
        self.db.flush()
        return version

    def _propagate_descendants(
        self,
        service: Service,
        target_node: ConfigNode,
        new_parent_materialized: dict[str, str],
        changed_keys: list[str],
        new_tree_version: int,
        activation_map: dict[UUID, UUID],
    ) -> None:
        queue = deque([(target_node.config_node_id, new_parent_materialized, changed_keys)])
        while queue:
            parent_id, parent_materialized, parent_changed_keys = queue.popleft()
            children = self.db.scalars(
                select(ConfigNode).where(ConfigNode.parent_config_node_id == parent_id).order_by(ConfigNode.path.asc())
            ).all()
            for child in children:
                if not child.active_version_id:
                    continue
                child_active_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == child.active_version_id))
                child_doc = self.payload_store.get_document_by_id("NODE", str(child.config_node_id), child_active_version.document_id)
                if not child_doc:
                    continue
                child_materialized = dict(child_doc["materializedConfig"])
                child_override_keys = set(child_doc.get("overrideKeys", []))
                child_changed_keys: list[str] = []
                for key in parent_changed_keys:
                    if key in child_override_keys:
                        continue
                    parent_value = parent_materialized.get(key)
                    current_value = child_materialized.get(key)
                    if parent_value is None:
                        if key in child_materialized:
                            del child_materialized[key]
                            child_changed_keys.append(key)
                    elif current_value != parent_value:
                        child_materialized[key] = parent_value
                        child_changed_keys.append(key)
                if not child_changed_keys:
                    continue
                self._validate_payload(service, child_materialized)
                new_payload = {
                    "documentType": ACTIVE_VERSION,
                    "serviceId": str(service.service_id),
                    "configNodeId": str(child.config_node_id),
                    "path": child.path,
                    "materializedConfig": child_materialized,
                    "localOverrides": dict(child_doc.get("localOverrides", {})),
                    "overrideKeys": list(child_doc.get("overrideKeys", [])),
                    "keyCount": len(child_materialized),
                    "createdAt": datetime.utcnow().isoformat(),
                }
                new_version = self._create_candidate_version(
                    service=service,
                    node=child,
                    tree_version=new_tree_version,
                    payload=new_payload,
                    created_from_request_id=None,
                    created_from_revision_id=None,
                )
                activation_map[child.config_node_id] = new_version.version_id
                queue.append((child.config_node_id, child_materialized, child_changed_keys))

    def _activate_versions(self, service: Service, activation_map: dict[UUID, UUID]) -> None:
        for node_id, new_version_id in activation_map.items():
            node = self.db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == node_id))
            old_version_id = node.active_version_id
            node.active_version_id = new_version_id
            self.db.add(node)
            if old_version_id:
                old_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == old_version_id))
                if old_version:
                    old_version.version_status = VersionStatus.SUPERSEDED
                    self.db.add(old_version)
            new_version = self.db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == new_version_id))
            new_version.version_status = VersionStatus.ACTIVE
            self.db.add(new_version)
        service.current_tree_version += 1
        self.db.add(service)
