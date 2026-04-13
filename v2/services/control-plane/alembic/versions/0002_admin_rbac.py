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
    # The unique constraint and index are already created by 0001_initial via
    # Base.metadata.create_all(), which picks up the ORM-level UniqueConstraint and
    # Index definitions on the UserRoleBinding model.  Use existence-check guards so
    # this migration is idempotent when applied on top of a create_all bootstrap.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_user_role_binding_scope'
                ) THEN
                    ALTER TABLE user_role_bindings
                        ADD CONSTRAINT uq_user_role_binding_scope
                        UNIQUE (user_id, role_id, scope_type, scope_id);
                END IF;
            END $$;
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_user_role_bindings_user_scope "
            "ON user_role_bindings (user_id, scope_type, scope_id)"
        )
    )

    # rbac_audit_events is already created by 0001_initial's create_all; guard with
    # IF NOT EXISTS so this migration is idempotent.
    conn.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS rbac_audit_events (
                audit_event_id  UUID        NOT NULL,
                actor_user_id   UUID        NOT NULL,
                target_user_id  UUID        NOT NULL,
                role_id         UUID        NOT NULL,
                scope_type      VARCHAR(50) NOT NULL,
                scope_id        UUID,
                action          VARCHAR(50) NOT NULL,
                note            TEXT,
                created_at      TIMESTAMP   NOT NULL,
                CONSTRAINT pk_rbac_audit_events PRIMARY KEY (audit_event_id),
                CONSTRAINT fk_rbac_audit_events_actor_user_id_users
                    FOREIGN KEY (actor_user_id) REFERENCES users (user_id),
                CONSTRAINT fk_rbac_audit_events_target_user_id_users
                    FOREIGN KEY (target_user_id) REFERENCES users (user_id),
                CONSTRAINT fk_rbac_audit_events_role_id_roles
                    FOREIGN KEY (role_id) REFERENCES roles (role_id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_rbac_audit_events_target_created "
            "ON rbac_audit_events (target_user_id, created_at)"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_rbac_audit_events_target_created", table_name="rbac_audit_events")
    op.drop_table("rbac_audit_events")
    op.drop_index("ix_user_role_bindings_user_scope", table_name="user_role_bindings")
    op.drop_constraint("uq_user_role_binding_scope", "user_role_bindings", type_="unique")
