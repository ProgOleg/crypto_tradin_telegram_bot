"""first_migration

Revision ID: 15f6fa38d265
Revises: 
Create Date: 2021-04-18 16:10:25.966751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15f6fa38d265'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=True),
        sa.Column('language', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('chat_id')
    )
    op.create_table('order',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False, start=1000, increment=1), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('quantity', sa.DECIMAL(), nullable=False),
        sa.Column('exchange_type', sa.String(length=255), nullable=False),
        sa.Column('crypto', sa.String(length=255), nullable=False),
        sa.Column('fiat', sa.String(length=255), nullable=False),
        sa.Column('cr_date', sa.DateTime(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('success_date', sa.DateTime(), nullable=True),
        sa.Column('approve', sa.Boolean(), nullable=True),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.chat_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('order')
    op.drop_table('user')
    # ### end Alembic commands ###
