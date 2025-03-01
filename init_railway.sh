#!/bin/bash

# Executar SQL para adicionar colunas
echo "Adicionando colunas de ativação..."
psql $DATABASE_URL << 'EOSQL'
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS activation_token TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_activation_token ON "user" (activation_token);
EOSQL

# Iniciar a aplicação
python migrations/railway_migrate.py && gunicorn app:app
