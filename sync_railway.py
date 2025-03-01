import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
import time

def wait_for_db(app, max_retries=30):
    """Espera o banco de dados ficar disponível"""
    print("Verificando conexão com o banco de dados...")
    for i in range(max_retries):
        try:
            with app.app_context():
                db = SQLAlchemy(app)
                db.session.execute(text('SELECT 1'))
                db.session.commit()
                print("Conexão com o banco de dados estabelecida!")
                return db
        except Exception as e:
            if i < max_retries - 1:
                print(f"Tentativa {i+1}/{max_retries}: Aguardando banco de dados... ({str(e)})")
                time.sleep(1)
            else:
                print(f"Erro ao conectar ao banco de dados após {max_retries} tentativas")
                raise
    return None

def ensure_column_exists(db, table_name, column_name, column_type, default=None):
    """Garante que uma coluna existe na tabela"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name not in columns:
        print(f"Adicionando coluna {column_name} na tabela {table_name}...")
        alter_stmt = f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS {column_name} {column_type}'
        if default is not None:
            alter_stmt += f" DEFAULT {default}"
        db.session.execute(text(alter_stmt))
        db.session.commit()
        print(f"Coluna {column_name} adicionada com sucesso!")
    else:
        print(f"Coluna {column_name} já existe na tabela {table_name}")

def ensure_index_exists(db, table_name, index_name, column_name, unique=False):
    """Garante que um índice existe na tabela"""
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes(table_name)
    index_exists = any(idx['name'] == index_name for idx in indexes)
    
    if not index_exists:
        print(f"Criando índice {index_name} na tabela {table_name}...")
        unique_str = "UNIQUE" if unique else ""
        db.session.execute(text(
            f'CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON "{table_name}" ({column_name})'
        ))
        db.session.commit()
        print(f"Índice {index_name} criado com sucesso!")
    else:
        print(f"Índice {index_name} já existe na tabela {table_name}")

def sync_database():
    """Sincroniza o esquema do banco de dados"""
    try:
        from app import app
        db = wait_for_db(app)
        
        print("\nVerificando estrutura do banco de dados...")
        
        # Garantir que as colunas de ativação existem
        ensure_column_exists(db, "user", "is_active", "BOOLEAN", "false")
        ensure_column_exists(db, "user", "activation_token", "TEXT")
        
        # Garantir que o índice único existe
        ensure_index_exists(db, "user", "idx_user_activation_token", "activation_token", unique=True)
        
        print("\nBanco de dados sincronizado com sucesso!")
        return True
        
    except Exception as e:
        print(f"\nErro ao sincronizar banco de dados: {str(e)}")
        return False

def verify_env_vars():
    """Verifica se todas as variáveis de ambiente necessárias estão definidas"""
    required_vars = [
        'DATABASE_URL',
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USE_TLS',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
        'SECRET_KEY'
    ]
    
    print("\nVerificando variáveis de ambiente...")
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"ERRO: Variável {var} não está definida!")
        else:
            print(f"OK: Variável {var} está definida")
    
    if missing_vars:
        print("\nATENÇÃO: As seguintes variáveis precisam ser configuradas:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nConfigure estas variáveis no painel do Railway!")
        return False
    
    print("\nTodas as variáveis de ambiente necessárias estão configuradas!")
    return True

if __name__ == '__main__':
    print("=== Iniciando sincronização com Railway ===\n")
    
    db_success = sync_database()
    env_success = verify_env_vars()
    
    if db_success and env_success:
        print("\n✅ Sincronização concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Sincronização concluída com erros!")
        sys.exit(1)
