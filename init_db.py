import os
from app import app, db, User, SystemConfig

print("Iniciando configuração do banco de dados...")
print(f"DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

try:
    with app.app_context():
        print("Criando todas as tabelas...")
        db.create_all()
        print("Tabelas criadas com sucesso!")

        # Listar todas as tabelas criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        print("\nTabelas existentes no banco:")
        for table_name in inspector.get_table_names():
            print(f"- {table_name}")

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

except Exception as e:
    print(f"\nERRO ao inicializar banco de dados: {str(e)}")
    raise
