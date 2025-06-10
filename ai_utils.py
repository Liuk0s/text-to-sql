import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import MODEL_SIZE, DB_TYPE

logger = logging.getLogger(__name__)

def load_model():
    """
    Carrega o modelo NSQL baseado na configuração
    
    Returns:
        tuple: (tokenizer, model)
    """
    # Valida o tamanho do modelo
    if MODEL_SIZE not in ['350M', '2B', '6B']:
        error_msg = f"Tamanho de modelo inválido: {MODEL_SIZE}. Use '350M', '2B' ou '6B'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    model_name = f"NumbersStation/nsql-{MODEL_SIZE}"
    logger.info(f"Carregando modelo NSQL-{MODEL_SIZE}...")
    logger.info(f"Modelo HuggingFace: {model_name}")
    
    try:
        # Carrega tokenizer e modelo do HuggingFace
        logger.debug("Carregando tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        logger.debug("Carregando modelo neural...")
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Define token de padding se não estiver definido
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.debug("Token de padding configurado")
            
        logger.info(f"Modelo NSQL-{MODEL_SIZE} carregado com sucesso!")
        logger.info(f"Vocabulário: {len(tokenizer.vocab)} tokens")
        logger.info(f"Parâmetros do modelo: ~{MODEL_SIZE} parâmetros")
        
        return tokenizer, model
        
    except Exception as e:
        logger.error(f"Erro ao carregar o modelo: {e}")
        raise RuntimeError(f"Falha crítica ao carregar modelo NSQL: {e}") from e

def format_schema_for_model(schema):
    """
    Formata o esquema do banco de dados de uma forma que o modelo NSQL possa entender.
    
    Args:
        schema (dict): Dicionário do esquema do banco
        
    Returns:
        str: String do esquema formatada para o modelo
    """
    logger.debug(f"Formatando schema para o modelo - {len(schema)} tabelas")
    
    formatted_schema = "\n".join(
        f"CREATE TABLE {table_name} ({', '.join(columns)});"
        for table_name, columns in schema.items()
    )
    
    logger.debug(f"Schema formatado com {len(formatted_schema)} caracteres")
    return formatted_schema

def generate_model_response(tokenizer, model, prompt_text, max_new_tokens=128):
    """
    Gera uma resposta do modelo NSQL dado um prompt.
    
    Args:
        tokenizer: Tokenizer do modelo
        model: Modelo NSQL carregado
        prompt_text (str): Prompt de entrada para o modelo
        max_new_tokens (int): Número máximo de novos tokens para gerar
        
    Returns:
        str: Resposta gerada pelo modelo
    """
    logger.debug(f"Gerando resposta do modelo - prompt: {len(prompt_text)} caracteres")
    
    # Tokeniza o prompt de entrada
    model_inputs = tokenizer(
        prompt_text, 
        return_tensors="pt", 
        max_length=512, 
        truncation=True
    )
    
    input_length = model_inputs['input_ids'].shape[1]
    logger.debug(f"Tokens de entrada: {input_length}")
    
    # Gera resposta sem computar gradientes (inferência mais rápida)
    with torch.no_grad():
        model_outputs = model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,  # Temperatura baixa para saída mais determinística
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    output_length = model_outputs[0].shape[0]
    new_tokens = output_length - input_length
    logger.debug(f"Tokens gerados: {new_tokens}")
    
    # Decodifica apenas os tokens recém-gerados (exclui entrada)
    generated_text = tokenizer.decode(
        model_outputs[0][model_inputs['input_ids'].shape[1]:], 
        skip_special_tokens=True
    )
    
    logger.debug(f"Texto gerado: {len(generated_text)} caracteres")
    return generated_text

def generate_sql_from_question(tokenizer, model, natural_language_question, database_schema):
    """
    Converte uma pergunta em linguagem natural em uma consulta SQL usando o modelo NSQL.
    Adapta o prompt para usar o dialeto SQL correto baseado no tipo de banco configurado.
    
    Args:
        tokenizer: Tokenizer do modelo
        model: Modelo NSQL carregado
        natural_language_question (str): Pergunta do usuário em linguagem natural
        database_schema (dict): Informações do esquema do banco de dados
        
    Returns:
        str: Consulta SQL gerada
    """
    logger.info(f"Convertendo pergunta para SQL: '{natural_language_question}'")
    
    # Determina o dialeto SQL baseado no tipo de banco configurado
    dialect = "MySQL" if DB_TYPE == "mysql" else "PostgreSQL"
    logger.debug(f"Usando dialeto SQL: {dialect}")
    
    # Cria um prompt seguindo o formato NSQL com dialeto específico
    model_prompt = f"""-- Using valid {dialect}, answer the following questions for the tables provided above.

-- Schema:
{format_schema_for_model(database_schema)}

-- Question: {natural_language_question}

-- SQL Query:
"""
    
    logger.debug(f"Prompt construído - {len(model_prompt)} caracteres")
    
    # Gera SQL usando o modelo
    generated_response = generate_model_response(tokenizer, model, model_prompt)
    
    # Extrai apenas a parte SQL (antes do primeiro ponto e vírgula)
    sql_query = generated_response.split(";")[0].strip()
    
    logger.info(f"SQL gerada: {sql_query}")
    return sql_query