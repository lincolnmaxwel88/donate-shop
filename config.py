import os

class Config:
    # Configurações do Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'  # Para Gmail
    MAIL_PORT = 587  # Porta TLS
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'lincolnmaxwel@gmail.com'  # Seu email Gmail
    MAIL_PASSWORD = 'guib ycae qsmz kdpa'  # Sua senha de app do Gmail
    MAIL_DEFAULT_SENDER = ('Donate Shop', 'lincolnmaxwel@gmail.com')  # Email que aparecerá como remetente
    CONTACT_EMAIL = 'lincolnmaxwel@gmail.com'  # Email que receberá as mensagens de contato
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///donate_shop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Chave secreta para sessões
    SECRET_KEY = 'your-secret-key-here'
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
