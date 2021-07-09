"""fix_order

Revision ID: 774308e0e7f1
Revises: 28900bd5090c
Create Date: 2021-06-27 17:21:26.926668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '774308e0e7f1'
down_revision = '28900bd5090c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('order', sa.Column('bill', sa.String(length=1024), nullable=True))
    op.add_column('order', sa.Column('payment_type', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('order', 'payment_type')
    op.drop_column('order', 'bill')
