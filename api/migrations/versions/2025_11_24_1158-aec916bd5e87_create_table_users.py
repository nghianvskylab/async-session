"""create table users

Revision ID: aec916bd5e87
Revises:
Create Date: 2025-11-24 11:58:20.349955

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "aec916bd5e87"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE userpermission AS ENUM ('ADMIN', 'USER');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "permission",
            postgresql.ENUM("ADMIN", "USER", name="userpermission", create_type=False),
            nullable=False,
        ),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
    )

    # Create indexes
    op.create_index("ix_users_name", "users", ["name"])
    op.create_index("ix_users_permission", "users", ["permission"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # Create GIN index for full-text search (using default operator class)
    op.execute("CREATE INDEX idx_user_name_bigm ON users USING gin (name gin_trgm_ops)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_user_name_bigm", table_name="users")
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_permission", table_name="users")
    op.drop_index("ix_users_name", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userpermission")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
