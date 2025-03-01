#!/bin/bash

# Esperar o PostgreSQL ficar disponível
echo "Aguardando PostgreSQL..."
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

# Pegar a URL do banco
db_url = os.getenv('DATABASE_URL', '')
if not db_url:
    print("ERROR: DATABASE_URL não está definida!")
    sys.exit(1)

# Converter postgres:// para postgresql://
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

# Extrair informações de conexão
result = urlparse(db_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Tentar conectar
for i in range(30):  # Tenta por 30 segundos
    try:
        print(f"Tentativa {i+1} de conectar ao PostgreSQL...")
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.close()
        print("Conexão com PostgreSQL estabelecida!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"Aguardando PostgreSQL... ({str(e)})")
        time.sleep(1)

print("ERROR: Não foi possível conectar ao PostgreSQL!")
sys.exit(1)
END

# Se o script Python saiu com erro, não continua
if [ $? -ne 0 ]; then
    echo "Erro ao conectar ao PostgreSQL. Abortando..."
    exit 1
fi

# Inicializar o banco
echo "Inicializando banco de dados..."
python init_db.py

# Se init_db.py falhou, não continua
if [ $? -ne 0 ]; then
    echo "Erro ao inicializar banco de dados. Abortando..."
    exit 1
fi

# Iniciar o servidor
echo "Iniciando servidor Gunicorn..."
gunicorn -c gunicorn_config.py app:app
