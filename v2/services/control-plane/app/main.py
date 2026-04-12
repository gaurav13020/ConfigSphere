from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.constants import ChangeRequestStatus, RequestType, RoleName, ScopeType
from configsphere_shared.models import (
    ConfigChangeRequest,
    ConfigChangeRevision,
    ConfigNode,
    ConfigNodeVersion,
    RbacAuditEvent,
    Role,
    RollbackRequest,
    Service,
    ServiceApiKey,
    User,
    UserRoleBinding,
)
from configsphere_shared.security import AuthenticatedUser, get_current_user

from app.db.session import get_db
from app.schemas.api import (
    BootstrapAdminResponse,
    BootstrapAdminStatusRead,
    CancelRequest,
    ChangeRequestCreate,
    ChangeRequestRead,
    ChildNodeCreate,
    CommentRead,
    CommentCreate,
    ConfigNodeRead,
    ConfigNodeVersionRead,
    JobRead,
    RbacAuditEventRead,
    RequestActivityRead,
    RevisionCreate,
    RevisionRead,
    ReviewRead,
    ReviewCreate,
    RoleBindingCreate,
    RoleBindingRead,
    RollbackApprove,
    RollbackCreate,
    RollbackRead,
    RootNodeCreate,
    ServiceApiKeyCreate,
    ServiceApiKeyCreated,
    ServiceApiKeyRead,
    ServiceCreate,
    ServiceRead,
    SubmitRequest,
    UserSummaryRead,
)
from app.services.authz import (
    count_global_admins,
    ensure_role_seed,
    get_or_create_user,
    grant_role_binding,
    has_service_role,
    list_role_bindings_for_user,
    require_global_admin,
    require_service_role,
    revoke_role_binding,
)
from app.services.configs import create_child_node, create_root_node, create_service
from app.services.delivery_keys import create_service_api_key, list_service_api_keys, revoke_service_api_key
from app.services.governance import (
    add_comment,
    approve_rollback,
    cancel_request,
    create_change_request,
    create_revision,
    create_rollback_request,
    implement_request,
    implement_rollback,
    review_request,
    submit_request,
)
from app.services.kafka import KafkaPublisher


app = FastAPI(title="ConfigSphere V2 Control Plane")
payload_store = ConfigPayloadStore()
kafka = KafkaPublisher()

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _bootstrap_user(db: Session, current_user: AuthenticatedUser):
    ensure_role_seed(db)
    user = get_or_create_user(db, current_user)
    db.commit()
    db.refresh(user)
    return user


def _role_binding_read(binding: UserRoleBinding, role_name: RoleName) -> RoleBindingRead:
    return RoleBindingRead(
        binding_id=binding.binding_id,
        user_id=binding.user_id,
        role_id=binding.role_id,
        role_name=role_name,
        scope_type=binding.scope_type,
        scope_id=binding.scope_id,
        created_at=binding.created_at,
    )


def _rbac_audit_event_read(event: RbacAuditEvent, role_name: RoleName) -> RbacAuditEventRead:
    return RbacAuditEventRead(
        audit_event_id=event.audit_event_id,
        actor_user_id=event.actor_user_id,
        target_user_id=event.target_user_id,
        role_id=event.role_id,
        role_name=role_name,
        scope_type=event.scope_type,
        scope_id=event.scope_id,
        action=event.action,
        note=event.note,
        created_at=event.created_at,
    )


def _change_request_read(
    request: ConfigChangeRequest,
    latest_revision_number: int | None = None,
    latest_diff_summary: dict | None = None,
) -> ChangeRequestRead:
    return ChangeRequestRead(
        request_id=request.request_id,
        service_id=request.service_id,
        target_config_node_id=request.target_config_node_id,
        request_type=request.request_type,
        status=request.status,
        created_by=request.created_by,
        assigned_reviewer_id=request.assigned_reviewer_id,
        jira_issue_key=request.jira_issue_key,
        current_revision_id=request.current_revision_id,
        submitted_at=request.submitted_at,
        approved_at=request.approved_at,
        implemented_at=request.implemented_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
        latest_revision_number=latest_revision_number,
        latest_diff_summary=latest_diff_summary,
    )


