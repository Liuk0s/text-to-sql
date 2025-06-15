import os
import warnings
import logging
from flask import Flask, render_template, request, jsonify, url_for

from config import FLASK_DEBUG, FLASK_PORT, DB_TYPE, DATABASE_CONFIG, MODEL_SIZE
from database_utils import get_database_schema, execute_sql_query
from ai_utils import load_model, generate_sql_from_question

# Suprime mensagens de warning para uma saída mais limpa
warnings.filterwarnings('ignore')

# Inicializa a aplicação Flask com configuração para arquivos estáticos
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configura o Flask baseado nas variáveis de ambiente
app.config['DEBUG'] = FLASK_DEBUG

# Configura o sistema de logging baseado no modo debug
log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
logging.basicConfig(
    level=log_level,
    format='[%(asctime)s] %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ===========================
# INICIALIZAÇÃO DO MODELO
# ===========================
tokenizer = model = None

try:
    tokenizer, model = load_model()
    logger.info(f"Modelo NSQL-{MODEL_SIZE} carregado com sucesso!")
except Exception as e:
    logger.critical("Erro fatal ao iniciar o modelo. A API não estará disponível.")
    raise RuntimeError("Aplicação não pode iniciar sem modelo NSQL") from e

# ===========================
# INFORMAÇÕES DO SISTEMA
# ===========================
def get_system_info():
    """
    Retorna informações do sistema para exibir na interface
    """
    return {
        'db_type': DB_TYPE,
        'db_name': DATABASE_CONFIG.get('database', 'N/A'),
        'model_size': MODEL_SIZE,
        'db_host': DATABASE_CONFIG.get('host', 'localhost'),
        'db_port': DATABASE_CONFIG.get('port', 'N/A')
    }

# ===========================
# ROTAS DO FLASK
# ===========================
@app.route('/')
def index():
    """
    Rota da página principal que renderiza a interface HTML.
    
    Returns:
        str: Template HTML renderizado com o esquema do banco e informações do sistema
    """
    try:
        schema = get_database_schema()
        system_info = get_system_info()
        
        logger.info(f"Página inicial carregada - Banco: {system_info['db_type'].upper()}, "
                   f"DB: {system_info['db_name']}, Modelo: NSQL-{system_info['model_size']}")
        
        return render_template('index.html', 
                             schema=schema, 
                             system_info=system_info)
    except Exception as e:
        logger.error(f"Erro ao carregar página inicial: {e}")
        # Em caso de erro, retorna template com informações mínimas
        return render_template('index.html', 
                             schema={}, 
                             system_info=get_system_info())

@app.route('/query', methods=['POST'])
def process_natural_language_query():
    """
    Endpoint da API para processar consultas em linguagem natural e retornar resultados SQL.
    
    Returns:
        JSON: Resultados da consulta ou informações de erro
    """
    # Analisa dados JSON da requisição
    request_data = request.json
    user_question = request_data.get('question', '')
    
    # Log da consulta recebida
    logger.info(f"Nova consulta recebida: '{user_question}'")
    
    # Valida entrada
    if not user_question:
        logger.warning("Consulta vazia recebida")
        return jsonify({'error': 'Nenhuma pergunta fornecida'}), 400

    # Obtém esquema atual do banco
    try:
        current_schema = get_database_schema()
        logger.debug(f"Schema obtido: {len(current_schema)} tabelas")
    except Exception as e:
        logger.error(f"Erro ao obter schema: {e}")
        return jsonify({
            'success': False, 
            'error': f'Erro ao acessar banco de dados: {str(e)}'
        }), 500
    
    try:
        # Gera consulta SQL a partir da linguagem natural
        logger.info(f"Gerando SQL com modelo NSQL-{MODEL_SIZE}...")
        generated_sql = generate_sql_from_question(
            tokenizer, model, user_question, current_schema
        )
        logger.info(f"SQL gerada: {generated_sql}")
        
    except Exception as error:
        logger.error(f"Erro na geração de SQL: {error}")
        return jsonify({
            'success': False, 
            'error': f'Erro ao gerar SQL: {str(error)}'
        }), 500

    # Executa a consulta SQL gerada e retorna resultados
    result = execute_sql_query(generated_sql)
    
    if result.get('success'):
        row_count = len(result.get('data', []))
        logger.info(f"Consulta executada com sucesso - {row_count} linhas retornadas")
    else:
        logger.warning(f"Falha na execução da consulta: {result.get('error', 'Erro desconhecido')}")
    
    return jsonify(result)

@app.route('/schema', methods=['GET'])
def get_current_schema():
    """
    Endpoint da API para obter o esquema atual do banco de dados.
    
    Returns:
        JSON: Informações do esquema do banco de dados
    """
    try:
        schema = get_database_schema()
        logger.info(f"Schema solicitado via API - {len(schema)} tabelas")
        return jsonify(schema)
    except Exception as e:
        logger.error(f"Erro ao obter schema via API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/system-info', methods=['GET'])
def get_system_info_endpoint():
    """
    Endpoint da API para obter informações do sistema.
    
    Returns:
        JSON: Informações do sistema (banco, modelo, etc.)
    """
    system_info = get_system_info()
    logger.info("Informações do sistema solicitadas via API")
    return jsonify(system_info)

# ===========================
# PONTO DE ENTRADA DA APLICAÇÃO
# ===========================
if __name__ == '__main__':
    # Log das configurações de inicialização
    system_info = get_system_info()
    
    logger.info("Iniciando Motor Text-to-SQL...")
    logger.info(f"Configurações do Sistema:")
    logger.info(f"   • Banco de Dados: {system_info['db_type'].upper()}")
    logger.info(f"   • Nome do Banco: {system_info['db_name']}")
    logger.info(f"   • Host: {system_info['db_host']}:{system_info['db_port']}")
    logger.info(f"   • Modelo IA: NSQL-{system_info['model_size']}")
    logger.info(f"   • Debug habilitado: {FLASK_DEBUG}")
    logger.info(f"   • Porta: {FLASK_PORT}")
    
    # Inicia o servidor de desenvolvimento Flask
    try:
        app.run(
            debug=FLASK_DEBUG, 
            host='0.0.0.0', 
            port=FLASK_PORT
        )
    except Exception as e:
        logger.critical(f"Falha crítica ao iniciar servidor: {e}")
        raise
