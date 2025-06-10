import logging
from config import DATABASE_CONFIG, DB_TYPE

logger = logging.getLogger(__name__)

def create_database_connection():
    """
    Cria conexão com o banco baseado no tipo configurado.
    Suporta MySQL e PostgreSQL de forma flexível.
    
    Returns:
        connection: Objeto de conexão do banco
    """
    logger.info(f"Conectando ao banco de dados: {DB_TYPE.upper()}")
    logger.debug(f"Host: {DATABASE_CONFIG.get('host')}:{DATABASE_CONFIG.get('port')}")
    logger.debug(f"Banco: {DATABASE_CONFIG.get('database')}")
    logger.debug(f"Usuário: {DATABASE_CONFIG.get('user')}")
    
    if DB_TYPE == 'mysql':
        import mysql.connector
        return mysql.connector.connect(**DATABASE_CONFIG)
    elif DB_TYPE == 'postgresql':
        import psycopg2
        # PostgreSQL usa 'dbname' ao invés de 'database'
        pg_config = DATABASE_CONFIG.copy()
        pg_config['dbname'] = pg_config.pop('database')
        return psycopg2.connect(**pg_config)
    else:
        raise ValueError(f"Tipo de banco não suportado: {DB_TYPE}")

def get_database_cursor(connection, dictionary_mode=False):
    """
    Cria um cursor apropriado baseado no tipo de banco.
    
    Args:
        connection: Objeto de conexão do banco
        dictionary_mode (bool): Se deve retornar resultados como dicionário
        
    Returns:
        cursor: Cursor do banco de dados
    """
    logger.debug(f"Criando cursor - modo dicionário: {dictionary_mode}")
    
    if DB_TYPE == 'mysql':
        return connection.cursor(dictionary=dictionary_mode)
    elif DB_TYPE == 'postgresql':
        import psycopg2.extras
        if dictionary_mode:
            return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return connection.cursor()
    else:
        return connection.cursor()

def get_database_schema():
    """
    Obtém o esquema do banco de dados incluindo todas as tabelas e suas colunas.
    Funciona tanto para MySQL quanto PostgreSQL.
    
    Returns:
        dict: Dicionário com nomes das tabelas como chaves e listas de colunas como valores
    """
    logger.debug("Iniciando descoberta do schema do banco")
    
    try:
        # Estabelece conexão com o banco de dados
        connection = create_database_connection()
        cursor = get_database_cursor(connection)
        
        # Obtém todos os nomes das tabelas (sintaxe diferente para cada banco)
        if DB_TYPE == 'mysql':
            logger.debug("Executando: SHOW TABLES")
            cursor.execute("SHOW TABLES")
        elif DB_TYPE == 'postgresql':
            logger.debug("Executando query para listar tabelas do PostgreSQL")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
        
        tables = cursor.fetchall()
        logger.info(f"Encontradas {len(tables)} tabelas no banco")
        
        schema = {}
        
        # Para cada tabela, obtém informações das colunas
        for table_row in tables:
            # Extrai nome da tabela (formato pode variar entre bancos)
            table_name = table_row[0] if isinstance(table_row, tuple) else table_row
            logger.debug(f"Processando tabela: {table_name}")
            
            if DB_TYPE == 'mysql':
                cursor.execute(f"DESCRIBE {table_name}")
            elif DB_TYPE == 'postgresql':
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """)
            
            columns = cursor.fetchall()
            # Armazena apenas os nomes das colunas (primeiro elemento de cada tupla)
            column_names = [column[0] for column in columns]
            schema[table_name] = column_names
            
            logger.debug(f"Tabela {table_name}: {len(column_names)} colunas")

        # Limpa a conexão com o banco
        cursor.close()
        connection.close()
        logger.debug("Conexão com banco fechada")
        
        # Log do schema completo
        total_columns = sum(len(cols) for cols in schema.values())
        logger.info(f"Schema obtido: {len(schema)} tabelas, {total_columns} colunas total")
        
        return schema
        
    except Exception as error:
        logger.error(f"Erro ao obter esquema do banco: {error}")
        raise RuntimeError(f"Erro ao obter esquema do banco: {error}") from error

def execute_sql_query(sql_query):
    """
    Executa uma consulta SQL contra o banco de dados.
    Compatível com MySQL e PostgreSQL.
    
    Args:
        sql_query (str): Consulta SQL para executar
        
    Returns:
        dict: Dicionário de resultado com status de sucesso, dados e metadados
    """
    logger.info(f"Executando consulta SQL: {sql_query}")
    
    try:
        # Estabelece conexão com cursor de dicionário para facilitar o manuseio
        connection = create_database_connection()
        cursor = get_database_cursor(connection, dictionary_mode=True)
        
        # Executa a consulta SQL
        logger.debug("Executando query no banco de dados...")
        cursor.execute(sql_query)
        query_results = cursor.fetchall()
        
        # Obtém nomes das colunas (método varia entre bancos)
        if DB_TYPE == 'mysql':
            column_names = cursor.column_names if cursor.description else []
        elif DB_TYPE == 'postgresql':
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
        else:
            column_names = []

        logger.info(f"Consulta executada com sucesso - {len(query_results)} linhas retornadas")
        logger.debug(f"Colunas retornadas: {column_names}")

        # Limpa a conexão com o banco
        cursor.close()
        connection.close()
        logger.debug("Conexão com banco fechada")

        return {
            'success': True, 
            'columns': column_names, 
            'data': query_results, 
            'query': sql_query
        }
        
    except Exception as error:
        logger.warning(f"Erro na execução da consulta: {error}")
        return {
            'success': False, 
            'error': str(error), 
            'query': sql_query
        }