def _service_api_key_created_read(api_key: ServiceApiKey, plain_token: str) -> ServiceApiKeyCreated:
    return ServiceApiKeyCreated(
        api_key_id=api_key.api_key_id,
        service_id=api_key.service_id,
        key_name=api_key.key_name,
        token_prefix=api_key.token_prefix,
        created_by=api_key.created_by,
        revoked_at=api_key.revoked_at,
        created_at=api_key.created_at,
        plain_token=plain_token,
    )


@app.get("/v1/admin/bootstrap/status", response_model=BootstrapAdminStatusRead)
def bootstrap_admin_status_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    admin_count = count_global_admins(db)
    return BootstrapAdminStatusRead(
        bootstrap_required=admin_count == 0,
        global_admin_count=admin_count,
    )


@app.post("/v1/admin/bootstrap", response_model=BootstrapAdminResponse)
def bootstrap_admin_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    if count_global_admins(db) > 0:
        raise HTTPException(status_code=409, detail="Bootstrap admin already exists")
    grant_role_binding(
        db,
        actor_user_id=user.user_id,
        target_user_id=user.user_id,
        role_name=RoleName.CONFIG_ADMIN,
        scope_type=ScopeType.GLOBAL,
        scope_id=None,
        note="Initial bootstrap admin",
    )
    db.commit()
    return BootstrapAdminResponse(status="bootstrapped", user_id=user.user_id, email=user.email)


@app.get("/v1/admin/users", response_model=list[UserSummaryRead])
def list_admin_users_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_global_admin(db, user.user_id)
    return db.scalars(select(User).order_by(User.email.asc())).all()


@app.get("/v1/admin/users/{target_user_id}/bindings", response_model=list[RoleBindingRead])
def list_user_role_bindings_endpoint(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_global_admin(db, user.user_id)
    target = db.scalar(select(User).where(User.user_id == target_user_id))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        _role_binding_read(binding, role_name)
        for binding, role_name in list_role_bindings_for_user(db, target.user_id)
    ]


@app.get("/v1/users", response_model=list[UserSummaryRead])
def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    return db.scalars(select(User).order_by(User.email.asc())).all()


@app.get("/v1/me/bindings", response_model=list[RoleBindingRead])
def list_my_bindings_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    return [
        _role_binding_read(binding, role_name)
        for binding, role_name in list_role_bindings_for_user(db, user.user_id)
    ]


