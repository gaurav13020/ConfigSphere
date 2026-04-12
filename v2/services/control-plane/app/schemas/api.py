from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from configsphere_shared.constants import ChangeRequestStatus, RequestType, ReviewDecision, RoleName, RollbackStatus, ScopeType, ServiceType


class ServiceCreate(BaseModel):
    service_name: str
    service_type: ServiceType
    owner_team: str | None = None


class ServiceRead(BaseModel):
    service_id: UUID
    service_name: str
    service_type: ServiceType
    owner_team: str | None
    node_count: int
    current_tree_version: int

    class Config:
        from_attributes = True


class ConfigNodeVersionRead(BaseModel):
    version_id: UUID
    config_node_id: UUID
    service_id: UUID
    tree_version: int
    document_id: str
    version_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RootNodeCreate(BaseModel):
    path: str = "/global"
    base_config: dict[str, str] = Field(default_factory=dict)


class ChildNodeCreate(BaseModel):
    segment: str


class ConfigNodeRead(BaseModel):
    config_node_id: UUID
    service_id: UUID
    parent_config_node_id: UUID | None
    path: str
    depth: int
    active_version_id: UUID | None

    class Config:
        from_attributes = True


class ChangeRequestCreate(BaseModel):
    service_id: UUID
    target_config_node_id: UUID
    request_type: RequestType = RequestType.EDIT_NODE
    assigned_reviewer_id: UUID | None = None


class RevisionCreate(BaseModel):
    proposed_overrides: dict[str, str]
    change_note: str | None = None


class CommentCreate(BaseModel):
    body: str
    revision_id: UUID | None = None


class SubmitRequest(BaseModel):
    note: str | None = None


class CancelRequest(BaseModel):
    note: str | None = None


class ReviewCreate(BaseModel):
    revision_id: UUID
    decision: ReviewDecision
    note: str | None = None


class RollbackCreate(BaseModel):
    service_id: UUID
    target_config_node_id: UUID
    target_version_id: UUID


class RollbackApprove(BaseModel):
    note: str | None = None


class JobRead(BaseModel):
    job_id: UUID
    status: str
    job_type: str

    class Config:
        from_attributes = True


class ChangeRequestRead(BaseModel):
    request_id: UUID
    service_id: UUID
    target_config_node_id: UUID
    request_type: RequestType
    status: ChangeRequestStatus
    created_by: UUID
    assigned_reviewer_id: UUID | None
    jira_issue_key: str | None
    current_revision_id: UUID | None
    submitted_at: datetime | None
    approved_at: datetime | None
    implemented_at: datetime | None
    created_at: datetime
    updated_at: datetime
    latest_revision_number: int | None = None
    latest_diff_summary: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class RevisionRead(BaseModel):
    revision_id: UUID
    request_id: UUID
    revision_number: int
    proposed_document_id: str
    diff_summary_json: dict[str, Any]
    proposed_overrides: dict[str, str] = Field(default_factory=dict)
    base_tree_version: int
    change_note: str | None
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CommentRead(BaseModel):
    comment_id: UUID
    request_id: UUID
    revision_id: UUID | None
    author_id: UUID
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewRead(BaseModel):
    review_id: UUID
    request_id: UUID
    revision_id: UUID
    reviewer_id: UUID
    decision: ReviewDecision
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RequestActivityRead(BaseModel):
    request: ChangeRequestRead
    revisions: list[RevisionRead]
    comments: list[CommentRead]
    reviews: list[ReviewRead]


class RollbackRead(BaseModel):
    rollback_request_id: UUID
    service_id: UUID
    target_config_node_id: UUID
    target_version_id: UUID
    status: RollbackStatus
    jira_issue_key: str | None

    class Config:
        from_attributes = True


class BootstrapAdminStatusRead(BaseModel):
    bootstrap_required: bool
    global_admin_count: int


class BootstrapAdminResponse(BaseModel):
    status: str
    user_id: UUID
    email: str


class UserSummaryRead(BaseModel):
    user_id: UUID
    email: str
    display_name: str
    external_subject: str
    jira_account_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleBindingCreate(BaseModel):
    target_user_id: UUID
    role_name: RoleName
    scope_type: ScopeType
    scope_id: UUID | None = None
    note: str | None = None


class RoleBindingRead(BaseModel):
    binding_id: UUID
    user_id: UUID
    role_id: UUID
    role_name: RoleName
    scope_type: ScopeType
    scope_id: UUID | None
    created_at: datetime


class ServiceApiKeyCreate(BaseModel):
    key_name: str


class ServiceApiKeyRead(BaseModel):
    api_key_id: UUID
    service_id: UUID
    key_name: str
    token_prefix: str
    created_by: UUID | None
    revoked_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceApiKeyCreated(ServiceApiKeyRead):
    plain_token: str


class RbacAuditEventRead(BaseModel):
    audit_event_id: UUID
    actor_user_id: UUID
    target_user_id: UUID
    role_id: UUID
    role_name: RoleName
    scope_type: ScopeType
    scope_id: UUID | None
    action: str
    note: str | None
    created_at: datetime
