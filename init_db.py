from app import app, db, User, SystemConfig
import os
import time
from sqlalchemy import text, DDL
from sqlalchemy.exc import OperationalError

def wait_for_db():
    """Espera o banco de dados ficar disponível"""
    max_retries = 30
    for i in range(max_retries):
        try:
            # Tenta fazer uma consulta simples
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                db.session.commit()
                return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"Aguardando banco de dados... ({str(e)})")
                time.sleep(1)
            else:
                print(f"Erro ao conectar ao banco de dados após {max_retries} tentativas")
                return False
    return False

def init_db():
    print("Inicializando banco de dados...")
    
    # Mostrar a URL do banco (ocultando a senha)
    db_url = os.getenv('DATABASE_URL', '')
    if '@' in db_url:
        # Oculta a senha na URL para logging
        safe_url = db_url.split('@')
        credentials = safe_url[0].split(':')
        safe_url = f"{credentials[0]}:****@{safe_url[1]}"
        print(f"Database URL: {safe_url}")
    
    # Espera o banco ficar disponível
    if not wait_for_db():
        print("Não foi possível conectar ao banco de dados")
        return False
    
    try:
        with app.app_context():
            # Criar tabelas
            print("Criando tabelas...")
            db.create_all()
            
            # Alterar o tamanho do campo password_hash
            print("Alterando tamanho do campo password_hash...")
            try:
                if 'sqlite' in str(db.engine.url):
                    # SQLite não suporta ALTER COLUMN, precisamos recriar a tabela
                    db.session.execute(text("""
                        CREATE TABLE IF NOT EXISTS user_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username VARCHAR(80) NOT NULL UNIQUE,
                            email VARCHAR(120) NOT NULL UNIQUE,
                            password_hash VARCHAR(256),
                            is_admin BOOLEAN DEFAULT 0,
                            is_blocked BOOLEAN DEFAULT 0,
                            is_active BOOLEAN DEFAULT 0,
                            activation_token VARCHAR(100) UNIQUE,
                            created_at DATETIME,
                            profile_image VARCHAR(100),
                            pix_key VARCHAR(100)
                        )
                    """))
                    db.session.execute(text("""
                        INSERT OR IGNORE INTO user_new 
                        SELECT id, username, email, password_hash, is_admin, is_blocked, 
                               0 as is_active, NULL as activation_token, created_at, 
                               profile_image, pix_key 
                        FROM user
                    """))
                    db.session.execute(text("DROP TABLE IF EXISTS user"))
                    db.session.execute(text("ALTER TABLE user_new RENAME TO user"))
                else:
                    # PostgreSQL suporta ALTER COLUMN
                    db.session.execute(text("""
                        ALTER TABLE "user" 
                        ALTER COLUMN password_hash TYPE character varying(256);
                        ALTER TABLE "user"
                        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;
                        ALTER TABLE "user"
                        ADD COLUMN IF NOT EXISTS activation_token VARCHAR(100) UNIQUE;
                    """))
                db.session.commit()
                print("Campos alterados com sucesso!")
            except Exception as e:
                print(f"Aviso: Não foi possível alterar os campos: {str(e)}")
                db.session.rollback()
            
            # Listar tabelas criadas
            tables = db.session.execute(text(
                'SELECT name FROM sqlite_master WHERE type="table"'
                if 'sqlite' in str(db.engine.url)
                else 'SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\''
            )).fetchall()
            print("\nTabelas no banco de dados:")
            for table in tables:
                print(f"- {table[0]}")
            
            # Criar configuração inicial do sistema se não existir
            if not SystemConfig.query.first():
                print("\nCriando configuração inicial do sistema...")
                config = SystemConfig()
                db.session.add(config)
                db.session.commit()
                print("Configuração inicial criada!")
            else:
                print("\nConfiguração do sistema já existe!")
                
        print("\nBanco de dados inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {str(e)}")
        return False

if __name__ == '__main__':
    success = init_db()
    if not success:
        exit(1)
