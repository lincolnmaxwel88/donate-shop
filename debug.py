from app import app
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Tentar inicializar o app
        with app.app_context():
            from app import db
            # Verificar conexão com o banco
            db.engine.connect()
            logger.info("Conexão com o banco estabelecida com sucesso!")
            
            # Listar todas as tabelas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Tabelas encontradas: {tables}")
            
    except Exception as e:
        logger.error(f"Erro ao inicializar aplicação: {str(e)}", exc_info=True)

    # Rodar o app em modo debug
    app.run(debug=True, port=5000)
