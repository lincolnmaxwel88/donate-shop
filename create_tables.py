import psycopg2
from urllib.parse import urlparse

# URL do banco de dados
DATABASE_URL = "postgresql://postgres:JVnCsSTibEVcGjoDegqaeBInwMEhssyp@nozomi.proxy.rlwy.net:49195/railway"

# Parse da URL para obter os componentes
url = urlparse(DATABASE_URL)
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

# SQL para criar as tabelas
CREATE_TABLES = """
-- Tabela user
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    profile_image VARCHAR(200),
    pix_key VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela campaign
CREATE TABLE IF NOT EXISTS campaign (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    goal FLOAT,
    image VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    allow_comments BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    user_id INTEGER REFERENCES "user"(id) NOT NULL
);

-- Tabela donation
CREATE TABLE IF NOT EXISTS donation (
    id SERIAL PRIMARY KEY,
    amount FLOAT NOT NULL,
    net_amount FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES "user"(id) NOT NULL,
    campaign_id INTEGER REFERENCES campaign(id) NOT NULL
);

-- Tabela comment
CREATE TABLE IF NOT EXISTS comment (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES "user"(id) NOT NULL,
    campaign_id INTEGER REFERENCES campaign(id) NOT NULL
);

-- Tabela like
CREATE TABLE IF NOT EXISTS "like" (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES "user"(id) NOT NULL,
    campaign_id INTEGER REFERENCES campaign(id) NOT NULL,
    UNIQUE(user_id, campaign_id)
);

-- Tabela campaign_view
CREATE TABLE IF NOT EXISTS campaign_view (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaign(id) NOT NULL,
    user_id INTEGER REFERENCES "user"(id),
    ip_address VARCHAR(45),
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela withdrawal_request
CREATE TABLE IF NOT EXISTS withdrawal_request (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaign(id) NOT NULL,
    user_id INTEGER REFERENCES "user"(id) NOT NULL,
    amount FLOAT NOT NULL,
    fee_percentage FLOAT NOT NULL,
    net_amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by_id INTEGER REFERENCES "user"(id),
    notes TEXT,
    next_attempt_allowed_at TIMESTAMP,
    pix_key VARCHAR(100)
);

-- Tabela system_config
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    withdrawal_fee FLOAT DEFAULT 5.0,
    min_withdrawal_percentage FLOAT DEFAULT 10.0,
    next_withdrawal_minutes INTEGER DEFAULT 1440,
    gateway_fee_percentage FLOAT DEFAULT 3.99,
    gateway_fee_fixed FLOAT DEFAULT 0.39,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER REFERENCES "user"(id)
);
"""

# SQL para adicionar a coluna pix_key se ela não existir
ADD_PIX_KEY = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='user' 
        AND column_name='pix_key'
    ) THEN
        ALTER TABLE "user" ADD COLUMN pix_key VARCHAR(100);
    END IF;
END $$;
"""

# SQL para adicionar as colunas de confirmação de email
ADD_EMAIL_CONFIRMATION_COLUMNS = """
DO $$
BEGIN
    -- Adicionar coluna email_confirmed
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='user' 
        AND column_name='email_confirmed'
    ) THEN
        ALTER TABLE "user" ADD COLUMN email_confirmed BOOLEAN DEFAULT FALSE;
    END IF;

    -- Adicionar coluna confirmation_token
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='user' 
        AND column_name='confirmation_token'
    ) THEN
        ALTER TABLE "user" ADD COLUMN confirmation_token VARCHAR(100) UNIQUE;
    END IF;

    -- Adicionar coluna confirmation_token_created_at
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='user' 
        AND column_name='confirmation_token_created_at'
    ) THEN
        ALTER TABLE "user" ADD COLUMN confirmation_token_created_at TIMESTAMP;
    END IF;
END $$;
"""

def create_tables():
    try:
        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        
        print("Conexão estabelecida com sucesso!")
        
        # Criar um cursor
        cur = conn.cursor()
        
        print("Criando tabelas...")
        # Executar os comandos SQL
        cur.execute(CREATE_TABLES)
        
        print("Adicionando coluna pix_key se necessário...")
        cur.execute(ADD_PIX_KEY)
        
        print("Adicionando colunas de confirmação de email...")
        cur.execute(ADD_EMAIL_CONFIRMATION_COLUMNS)
        
        # Commit das alterações
        conn.commit()
        print("Tabelas criadas/atualizadas com sucesso!")
        
        # Listar as tabelas criadas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print("\nTabelas existentes no banco:")
        for table in cur.fetchall():
            print(f"- {table[0]}")
            
            # Se for a tabela user, vamos listar suas colunas
            if table[0] == 'user':
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user'
                """)
                print("  Colunas:")
                for column in cur.fetchall():
                    print(f"  - {column[0]}")
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        raise
    finally:
        # Fechar cursor e conexão
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    create_tables()
