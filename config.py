import os
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CONTACT_EMAIL = 'lincolnmaxwel@gmail.com'  # Email que receberá as mensagens de contato
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///donate_shop.db')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Chave secreta para sessões
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    
    # Configurações do Flask-Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'lincolnmaxwel@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'guib ycae qsmz kdpa')
    MAIL_DEFAULT_SENDER = ('Donate Shop', 'lincolnmaxwel@gmail.com')  # Email que aparecerá como remetente
