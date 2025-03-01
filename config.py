import os
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.getenv('SECRET_KEY', 'b215813213bb78fcfe04e62a84b98dc97be63365a0536dd37b979ceccea195da')
    CONTACT_EMAIL = 'contato@doarsonhos.com.br'  # Email que receberá as mensagens de contato
    
    # Configurações do banco de dados
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///donate_shop.db')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Chave secreta para sessões
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Configurações de email
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'no-reply@doarsonhos.com.br'
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'Linday#1818')  # Definir no Railway
    MAIL_DEFAULT_SENDER = 'no-reply@doarsonhos.com.br'  
    MAIL_DEBUG = True  # Habilita logs detalhados
    MAIL_ASCII_ATTACHMENTS = True  # Força codificação ASCII
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
