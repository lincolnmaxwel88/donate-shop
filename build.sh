#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências
pip install -r requirements.txt

# Criar diretórios necessários
mkdir -p static/uploads
mkdir -p static/img

# Inicializar o banco de dados
python init_db.py
