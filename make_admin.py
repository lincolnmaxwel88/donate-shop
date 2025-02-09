from app import db, User, app

def make_admin(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"Usuário {username} agora é admin!")
    else:
        print(f"Usuário {username} não encontrado.")

if __name__ == '__main__':
    with app.app_context():
        make_admin('lincoln')
