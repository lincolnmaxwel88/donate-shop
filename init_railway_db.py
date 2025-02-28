from app import app, db, User, SystemConfig
from sqlalchemy.exc import SQLAlchemyError
import sys

def init_db():
    try:
        with app.app_context():
            print("Verificando conexão com o banco de dados...")
            db.engine.connect()
            print("Conexão estabelecida com sucesso!")

            print("Criando todas as tabelas...")
            db.create_all()
            print("Tabelas criadas com sucesso!")

            # Criar configuração inicial do sistema se não existir
            if not SystemConfig.query.first():
                print("Criando configuração inicial do sistema...")
                config = SystemConfig()
                db.session.add(config)
                db.session.commit()
                print("Configuração inicial criada com sucesso!")
            else:
                print("Configuração do sistema já existe!")

            print("\nBanco de dados inicializado com sucesso!")
            return True

    except SQLAlchemyError as e:
        print("\nErro ao inicializar o banco de dados:")
        print(f"Erro: {str(e)}")
        print("\nVerifique se:")
        print("1. A variável DATABASE_URL está configurada corretamente no Railway")
        print("2. O banco PostgreSQL está ativo no Railway")
        print("3. As credenciais de acesso estão corretas")
        return False

if __name__ == '__main__':
    print("\n=== Iniciando setup do banco de dados ===\n")
    success = init_db()
    if not success:
        sys.exit(1)  # Sai com código de erro
    print("\n=== Setup concluído com sucesso! ===\n")
