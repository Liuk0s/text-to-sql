import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', '3306').split('#')[0].strip())
}

# Configurações do modelo
MODEL_SIZE = os.getenv('MODEL_SIZE', '350M').upper()

# Configurações do Flask
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000').split('#')[0].strip())

# Tipo do banco
DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()