import os
import sys

# Adicione o diretório do seu aplicativo ao path do Python
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SITE_ROOT)

# Configuração do ambiente virtual (ajuste o caminho conforme necessário)
VENV_PATH = os.path.join(SITE_ROOT, 'venv')
PYTHON_PATH = os.path.join(VENV_PATH, 'bin', 'python')

if sys.executable != PYTHON_PATH:
    os.execl(PYTHON_PATH, PYTHON_PATH, *sys.argv)

from app import app as application
