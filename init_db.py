from flask_migrate import upgrade
from app import app, db
import os
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app import User, SystemConfig

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
        # Executar migrações pendentes
        print("Executando migrações...")
        with app.app_context():
            upgrade()
        
        # Criar tabelas (caso alguma não tenha sido criada pelas migrações)
        print("Criando tabelas...")
        with app.app_context():
            db.create_all()
            
        # Listar tabelas criadas
        with app.app_context():
            # Usar raw SQL para listar tabelas
            tables = db.session.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')).fetchall()
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
