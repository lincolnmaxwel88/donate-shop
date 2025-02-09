import os

class Config:
    # Configurações do Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'  # Para Gmail
    MAIL_PORT = 587  # Porta TLS
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'lincolnmaxwel@gmail.com'  # Substitua pelo seu email
    MAIL_PASSWORD = 'guib ycae qsmz kdpa'  # Substitua pela sua senha de app
    MAIL_DEFAULT_SENDER = ('Donate Shop', 'lincolnmaxwel@gmail.com')  # Email que aparecerá como remetente
    CONTACT_EMAIL = 'lincolnmaxwel@gmail.com'  # Email que receberá as mensagens de contato
