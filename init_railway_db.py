from app import app, db
from flask_migrate import upgrade

def init_db():
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()
        
        # Executa as migrações
        upgrade()

if __name__ == '__main__':
    print("Iniciando criação do banco de dados...")
    init_db()
    print("Banco de dados inicializado com sucesso!")
