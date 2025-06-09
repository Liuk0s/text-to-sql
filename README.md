# Text-to-SQL Engine

Converte perguntas em linguagem natural para consultas SQL usando modelos NSQL.

## Requisitos

- Python 3.8+
- MySQL ou PostgreSQL
- 2GB RAM (NSQL-350M) ou 8GB RAM (NSQL-2B)
- Internet (para download inicial do modelo)

## Instalação

### 1. Clone e prepare ambiente

```bash
git clone <url-do-repositorio>
cd text-to-sql-engine
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instale dependências

```bash
pip install -r requirements.txt
```

### 3. Configure banco

Crie arquivo `.env` na raiz:

```env
# Banco de dados
DB_TYPE=mysql          # ou 'postgresql'
DB_HOST=localhost
DB_PORT=3306           # 5432 para PostgreSQL
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nome_do_banco

# Modelo NSQL
MODEL_SIZE=350M        # ou '2B'

# Flask
FLASK_DEBUG=False
FLASK_PORT=5000
```

### 4. Inicie aplicação

```bash
python app.py
```

Acesse `http://localhost:5000`

## Uso

Faça perguntas em **inglês** sobre seu banco de dados. O sistema gera automaticamente a consulta SQL e exibe os resultados.

### Exemplos

- "How many students are in each department?"
- "What is the total budget of all departments?"
- "Which building has the highest capacity classroom?"
- "What is the average grade of students in the Economics department?"

## Estrutura do projeto

```
text-to-sql-engine/
├── app.py                 # Aplicação Flask principal
├── config.py              # Configurações
├── ai_utils.py            # Utilitários de IA
├── database_utils.py      # Utilitários de banco
├── requirements.txt       # Dependências
├── .env                   # Configurações (criar)
├── templates/
│   └── index.html         # Interface web
└── static/
    ├── css/style.css      # Estilos
    └── js/app.js          # JavaScript
```

## API

- `GET /` - Interface principal
- `POST /query` - Processar consulta em linguagem natural
- `GET /schema` - Obter schema do banco

## Configurações

### Modelos NSQL

- **350M**: Mais rápido (~1.4GB RAM)
- **2B**: Maior precisão (~8GB RAM)

### Debug

- `FLASK_DEBUG=True`: Logs detalhados, recarga automática
- `FLASK_DEBUG=False`: Modo produção, melhor performance

## Solução de problemas

### Erro de conexão
- Verifique se o banco está executando
- Confirme credenciais no `.env`
- Teste conexão manual

### Erro de memória
- Use NSQL-350M para menor uso de RAM
- Feche outras aplicações
- Aumente RAM disponível

### Modelo não carrega
- Verifique conexão com internet
- Aguarde download completo (primeira execução)
- Confirme se `MODEL_SIZE` é válido (350M ou 2B)

## Tecnologias

- Flask, PyTorch, Transformers (HuggingFace)
- MySQL/PostgreSQL
- HTML, CSS, JavaScript
