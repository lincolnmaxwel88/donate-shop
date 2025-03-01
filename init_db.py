from app import app, db, User, SystemConfig
import os

print("Iniciando criação das tabelas...")
print(f"URL do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")

try:
    with app.app_context():
        print("Criando todas as tabelas...")
        db.create_all()
        print("Tabelas criadas com sucesso!")

        # Criar configuração inicial do sistema se não existir
        if not SystemConfig.query.first():
            print("Criando configuração inicial do sistema...")
            config = SystemConfig()
            db.session.add(config)
            db.session.commit()
            print("Configuração inicial criada!")

        print("Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao criar tabelas: {str(e)}")
    raise
