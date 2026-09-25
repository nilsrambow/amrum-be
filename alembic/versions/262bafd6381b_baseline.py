"""baseline

Revision ID: 262bafd6381b
Revises:
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '262bafd6381b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

booking_status = postgresql.ENUM(
    'NEW', 'CONFIRMED', 'KURKARTEN_REQUESTED', 'READY_FOR_ARRIVAL',
    'ARRIVING', 'ON_SITE', 'DEPARTING', 'DEPARTED_READINGS_DUE',
    'DEPARTED_INVOICE_DUE', 'DEPARTED_PAYMENT_DUE', 'DEPARTED_DONE',
    name='bookingstatus',
    create_type=False,
)

price_type = postgresql.ENUM(
    'ELECTRICITY_PER_KWH', 'STAY_PER_NIGHT', 'GAS_PER_CUBIC_METER', 'FIREWOOD_PER_BOX',
    name='pricetype',
    create_type=False,
)


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bookingstatus AS ENUM ('NEW', 'CONFIRMED', 'KURKARTEN_REQUESTED', 'READY_FOR_ARRIVAL', 'ARRIVING', 'ON_SITE', 'DEPARTING', 'DEPARTED_READINGS_DUE', 'DEPARTED_INVOICE_DUE', 'DEPARTED_PAYMENT_DUE', 'DEPARTED_DONE');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pricetype AS ENUM ('ELECTRICITY_PER_KWH', 'STAY_PER_NIGHT', 'GAS_PER_CUBIC_METER', 'FIREWOOD_PER_BOX');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)

    op.create_table(
        'guests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('pays_dayrate', sa.Boolean(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('modified_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_guests_email'), 'guests', ['email'], unique=True)
    op.create_index(op.f('ix_guests_id'), 'guests', ['id'], unique=False)

    op.create_table(
        'unit_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('price_type', price_type, nullable=False),
        sa.Column('price_per_unit', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('modified_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_unit_prices_id'), 'unit_prices', ['id'], unique=False)

    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_admin_users_id'), 'admin_users', ['id'], unique=False)
    op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True)
    op.create_index(op.f('ix_admin_users_email'), 'admin_users', ['email'], unique=True)

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_id', sa.Integer(), nullable=True),
        sa.Column('check_in', sa.Date(), nullable=True),
        sa.Column('check_out', sa.Date(), nullable=True),
        sa.Column('confirmed', sa.Boolean(), nullable=True),
        sa.Column('final_info_sent', sa.Boolean(), nullable=True),
        sa.Column('invoice_created', sa.Boolean(), nullable=True),
        sa.Column('invoice_sent', sa.Boolean(), nullable=True),
        sa.Column('paid', sa.Boolean(), nullable=True),
        sa.Column('status', booking_status, nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('kurkarten_email_sent', sa.Boolean(), nullable=True),
        sa.Column('kurkarten_email_sent_date', sa.DateTime(), nullable=True),
        sa.Column('pre_arrival_email_sent', sa.Boolean(), nullable=True),
        sa.Column('pre_arrival_email_sent_date', sa.DateTime(), nullable=True),
        sa.Column('kurtaxe_amount', sa.Float(), nullable=True),
        sa.Column('kurtaxe_notes', sa.Text(), nullable=True),
        sa.Column('invoice_id', sa.String(), nullable=True),
        sa.Column('invoice_sent_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('modified_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('check_out > check_in', name='check_out_after_check_in'),
        sa.ForeignKeyConstraint(['guest_id'], ['guests.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_index(op.f('ix_bookings_access_token'), 'bookings', ['access_token'], unique=True)

    op.create_table(
        'booking_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_booking_tokens_id'), 'booking_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_booking_tokens_token'), 'booking_tokens', ['token'], unique=True)

    op.create_table(
        'meter_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('electricity_start', sa.Float(), nullable=True),
        sa.Column('electricity_end', sa.Float(), nullable=True),
        sa.Column('gas_start', sa.Float(), nullable=True),
        sa.Column('gas_end', sa.Float(), nullable=True),
        sa.Column('firewood_boxes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('modified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id'),
    )
    op.create_index(op.f('ix_meter_readings_id'), 'meter_readings', ['id'], unique=False)

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('modified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('meter_readings')
    op.drop_table('booking_tokens')
    op.drop_table('bookings')
    op.drop_table('admin_users')
    op.drop_table('unit_prices')
    op.drop_table('guests')
    booking_status.drop(op.get_bind(), checkfirst=True)
    price_type.drop(op.get_bind(), checkfirst=True)
