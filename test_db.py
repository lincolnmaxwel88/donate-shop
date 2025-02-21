from app import app, db, User
from datetime import datetime

def test_database():
    with app.app_context():
        try:
            # Tenta criar um usuário de teste
            test_user = User(
                username='test_user',
                email='test@test.com',
                password_hash='test123'
            )
            
            # Adiciona ao banco
            db.session.add(test_user)
            db.session.commit()
            
            # Busca o usuário criado
            found_user = User.query.filter_by(username='test_user').first()
            print(f"Usuário encontrado: {found_user.username}")
            
            # Remove o usuário de teste
            db.session.delete(found_user)
            db.session.commit()
            
            print("Teste concluído com sucesso! O banco de dados está funcionando corretamente.")
            print("Novos cadastros serão salvos no PostgreSQL.")
            
        except Exception as e:
            print(f"Erro ao testar o banco de dados: {str(e)}")
            print("Verifique se a variável DATABASE_URL está configurada corretamente no Railway.")
            db.session.rollback()

if __name__ == '__main__':
    test_database()
