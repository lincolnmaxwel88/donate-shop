from app import app, db, User, SystemConfig

print("Criando tabelas...")
with app.app_context():
    db.create_all()

    # Criar configuração inicial do sistema se não existir
    if not SystemConfig.query.first():
        print("Criando configuração inicial do sistema...")
        config = SystemConfig()
        db.session.add(config)
        db.session.commit()

    print("Banco de dados inicializado com sucesso!")
