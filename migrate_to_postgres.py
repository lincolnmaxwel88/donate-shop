from app import app, db
from flask_migrate import upgrade

def migrate_database():
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()
        
        # Executa as migrações pendentes
        upgrade()

if __name__ == '__main__':
    migrate_database()
