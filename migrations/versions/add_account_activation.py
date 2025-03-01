"""add account activation

Revision ID: add_account_activation
Revises: increase_password_hash
Create Date: 2024-03-01 02:52:18.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_account_activation'
down_revision = 'increase_password_hash'
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar coluna is_active
    op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'))
    
    # Adicionar coluna activation_token
    op.add_column('user', sa.Column('activation_token', sa.String(length=100), nullable=True))
    
    # Criar índice único para activation_token
    op.create_unique_constraint('uq_user_activation_token', 'user', ['activation_token'])

def downgrade():
    # Remover índice
    op.drop_constraint('uq_user_activation_token', 'user', type_='unique')
    
    # Remover colunas
    op.drop_column('user', 'activation_token')
    op.drop_column('user', 'is_active')
