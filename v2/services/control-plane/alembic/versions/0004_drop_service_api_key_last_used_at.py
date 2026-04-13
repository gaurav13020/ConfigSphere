"""drop service api key last_used_at

Revision ID: 0004_drop_last_used
Revises: 0003_service_api_keys
Create Date: 2026-04-11 17:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_drop_last_used"
down_revision = "0003_service_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0001_initial uses create_all() from the current ORM which already omits
    # last_used_at, so the column may not exist.  Only drop if present.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'service_api_keys'
                      AND column_name = 'last_used_at'
                ) THEN
                    ALTER TABLE service_api_keys DROP COLUMN last_used_at;
                END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    op.add_column("service_api_keys", sa.Column("last_used_at", sa.DateTime(), nullable=True))
