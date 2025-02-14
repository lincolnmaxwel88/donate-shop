#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências
pip install -r requirements.txt

# Criar diretórios necessários se não existirem
mkdir -p static/uploads
mkdir -p static/img

# Dar permissões aos diretórios
chmod -R 755 static/uploads
chmod -R 755 static/img

# Inicializar o banco de dados
python init_db.py
