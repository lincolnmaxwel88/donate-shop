import os
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CONTACT_EMAIL = 'contato@doarsonhos.com.br'  # Email que receberá as mensagens de contato
    
    # Configurações do banco de dados
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///donate_shop.db')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Chave secreta para sessões
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    
    # Configurações do Flask-Mail
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'contato@doarsonhos.com.br'
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'Linday#1818')  # Coloque a senha no Railway
    MAIL_DEFAULT_SENDER = ('Doar Sonhos', 'contato@doarsonhos.com.br')  # Email que aparecerá como remetente
