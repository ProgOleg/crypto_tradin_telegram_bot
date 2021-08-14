"""fees

Revision ID: 47365b2354ff
Revises: 5536c11a51a7
Create Date: 2021-08-14 20:14:06.101828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47365b2354ff'
down_revision = '5536c11a51a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fees',
        sa.Column('coin', sa.String(length=255), nullable=False),
        sa.Column('min_deposit', sa.DECIMAL(), nullable=False),
        sa.Column('fees_amount', sa.DECIMAL(), nullable=False),
        sa.Column('fees_type', sa.String(length=20), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('coin')
    )


def downgrade():
    op.drop_table('fees')
