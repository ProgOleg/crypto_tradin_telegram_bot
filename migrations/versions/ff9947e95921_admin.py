"""admin

Revision ID: ff9947e95921
Revises: 15f6fa38d265
Create Date: 2021-05-30 01:27:49.079345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff9947e95921'
down_revision = '15f6fa38d265'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admins',
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('chat_id')
    )
    op.create_table('settings',
    sa.Column('markup', sa.DECIMAL(), nullable=False),
    sa.PrimaryKeyConstraint('markup')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('settings')
    op.drop_table('admins')
    # ### end Alembic commands ###
