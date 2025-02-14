from app import app, db, User

def make_user_admin(email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"Usuário {email} agora é admin!")
        else:
            print(f"Usuário {email} não encontrado.")

if __name__ == "__main__":
    make_user_admin("lincolnmaxwel@gmail.com")
