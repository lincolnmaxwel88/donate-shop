import os
from app import app, db
from flask_migrate import upgrade
from sqlalchemy import text

# URL do banco de dados
DATABASE_URL = "postgresql://postgres:JVnCsSTibEVcGjoDegqaeBInwMEhssyp@nozomi.proxy.rlwy.net:49195/railway"

def init_db():
    try:
        print("Configurando conexão com o banco de dados...")
        print(f"URL do banco: {DATABASE_URL}")
        
        # Configura a URL do banco de dados
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
        
        with app.app_context():
            print("Testando conexão com o banco...")
            # Testa a conexão
            with db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                conn.commit()
            print("Conexão bem sucedida!")
            
            print("Removendo tabelas existentes se houver...")
            db.drop_all()
            
            print("Criando tabelas...")
            db.create_all()
            
            print("Listando tabelas criadas:")
            # Lista as tabelas criadas
            inspector = db.inspect(db.engine)
            for table_name in inspector.get_table_names():
                print(f"- {table_name}")
            
            print("\nExecutando migrações...")
            upgrade()
            
            print("Banco de dados inicializado com sucesso!")
            
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {str(e)}")
        raise

if __name__ == '__main__':
    init_db()
