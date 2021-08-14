"""creating_cost_pair

Revision ID: 5536c11a51a7
Revises: ee3ab8f48115
Create Date: 2021-08-14 11:54:22.979483

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5536c11a51a7'
down_revision = 'ee3ab8f48115'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cost_pair',
        sa.Column('pair', sa.String(length=20), nullable=False),
        sa.Column('cost', sa.DECIMAL(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('pair')
    )
    op.create_unique_constraint(None, 'e_wallets', ['identifier'])


def downgrade():
    op.drop_constraint(None, 'e_wallets', type_='unique')
    op.drop_table('cost_pair')
