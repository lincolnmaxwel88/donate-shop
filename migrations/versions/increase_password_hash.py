"""increase password hash length

Revision ID: increase_password_hash
Revises: 
Create Date: 2025-03-01 02:14:50.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'increase_password_hash'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Alterar o tamanho do campo password_hash
    op.alter_column('user', 'password_hash',
        existing_type=sa.String(128),
        type_=sa.String(256),
        existing_nullable=True)

def downgrade():
    # Voltar para o tamanho original
    op.alter_column('user', 'password_hash',
        existing_type=sa.String(256),
        type_=sa.String(128),
        existing_nullable=True)
