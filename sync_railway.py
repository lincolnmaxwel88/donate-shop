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

def check_table_exists(db, table_name):
    """Verifica se uma tabela existe"""
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        print(f"ERRO: Tabela {table_name} não existe!")
        return False
    print(f"OK: Tabela {table_name} existe")
    return True

def check_table_columns(db, table_name):
    """Verifica todas as colunas de uma tabela"""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    print(f"\nColunas da tabela {table_name}:")
    for col in columns:
        print(f"- {col['name']}: {col['type']} (nullable: {col['nullable']})")
    return columns

def ensure_column_exists(db, table_name, column_name, column_type, default=None):
    """Garante que uma coluna existe na tabela"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name not in columns:
        print(f"Adicionando coluna {column_name} na tabela {table_name}...")
        alter_stmt = f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS {column_name} {column_type}'
        if default is not None:
            alter_stmt += f" DEFAULT {default}"
        try:
            db.session.execute(text(alter_stmt))
            db.session.commit()
            print(f"Coluna {column_name} adicionada com sucesso!")
        except Exception as e:
            print(f"ERRO ao adicionar coluna {column_name}: {str(e)}")
            return False
    else:
        print(f"Coluna {column_name} já existe na tabela {table_name}")
    return True

def ensure_index_exists(db, table_name, index_name, column_name, unique=False):
    """Garante que um índice existe na tabela"""
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes(table_name)
    index_exists = any(idx['name'] == index_name for idx in indexes)
    
    if not index_exists:
        print(f"Criando índice {index_name} na tabela {table_name}...")
        unique_str = "UNIQUE" if unique else ""
        try:
            db.session.execute(text(
                f'CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON "{table_name}" ({column_name})'
            ))
            db.session.commit()
            print(f"Índice {index_name} criado com sucesso!")
        except Exception as e:
            print(f"ERRO ao criar índice {index_name}: {str(e)}")
            return False
    else:
        print(f"Índice {index_name} já existe na tabela {table_name}")
    return True

def show_table_data(db, table_name):
    """Mostra os primeiros registros de uma tabela"""
    try:
        result = db.session.execute(text(f'SELECT * FROM "{table_name}" LIMIT 5'))
        rows = result.fetchall()
        if rows:
            print(f"\nPrimeiros registros da tabela {table_name}:")
            for row in rows:
                print(row)
        else:
            print(f"\nTabela {table_name} está vazia")
    except Exception as e:
        print(f"ERRO ao consultar tabela {table_name}: {str(e)}")

def sync_database():
    """Sincroniza o esquema do banco de dados"""
    try:
        from app import app
        db = wait_for_db(app)
        
        print("\nVerificando estrutura do banco de dados...")
        
        # Verificar se a tabela existe
        if not check_table_exists(db, "user"):
            return False
            
        # Mostrar todas as colunas atuais
        check_table_columns(db, "user")
        
        # Garantir que as colunas de ativação existem
        if not ensure_column_exists(db, "user", "is_active", "BOOLEAN", "false"):
            return False
        if not ensure_column_exists(db, "user", "activation_token", "TEXT"):
            return False
        
        # Garantir que o índice único existe
        if not ensure_index_exists(db, "user", "idx_user_activation_token", "activation_token", unique=True):
            return False
            
        # Verificar dados
        show_table_data(db, "user")
        
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
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"ERRO: Variável {var} não está definida!")
        else:
            # Mostrar parte da senha para debug
            if var == 'MAIL_PASSWORD':
                masked_value = value[:3] + '*' * (len(value) - 3)
                print(f"OK: Variável {var} está definida como: {masked_value}")
            else:
                print(f"OK: Variável {var} está definida como: {value}")
    
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
