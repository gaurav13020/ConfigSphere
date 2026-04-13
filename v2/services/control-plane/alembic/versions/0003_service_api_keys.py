"""service api keys

Revision ID: 0003_service_api_keys
Revises: 0002_admin_rbac
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_service_api_keys"
down_revision = "0002_admin_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # service_api_keys (without last_used_at) is already created by 0001_initial via
    # Base.metadata.create_all().  Use IF NOT EXISTS / existence guards for idempotency.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS service_api_keys (
                api_key_id   UUID         NOT NULL,
                service_id   UUID         NOT NULL,
                key_name     VARCHAR(200) NOT NULL,
                token_prefix VARCHAR(32)  NOT NULL,
                token_hash   VARCHAR(128) NOT NULL,
                created_by   UUID,
                last_used_at TIMESTAMP,
                revoked_at   TIMESTAMP,
                created_at   TIMESTAMP    NOT NULL,
                CONSTRAINT pk_service_api_keys PRIMARY KEY (api_key_id),
                CONSTRAINT fk_service_api_keys_service_id_services
                    FOREIGN KEY (service_id) REFERENCES services (service_id),
                CONSTRAINT fk_service_api_keys_created_by_users
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_service_api_keys_service_created "
            "ON service_api_keys (service_id, created_at)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_service_api_keys_token_hash "
            "ON service_api_keys (token_hash)"
        )
    )
    conn.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_service_api_keys_token_hash'
                ) THEN
                    ALTER TABLE service_api_keys
                        ADD CONSTRAINT uq_service_api_keys_token_hash UNIQUE (token_hash);
                END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("uq_service_api_keys_token_hash", "service_api_keys", type_="unique")
    op.drop_index("ix_service_api_keys_token_hash", table_name="service_api_keys")
    op.drop_index("ix_service_api_keys_service_created", table_name="service_api_keys")
    op.drop_table("service_api_keys")
