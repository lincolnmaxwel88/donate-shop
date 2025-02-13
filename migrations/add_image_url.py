from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

def upgrade():
    # Renomear a coluna 'image' para 'image_url'
    with app.app_context():
        db.session.execute('ALTER TABLE campaign RENAME COLUMN image TO image_url')
        db.session.commit()

def downgrade():
    # Reverter a renomeação
    with app.app_context():
        db.session.execute('ALTER TABLE campaign RENAME COLUMN image_url TO image')
        db.session.commit()

if __name__ == '__main__':
    upgrade()
