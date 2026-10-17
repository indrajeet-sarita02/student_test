"""add question tags

Revision ID: b7f3d9a4c210
Revises: 601b261c5185
Create Date: 2026-10-17 00:00:00.000000

Adds the free-form ``tags`` JSONB array column to ``questions`` used to label
and filter the question bank.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7f3d9a4c210'
down_revision: Union[str, Sequence[str], None] = '601b261c5185'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the ``questions.tags`` column."""
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'tags',
                postgresql.JSONB(astext_type=sa.Text()).with_variant(
                    sa.JSON(), 'sqlite'
                ),
                nullable=True,
            )
        )


def downgrade() -> None:
    """Drop the ``questions.tags`` column."""
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_column('tags')
