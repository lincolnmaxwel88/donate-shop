import os
import shutil
from datetime import datetime

def backup_database():
    """
    Faz uma cópia do banco de dados SQLite
    """
    # Nome do arquivo do banco de dados
    db_file = 'donate_shop.db'
    
    # Verifica se o banco existe
    if not os.path.exists(db_file):
        print("Banco de dados não encontrado!")
        return
    
    # Cria pasta de backup se não existir
    backup_dir = 'db_backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'donate_shop_{timestamp}.db')
    
    # Faz a cópia do banco
    shutil.copy2(db_file, backup_file)
    print(f"Backup criado com sucesso: {backup_file}")

if __name__ == '__main__':
    backup_database()
