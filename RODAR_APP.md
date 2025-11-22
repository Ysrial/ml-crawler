# 🚀 Como Rodar o App - Guia Rápido

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL instalado e rodando
- Git

---

## ⚡ Início Rápido (5 minutos)

### 1️⃣ Instalar PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**Windows:**
- Download: https://www.postgresql.org/download/windows/
- Executar installer

---

### 2️⃣ Criar Banco de Dados

```bash
# Abrir psql
psql -U postgres

# Criar banco (dentro do psql)
CREATE DATABASE ml_crawler;
\q
```

---

### 3️⃣ Clonar o Projeto

```bash
git clone https://github.com/Ysrial/ml-crawler.git
cd ml-crawler
```

---

### 4️⃣ Configurar Variáveis de Ambiente

```bash
# Copiar arquivo exemplo
cp .env.example .env

# Editar .env (abra no seu editor favorito)
# Deixe assim (padrão local):
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=ml_crawler
# DB_USER=postgres
# DB_PASSWORD=postgres
```

---

### 5️⃣ Instalar Dependências

```bash
# Se estiver usando venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instalar pacotes
pip install -r requirements.txt
```

---

### 6️⃣ Inicializar o Banco

```bash
python -c "from src.database_postgres import db; db.initialize_db(); print('✅ Banco criado!')"
```

---

### 7️⃣ Popular com Dados (Opcional)

Para testar com alguns dados:

```bash
python -c "
from src.database_postgres import get_database
from src.models import Produto

db = get_database()

# Adicionar um produto de teste
produto_teste = Produto(
    nome='iPhone 15 Pro Max',
    preco=7999.99,
    link='https://produto.mercadolivre.com.br/test',
    categoria='celulares'
)
db.adicionar_produto(produto_teste)
print('✅ Produto de teste adicionado!')
"
```

---

### 8️⃣ Rodar o Streamlit

```bash
streamlit run app.py
```

**Pronto!** 🎉 O app abrirá em: `http://localhost:8501`

---

## 🧪 Testar Tudo Funciona

### Verificar Conexão

```bash
python -c "
from src.database_postgres import db
print('✅ Conexão com PostgreSQL OK!')
"
```

### Verificar Streamlit

```bash
streamlit hello
```

Se ambos funcionarem, você está pronto!

---

## 🎯 Próximos Passos

### Depois que o app está rodando:

1. **Rodar o Scraper** (coleta dados):
```bash
python -m src.main "https://lista.mercadolivre.com.br/celular" 50 2
```

2. **Atualizar o dashboard** - Volta ao browser (localhost:8501) e dá refresh

3. **Acompanhar dados** - Veja os produtos sendo monitorados

---

## ⚠️ Erros Comuns

### ❌ "could not translate host name"
```
Solução: PostgreSQL não está rodando
brew services start postgresql@15
```

### ❌ "FATAL: database ml_crawler does not exist"
```
Solução: Banco não foi criado
createdb ml_crawler
```

### ❌ "ModuleNotFoundError"
```
Solução: Dependências não instaladas
pip install -r requirements.txt
```

### ❌ "Connection refused on 127.0.0.1:5432"
```
Solução: PostgreSQL não está ativo
brew services start postgresql@15
```

---

## 📱 Acessar Remotamente

Se quiser acessar de outro computador:

1. Copie o IP local da máquina (ex: 192.168.1.100)
2. Rodê o app com:
```bash
streamlit run app.py --server.address 0.0.0.0
```
3. Acesse: `http://192.168.1.100:8501`

---

## 🆘 Precisa de Ajuda?

```bash
# Ver versões instaladas
python --version
pip show streamlit
psql --version

# Ver status do PostgreSQL
brew services list

# Reiniciar PostgreSQL
brew services restart postgresql@15
```

---

**Dúvida?** Rode os comandos acima que tudo funciona! ✅