@app.post("/v1/admin/role-bindings", response_model=RoleBindingRead)
def grant_role_binding_endpoint(
    payload: RoleBindingCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_global_admin(db, user.user_id)
    target = db.scalar(select(User).where(User.user_id == payload.target_user_id))
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
    if payload.scope_type == ScopeType.SERVICE:
        service = db.scalar(select(Service).where(Service.service_id == payload.scope_id))
        if not service:
            raise HTTPException(status_code=404, detail="Service not found for service-scoped binding")
    binding = grant_role_binding(
        db,
        actor_user_id=user.user_id,
        target_user_id=payload.target_user_id,
        role_name=payload.role_name,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        note=payload.note,
    )
    db.commit()
    role = db.scalar(select(Role).where(Role.role_id == binding.role_id))
    return _role_binding_read(binding, role.role_name)


@app.delete("/v1/admin/role-bindings/{binding_id}")
def revoke_role_binding_endpoint(
    binding_id: str,
    note: str | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_global_admin(db, user.user_id)
    binding = db.scalar(select(UserRoleBinding).where(UserRoleBinding.binding_id == binding_id))
    if not binding:
        raise HTTPException(status_code=404, detail="Role binding not found")
    revoke_role_binding(db, actor_user_id=user.user_id, binding=binding, note=note)
    db.commit()
    return {"status": "revoked"}


@app.get("/v1/admin/audit", response_model=list[RbacAuditEventRead])
def list_rbac_audit_endpoint(
    target_user_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_global_admin(db, user.user_id)
    stmt = (
        select(RbacAuditEvent, Role.role_name)
        .join(Role, Role.role_id == RbacAuditEvent.role_id)
        .order_by(RbacAuditEvent.created_at.desc())
    )
    if target_user_id:
        stmt = stmt.where(RbacAuditEvent.target_user_id == target_user_id)
    return [
        _rbac_audit_event_read(event, role_name)
        for event, role_name in db.execute(stmt).all()
    ]


@app.post("/v1/services", response_model=ServiceRead)
def create_service_endpoint(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = create_service(db, payload.service_name, payload.service_type, payload.owner_team)
    db.commit()
    db.refresh(service)
    return service


@app.get("/v1/services", response_model=list[ServiceRead])
def list_services_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    return db.scalars(select(Service).order_by(Service.service_name.asc())).all()


@app.get("/v1/services/{service_id}", response_model=ServiceRead)
def get_service_endpoint(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.get("/v1/services/{service_id}/api-keys", response_model=list[ServiceApiKeyRead])
def list_service_api_keys_endpoint(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    require_service_role(db, user.user_id, service.service_id, [RoleName.CONFIG_ADMIN])
    return list_service_api_keys(db, service.service_id)


@app.post("/v1/services/{service_id}/api-keys", response_model=ServiceApiKeyCreated)
def create_service_api_key_endpoint(
    service_id: str,
    payload: ServiceApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    require_service_role(db, user.user_id, service.service_id, [RoleName.CONFIG_ADMIN])
    api_key, plain_token = create_service_api_key(db, service=service, key_name=payload.key_name, created_by=user.user_id)
    db.commit()
    db.refresh(api_key)
    return _service_api_key_created_read(api_key, plain_token)


@app.delete("/v1/services/{service_id}/api-keys/{api_key_id}", response_model=ServiceApiKeyRead)
def revoke_service_api_key_endpoint(
    service_id: str,
    api_key_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    require_service_role(db, user.user_id, service.service_id, [RoleName.CONFIG_ADMIN])
    api_key = db.scalar(
        select(ServiceApiKey).where(
            ServiceApiKey.api_key_id == api_key_id,
            ServiceApiKey.service_id == service.service_id,
        )
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="Service API key not found")
    revoke_service_api_key(db, api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


@app.post("/v1/services/{service_id}/nodes/root", response_model=ConfigNodeRead)
def create_root_node_endpoint(
    service_id: str,
    payload: RootNodeCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    node = create_root_node(db, payload_store, service, payload.path, payload.base_config, user.user_id)
    db.commit()
    db.refresh(node)
    return node


@app.post("/v1/services/{service_id}/nodes/{parent_node_id}/children", response_model=ConfigNodeRead)
def create_child_node_endpoint(
    service_id: str,
    parent_node_id: str,
    payload: ChildNodeCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    service = db.scalar(select(Service).where(Service.service_id == service_id))
    parent = db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == parent_node_id))
    if not service or not parent:
        raise HTTPException(status_code=404, detail="Service or parent node not found")
    node = create_child_node(db, payload_store, service, parent, payload.segment, user.user_id)
    db.commit()
    db.refresh(node)
    return node


@app.get("/v1/services/{service_id}/nodes", response_model=list[ConfigNodeRead])
def list_service_nodes_endpoint(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    return db.scalars(
        select(ConfigNode).where(ConfigNode.service_id == service_id).order_by(ConfigNode.path.asc())
    ).all()


@app.get("/v1/services/{service_id}/nodes/{node_id}/versions", response_model=list[ConfigNodeVersionRead])
def list_node_versions_endpoint(
    service_id: str,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    return db.scalars(
        select(ConfigNodeVersion)
        .where(
            ConfigNodeVersion.service_id == service_id,
            ConfigNodeVersion.config_node_id == node_id,
        )
        .order_by(ConfigNodeVersion.created_at.desc())
    ).all()


@app.post("/v1/change-requests", response_model=ChangeRequestRead)
def create_change_request_endpoint(
    payload: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_service_role(db, user.user_id, payload.service_id, [RoleName.CONFIG_AUTHOR, RoleName.CONFIG_ADMIN])
    request = create_change_request(
        db,
        payload.service_id,
        payload.target_config_node_id,
        payload.request_type,
        payload.assigned_reviewer_id,
        user.user_id,
    )
    db.commit()
    db.refresh(request)
    return _change_request_read(request)


@app.post("/v1/change-requests/{request_id}/revisions", response_model=ChangeRequestRead)
def create_revision_endpoint(
    request_id: str,
    payload: RevisionCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    require_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_AUTHOR, RoleName.CONFIG_ADMIN])
    service = db.scalar(select(Service).where(Service.service_id == request.service_id))
    node = db.scalar(select(ConfigNode).where(ConfigNode.config_node_id == request.target_config_node_id))
    revision = create_revision(
        db,
        payload_store,
        request,
        node,
        service,
        payload.proposed_overrides,
        payload.change_note,
        user.user_id,
    )
    db.commit()
    db.refresh(request)
    return _change_request_read(
        request,
        latest_revision_number=revision.revision_number,
        latest_diff_summary=revision.diff_summary_json,
    )


@app.get("/v1/change-requests/{request_id}", response_model=ChangeRequestRead)
def get_change_request_endpoint(request_id: str, db: Session = Depends(get_db)):
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    revision = None
    if request.current_revision_id:
        revision = db.scalar(select(ConfigChangeRevision).where(ConfigChangeRevision.revision_id == request.current_revision_id))
    return _change_request_read(
        request,
        latest_revision_number=revision.revision_number if revision else None,
        latest_diff_summary=revision.diff_summary_json if revision else None,
    )


@app.get("/v1/change-requests", response_model=list[ChangeRequestRead])
def list_change_requests_endpoint(
    service_id: str | None = None,
    status: ChangeRequestStatus | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    stmt = select(ConfigChangeRequest).order_by(ConfigChangeRequest.updated_at.desc())
    if service_id:
        stmt = stmt.where(ConfigChangeRequest.service_id == service_id)
    if status:
        stmt = stmt.where(ConfigChangeRequest.status == status)
    requests = db.scalars(stmt).all()
    results: list[ChangeRequestRead] = []
    for request in requests:
        revision = None
        if request.current_revision_id:
            revision = db.scalar(select(ConfigChangeRevision).where(ConfigChangeRevision.revision_id == request.current_revision_id))
        results.append(
            _change_request_read(
                request,
                latest_revision_number=revision.revision_number if revision else None,
                latest_diff_summary=revision.diff_summary_json if revision else None,
            )
        )
    return results


@app.get("/v1/change-requests/{request_id}/activity", response_model=RequestActivityRead)
def get_change_request_activity_endpoint(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    from configsphere_shared.models import ConfigChangeComment, ConfigRevisionReview

    _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    revisions = db.scalars(
        select(ConfigChangeRevision)
        .where(ConfigChangeRevision.request_id == request.request_id)
        .order_by(ConfigChangeRevision.revision_number.desc())
    ).all()
    comments = db.scalars(
        select(ConfigChangeComment)
        .where(ConfigChangeComment.request_id == request.request_id)
        .order_by(ConfigChangeComment.created_at.asc())
    ).all()
    reviews = db.scalars(
        select(ConfigRevisionReview)
        .where(ConfigRevisionReview.request_id == request.request_id)
        .order_by(ConfigRevisionReview.created_at.asc())
    ).all()
    latest_revision = revisions[0] if revisions else None
    request_read = _change_request_read(
        request,
        latest_revision_number=latest_revision.revision_number if latest_revision else None,
        latest_diff_summary=latest_revision.diff_summary_json if latest_revision else None,
    )
    revision_reads: list[RevisionRead] = []
    for revision in revisions:
        revision_doc = payload_store.get_document_by_id("REQUEST", str(request.request_id), revision.proposed_document_id)
        revision_reads.append(
            RevisionRead(
                revision_id=revision.revision_id,
                request_id=revision.request_id,
                revision_number=revision.revision_number,
                proposed_document_id=revision.proposed_document_id,
                diff_summary_json=revision.diff_summary_json,
                proposed_overrides=dict((revision_doc or {}).get("localOverrides", {})),
                base_tree_version=revision.base_tree_version,
                change_note=revision.change_note,
                created_by=revision.created_by,
                created_at=revision.created_at,
            )
        )
    return RequestActivityRead(
        request=request_read,
        revisions=revision_reads,
        comments=[CommentRead.model_validate(comment) for comment in comments],
        reviews=[ReviewRead.model_validate(review) for review in reviews],
    )


@app.post("/v1/change-requests/{request_id}/comments")
def add_comment_endpoint(
    request_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    add_comment(db, request, payload.revision_id, user.user_id, payload.body)
    db.commit()
    return {"status": "ok"}


@app.post("/v1/change-requests/{request_id}/submit", response_model=ChangeRequestRead)
def submit_change_request_endpoint(
    request_id: str,
    payload: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    require_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_AUTHOR, RoleName.CONFIG_ADMIN])
    submit_request(db, request, user.user_id, payload.note)
    db.commit()
    db.refresh(request)
    return _change_request_read(request)


@app.post("/v1/change-requests/{request_id}/review", response_model=ChangeRequestRead)
def review_change_request_endpoint(
    request_id: str,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    require_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_REVIEWER, RoleName.CONFIG_ADMIN])
    is_admin = has_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_ADMIN])
    if request.assigned_reviewer_id and request.assigned_reviewer_id != user.user_id and not is_admin:
        raise HTTPException(status_code=403, detail="This request is assigned to a different reviewer")
    review_request(db, request, payload.revision_id, payload.decision, user.user_id, payload.note)
    db.commit()
    db.refresh(request)
    return _change_request_read(request)


@app.post("/v1/change-requests/{request_id}/cancel", response_model=ChangeRequestRead)
def cancel_change_request_endpoint(
    request_id: str,
    payload: CancelRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    is_author = request.created_by == user.user_id
    is_admin = has_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_ADMIN])
    if not is_author and not is_admin:
        raise HTTPException(status_code=403, detail="Only the author or an admin may cancel this request")
    cancel_request(db, request, user.user_id, payload.note)
    db.commit()
    db.refresh(request)
    return _change_request_read(request)


@app.post("/v1/change-requests/{request_id}/implement", response_model=JobRead)
def implement_change_request_endpoint(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    request = db.scalar(select(ConfigChangeRequest).where(ConfigChangeRequest.request_id == request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Change request not found")
    require_service_role(db, user.user_id, request.service_id, [RoleName.CONFIG_IMPLEMENTER, RoleName.CONFIG_ADMIN])
    service = db.scalar(select(Service).where(Service.service_id == request.service_id))
    job = implement_request(db, request, service, user.user_id, kafka)
    db.commit()
    db.refresh(job)
    return job


@app.post("/v1/rollbacks", response_model=RollbackRead)
def create_rollback_endpoint(
    payload: RollbackCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    require_service_role(db, user.user_id, payload.service_id, [RoleName.CONFIG_AUTHOR, RoleName.CONFIG_ADMIN])
    rollback = create_rollback_request(db, payload.service_id, payload.target_config_node_id, payload.target_version_id, user.user_id)
    db.commit()
    db.refresh(rollback)
    return rollback


@app.post("/v1/rollbacks/{rollback_id}/approve", response_model=RollbackRead)
def approve_rollback_endpoint(
    rollback_id: str,
    payload: RollbackApprove,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    rollback = db.scalar(select(RollbackRequest).where(RollbackRequest.rollback_request_id == rollback_id))
    if not rollback:
        raise HTTPException(status_code=404, detail="Rollback request not found")
    require_service_role(db, user.user_id, rollback.service_id, [RoleName.CONFIG_REVIEWER, RoleName.CONFIG_ADMIN])
    approve_rollback(db, rollback, user.user_id)
    db.commit()
    db.refresh(rollback)
    return rollback


@app.post("/v1/rollbacks/{rollback_id}/implement", response_model=JobRead)
def implement_rollback_endpoint(
    rollback_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = _bootstrap_user(db, current_user)
    rollback = db.scalar(select(RollbackRequest).where(RollbackRequest.rollback_request_id == rollback_id))
    if not rollback:
        raise HTTPException(status_code=404, detail="Rollback request not found")
    require_service_role(db, user.user_id, rollback.service_id, [RoleName.CONFIG_IMPLEMENTER, RoleName.CONFIG_ADMIN])
    job = implement_rollback(db, rollback, user.user_id, kafka)
    db.commit()
    db.refresh(job)
    return job


@app.get("/v1/rollbacks", response_model=list[RollbackRead])
def list_rollbacks_endpoint(
    service_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _bootstrap_user(db, current_user)
    stmt = select(RollbackRequest).order_by(RollbackRequest.updated_at.desc())
    if service_id:
        stmt = stmt.where(RollbackRequest.service_id == service_id)
    return db.scalars(stmt).all()
