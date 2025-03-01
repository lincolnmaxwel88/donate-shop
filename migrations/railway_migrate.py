from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from app import app, db

def run_migrations():
    print("Iniciando migrações...")
    try:
        # Configurar migração
        migrate = Migrate(app, db)
        
        # Executar migração
        os.system('flask db upgrade')
        
        print("Migrações concluídas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        return False

if __name__ == '__main__':
    with app.app_context():
        run_migrations()
