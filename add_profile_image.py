from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE user ADD COLUMN profile_image VARCHAR(100)'))
        db.session.commit()
        print("Coluna profile_image adicionada com sucesso!")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {str(e)}")
        db.session.rollback()
