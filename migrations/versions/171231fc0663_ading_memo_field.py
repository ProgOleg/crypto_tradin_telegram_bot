"""ading_memo_field

Revision ID: 171231fc0663
Revises: 774308e0e7f1
Create Date: 2021-07-17 14:55:12.404876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '171231fc0663'
down_revision = '774308e0e7f1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('order', sa.Column('memo', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('order', 'memo')
