"""create table post

Revision ID: aec916bd5e87
Revises: 
Create Date: 2025-11-24 11:58:20.349955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aec916bd5e87'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create posts table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hash', sa.String(), nullable=False),
        sa.Column('salt', sa.String(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='posts_pkey')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
