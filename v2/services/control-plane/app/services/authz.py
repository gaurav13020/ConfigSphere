from __future__ import annotations

import os
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from configsphere_shared.constants import RoleName, ScopeType
from configsphere_shared.models import RbacAuditEvent, Role, User, UserRoleBinding
from configsphere_shared.security import AuthenticatedUser


def get_or_create_user(db: Session, current_user: AuthenticatedUser) -> User:
    user = db.scalar(select(User).where(User.external_subject == current_user.subject))
    if user:
        if user.email != current_user.email or user.display_name != current_user.display_name:
            user.email = current_user.email
            user.display_name = current_user.display_name
            db.add(user)
        return user

    user = User(
        email=current_user.email,
        display_name=current_user.display_name,
        external_subject=current_user.subject,
    )
    db.add(user)
    db.flush()
    return user


def ensure_role_seed(db: Session) -> None:
    existing = {role.role_name for role in db.scalars(select(Role)).all()}
    for role_name in RoleName:
        if role_name not in existing:
            db.add(Role(role_name=role_name))
    db.flush()


def ensure_dev_bindings(db: Session, user: User) -> None:
    dev_mode = os.getenv("AUTH_DEV_MODE", "true").lower() == "true"
    if not dev_mode or not user.external_subject.startswith("dev::"):
        return

    existing_role_names = {
        role_name
        for role_name in db.scalars(
            select(Role.role_name)
            .join(UserRoleBinding, UserRoleBinding.role_id == Role.role_id)
            .where(UserRoleBinding.user_id == user.user_id)
            .where(UserRoleBinding.scope_type == ScopeType.GLOBAL)
        ).all()
    }
    role_map = {
        role.role_name: role
        for role in db.scalars(select(Role).where(Role.role_name.in_(list(RoleName)))).all()
    }

    for role_name in RoleName:
        if role_name in existing_role_names:
            continue
        db.add(
            UserRoleBinding(
                user_id=user.user_id,
                role_id=role_map[role_name].role_id,
                scope_type=ScopeType.GLOBAL,
                scope_id=None,
            )
        )
    db.flush()


def require_service_role(db: Session, user_id: UUID, service_id: UUID, accepted_roles: list[RoleName]) -> None:
    stmt = (
        select(UserRoleBinding)
        .join(Role, Role.role_id == UserRoleBinding.role_id)
        .where(UserRoleBinding.user_id == user_id)
        .where(Role.role_name.in_(accepted_roles))
    )
    bindings = db.scalars(stmt).all()
    for binding in bindings:
        if binding.scope_type == ScopeType.GLOBAL:
            return
        if binding.scope_type == ScopeType.SERVICE and binding.scope_id == service_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role binding for service")


def count_global_admins(db: Session) -> int:
    return db.scalar(
        select(func.count(UserRoleBinding.binding_id))
        .join(Role, Role.role_id == UserRoleBinding.role_id)
        .where(Role.role_name == RoleName.CONFIG_ADMIN)
        .where(UserRoleBinding.scope_type == ScopeType.GLOBAL)
    ) or 0


def require_global_admin(db: Session, user_id: UUID) -> None:
    binding = db.scalar(
        select(UserRoleBinding)
        .join(Role, Role.role_id == UserRoleBinding.role_id)
        .where(UserRoleBinding.user_id == user_id)
        .where(UserRoleBinding.scope_type == ScopeType.GLOBAL)
        .where(Role.role_name == RoleName.CONFIG_ADMIN)
    )
    if not binding:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Global admin role required")


def grant_role_binding(
    db: Session,
    actor_user_id: UUID,
    target_user_id: UUID,
    role_name: RoleName,
    scope_type: ScopeType,
    scope_id: UUID | None,
    note: str | None = None,
) -> UserRoleBinding:
    if scope_type == ScopeType.GLOBAL:
        scope_id = None
    elif scope_type == ScopeType.SERVICE and scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope_id is required for service-scoped bindings")

    role = db.scalar(select(Role).where(Role.role_name == role_name))
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role {role_name} not found")

    existing = db.scalar(
        select(UserRoleBinding).where(
            UserRoleBinding.user_id == target_user_id,
            UserRoleBinding.role_id == role.role_id,
            UserRoleBinding.scope_type == scope_type,
            UserRoleBinding.scope_id == scope_id,
        )
    )
    if existing:
        return existing

    binding = UserRoleBinding(
        user_id=target_user_id,
        role_id=role.role_id,
        scope_type=scope_type,
        scope_id=scope_id,
    )
    db.add(binding)
    db.flush()
    db.add(
        RbacAuditEvent(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            role_id=role.role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            action="GRANTED",
            note=note,
        )
    )
    db.flush()
    return binding


def revoke_role_binding(db: Session, actor_user_id: UUID, binding: UserRoleBinding, note: str | None = None) -> None:
    admin_role = db.scalar(select(Role).where(Role.role_name == RoleName.CONFIG_ADMIN))
    if admin_role and binding.role_id == admin_role.role_id and binding.scope_type == ScopeType.GLOBAL:
        remaining_admins = db.scalar(
            select(func.count(UserRoleBinding.binding_id)).where(
                UserRoleBinding.role_id == admin_role.role_id,
                UserRoleBinding.scope_type == ScopeType.GLOBAL,
            )
        ) or 0
        if remaining_admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot remove the last global admin")

    db.add(
        RbacAuditEvent(
            actor_user_id=actor_user_id,
            target_user_id=binding.user_id,
            role_id=binding.role_id,
            scope_type=binding.scope_type,
            scope_id=binding.scope_id,
            action="REVOKED",
            note=note,
        )
    )
    db.delete(binding)


def list_role_bindings_for_user(db: Session, user_id: UUID) -> list[tuple[UserRoleBinding, RoleName]]:
    rows = db.execute(
        select(UserRoleBinding, Role.role_name)
        .join(Role, Role.role_id == UserRoleBinding.role_id)
        .where(UserRoleBinding.user_id == user_id)
        .order_by(UserRoleBinding.created_at.asc())
    ).all()
    return [(binding, role_name) for binding, role_name in rows]


def has_service_role(db: Session, user_id: UUID, service_id: UUID, accepted_roles: list[RoleName]) -> bool:
    stmt = (
        select(UserRoleBinding, Role.role_name)
        .join(Role, Role.role_id == UserRoleBinding.role_id)
        .where(UserRoleBinding.user_id == user_id)
        .where(Role.role_name.in_(accepted_roles))
    )
    for binding, _role_name in db.execute(stmt).all():
        if binding.scope_type == ScopeType.GLOBAL:
            return True
        if binding.scope_type == ScopeType.SERVICE and binding.scope_id == service_id:
            return True
    return False
