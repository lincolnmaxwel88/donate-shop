from app import app, db, User, SystemConfig
import os

print("=== Iniciando criação das tabelas ===")
print("Variáveis de ambiente:")
for var in ['SQLALCHEMY_DATABASE_URI', 'MYSQL_URL', 'DATABASE_URL']:
    print(f"{var}: {os.getenv(var, 'não definida')}")

print("\nConfiguração do Flask:")
print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"SQLALCHEMY_TRACK_MODIFICATIONS: {app.config['SQLALCHEMY_TRACK_MODIFICATIONS']}")

try:
    with app.app_context():
        print("\nTentando criar as tabelas...")
        db.create_all()
        print("Tabelas criadas com sucesso!")

        # Criar configuração inicial do sistema se não existir
        if not SystemConfig.query.first():
            print("Criando configuração inicial do sistema...")
            config = SystemConfig()
            db.session.add(config)
            db.session.commit()
            print("Configuração inicial criada!")

        print("\nBanco de dados inicializado com sucesso!")
        
        # Listar todas as tabelas criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        print("\nTabelas criadas no banco:")
        for table_name in inspector.get_table_names():
            print(f"- {table_name}")
            
except Exception as e:
    print(f"\nERRO ao criar tabelas: {str(e)}")
    print(f"Tipo do erro: {type(e).__name__}")
    raise
