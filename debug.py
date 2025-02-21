import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Criar app
app = Flask(__name__)

# Configurar banco de dados
DATABASE_URL = "postgresql://postgres:JVnCsSTibEVcGjoDegqaeBInwMEhssyp@nozomi.proxy.rlwy.net:49195/railway"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

def test_connection():
    try:
        # Tentar conectar ao banco
        with app.app_context():
            db.engine.connect()
            logger.info("Conexão com o banco estabelecida com sucesso!")
            
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}", exc_info=True)

if __name__ == '__main__':
    test_connection()
