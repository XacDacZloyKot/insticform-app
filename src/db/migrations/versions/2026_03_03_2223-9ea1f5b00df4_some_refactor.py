"""Some refactor

Revision ID: 9ea1f5b00df4
Revises: 9c7b57dfa0c1
Create Date: 2026-03-03 22:23:21.567980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ea1f5b00df4'
down_revision: Union[str, Sequence[str], None] = '9c7b57dfa0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_proctoring_events_attempt_id'), table_name='proctoring_events')
    op.create_index('ix_proctoring_event_attempt_timestamp', 'proctoring_events', ['attempt_id', 'timestamp'], unique=False)
    op.add_column('questions', sa.Column('media_type', sa.Enum('IMAGE', 'VIDEO', 'AUDIO', name='mediatype'), nullable=True))

    # ИСПОЛЬЗУЕМ BATCH ДЛЯ SQLITE
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('patronymic',
                   existing_type=sa.VARCHAR(length=64),
                   nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # ИСПОЛЬЗУЕМ BATCH ДЛЯ SQLITE
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('patronymic',
                   existing_type=sa.VARCHAR(length=64),
                   nullable=False)

    op.drop_column('questions', 'media_type')
    op.drop_index('ix_proctoring_event_attempt_timestamp', table_name='proctoring_events')
    op.create_index(op.f('ix_proctoring_events_attempt_id'), 'proctoring_events', ['attempt_id'], unique=False)