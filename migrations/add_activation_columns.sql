-- Adicionar coluna is_active
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

-- Adicionar coluna activation_token
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS activation_token VARCHAR(100);

-- Criar índice único para activation_token
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_activation_token ON "user" (activation_token);
