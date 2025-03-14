"""consistent naming: guest_id

Revision ID: 0044ed6bf938
Revises: 5122b986776f
Create Date: 2025-03-12 16:48:03.655664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0044ed6bf938'
down_revision: Union[str, None] = '5122b986776f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bookings', sa.Column('guest_id', sa.Integer(), nullable=True))
    op.drop_constraint('bookings_user_id_fkey', 'bookings', type_='foreignkey')
    op.create_foreign_key(None, 'bookings', 'guests', ['guest_id'], ['id'])
    op.drop_column('bookings', 'user_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bookings', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'bookings', type_='foreignkey')
    op.create_foreign_key('bookings_user_id_fkey', 'bookings', 'guests', ['user_id'], ['id'])
    op.drop_column('bookings', 'guest_id')
    # ### end Alembic commands ###
