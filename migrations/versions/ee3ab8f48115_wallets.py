"""wallets

Revision ID: ee3ab8f48115
Revises: 171231fc0663
Create Date: 2021-07-17 16:36:57.341482

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee3ab8f48115'
down_revision = '171231fc0663'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'e_wallets',
        sa.Column('identifier', sa.String(length=10), nullable=False),
        sa.Column('wallet', sa.String(length=1024), nullable=False),
        sa.Column('memo', sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint('identifier'),
        sa.UniqueConstraint('identifier')
    )


def downgrade():
    op.drop_table('e_wallets')
