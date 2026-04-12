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
    op.create_table(
        "service_api_keys",
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_name", sa.String(length=200), nullable=False),
        sa.Column("token_prefix", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.service_id"], name="fk_service_api_keys_service_id_services"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], name="fk_service_api_keys_created_by_users"),
    )
    op.create_index(
        "ix_service_api_keys_service_created",
        "service_api_keys",
        ["service_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_service_api_keys_token_hash",
        "service_api_keys",
        ["token_hash"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_service_api_keys_token_hash",
        "service_api_keys",
        ["token_hash"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_service_api_keys_token_hash", "service_api_keys", type_="unique")
    op.drop_index("ix_service_api_keys_token_hash", table_name="service_api_keys")
    op.drop_index("ix_service_api_keys_service_created", table_name="service_api_keys")
    op.drop_table("service_api_keys")
