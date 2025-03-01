from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app import app, db
from sqlalchemy import text

def run_migrations():
    print("Iniciando migrações...")
    try:
        with app.app_context():
            # Ler o arquivo SQL
            sql_file_path = os.path.join(os.path.dirname(__file__), 'add_activation_columns.sql')
            with open(sql_file_path, 'r') as file:
                sql = file.read()
            
            # Executar os comandos SQL
            print("Executando SQL para adicionar colunas...")
            with db.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            print("Migrações concluídas com sucesso!")
            return True
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        return False

if __name__ == '__main__':
    run_migrations()
