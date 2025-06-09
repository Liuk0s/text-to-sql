import os
import warnings
import logging
from flask import Flask, render_template, request, jsonify, url_for

# Importa nossas funções organizadas
from config import FLASK_DEBUG, FLASK_PORT
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
except Exception as e:
    logger.critical("Erro fatal ao iniciar o modelo. A API não estará disponível.")
    raise RuntimeError("Aplicação não pode iniciar sem modelo NSQL") from e

# ===========================
# ROTAS DO FLASK
# ===========================
@app.route('/')
def index():
    """
    Rota da página principal que renderiza a interface HTML.
    
    Returns:
        str: Template HTML renderizado com o esquema do banco
    """
    return render_template('index.html', schema=get_database_schema())

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
    
    # Valida entrada
    if not user_question:
        return jsonify({'error': 'Nenhuma pergunta fornecida'}), 400

    # Obtém esquema atual do banco
    current_schema = get_database_schema()
    
    try:
        # Gera consulta SQL a partir da linguagem natural
        generated_sql = generate_sql_from_question(
            tokenizer, model, user_question, current_schema
        )
    except Exception as error:
        return jsonify({
            'success': False, 
            'error': f'Erro ao gerar SQL: {str(error)}'
        }), 500

    # Executa a consulta SQL gerada e retorna resultados
    return jsonify(execute_sql_query(generated_sql))

@app.route('/schema', methods=['GET'])
def get_current_schema():
    """
    Endpoint da API para obter o esquema atual do banco de dados.
    
    Returns:
        JSON: Informações do esquema do banco de dados
    """
    return jsonify(get_database_schema())

# ===========================
# PONTO DE ENTRADA DA APLICAÇÃO
# ===========================
if __name__ == '__main__':
    # Log das configurações de inicialização
    logger.info(f"Debug habilitado: {FLASK_DEBUG}")
    
    # Inicia o servidor de desenvolvimento Flask
    app.run(
        debug=FLASK_DEBUG, 
        host='0.0.0.0', 
        port=FLASK_PORT
    )