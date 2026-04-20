"""add_invoice_snapshot

Revision ID: 42ce90daf3fe
Revises:
Create Date: 2026-04-20 12:23:16.368262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42ce90daf3fe'
down_revision: Union[str, None] = '262bafd6381b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'invoice_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('num_days', sa.Integer(), nullable=False),
        sa.Column('stay_rate', sa.Float(), nullable=True),
        sa.Column('accommodation_cost', sa.Float(), nullable=False),
        sa.Column('electricity_kwh', sa.Float(), nullable=True),
        sa.Column('elec_rate', sa.Float(), nullable=True),
        sa.Column('electricity_cost', sa.Float(), nullable=False),
        sa.Column('gas_kwh', sa.Float(), nullable=True),
        sa.Column('gas_cubic_meters', sa.Float(), nullable=True),
        sa.Column('gas_rate', sa.Float(), nullable=True),
        sa.Column('gas_cost', sa.Float(), nullable=False),
        sa.Column('firewood_boxes', sa.Integer(), nullable=True),
        sa.Column('firewood_rate', sa.Float(), nullable=True),
        sa.Column('firewood_cost', sa.Float(), nullable=False),
        sa.Column('kurtaxe_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id'),
    )
    op.create_index(op.f('ix_invoice_snapshots_id'), 'invoice_snapshots', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_invoice_snapshots_id'), table_name='invoice_snapshots')
    op.drop_table('invoice_snapshots')
