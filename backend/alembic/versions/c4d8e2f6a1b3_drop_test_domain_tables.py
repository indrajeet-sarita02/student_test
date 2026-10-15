"""drop test-domain tables

Removes the test-assembly / exam-taking subsystem from the schema:

    attempt_answers -> results -> attempts -> test_questions
        -> test_assignments -> tests

Children are dropped before their parents so the foreign keys resolve cleanly
on PostgreSQL (and ``IF EXISTS`` keeps the migration idempotent for databases
that never created the tables).

Revision ID: c4d8e2f6a1b3
Revises: 601b261c5185
Create Date: 2026-10-13 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d8e2f6a1b3"
down_revision: Union[str, Sequence[str], None] = "601b261c5185"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Dropped child-first so referenced tables still exist when each FK goes away.
_DROP_ORDER = (
    "attempt_answers",
    "results",
    "attempts",
    "test_questions",
    "test_assignments",
    "tests",
)


def upgrade() -> None:
    for table in _DROP_ORDER:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    # The schema is intentionally non-reversible: the removed subsystem is no
    # longer part of the application.  Recreate it from the initial-schema
    # revision (``601b261c5185``) if the tables are ever needed again.
    raise NotImplementedError(
        "Dropping the test-domain tables is not reversible; restore the schema "
        "from revision 601b261c5185 if required."
    )
