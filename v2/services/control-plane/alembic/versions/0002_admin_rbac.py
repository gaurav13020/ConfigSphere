"""admin rbac tables and constraints

Revision ID: 0002_admin_rbac
Revises: 0001_initial
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_admin_rbac"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_user_role_binding_scope",
        "user_role_bindings",
        ["user_id", "role_id", "scope_type", "scope_id"],
    )
    op.create_index(
        "ix_user_role_bindings_user_scope",
        "user_role_bindings",
        ["user_id", "scope_type", "scope_id"],
        unique=False,
    )

    op.create_table(
        "rbac_audit_events",
        sa.Column("audit_event_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope_type", sa.String(length=50), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.user_id"], name="fk_rbac_audit_events_actor_user_id_users"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.user_id"], name="fk_rbac_audit_events_target_user_id_users"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], name="fk_rbac_audit_events_role_id_roles"),
    )
    op.create_index(
        "ix_rbac_audit_events_target_created",
        "rbac_audit_events",
        ["target_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rbac_audit_events_target_created", table_name="rbac_audit_events")
    op.drop_table("rbac_audit_events")
    op.drop_index("ix_user_role_bindings_user_scope", table_name="user_role_bindings")
    op.drop_constraint("uq_user_role_binding_scope", "user_role_bindings", type_="unique")
