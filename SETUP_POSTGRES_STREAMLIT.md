# 🗄️ Setup PostgreSQL + Streamlit

## 📋 Por que PostgreSQL ao invés de SQLite?

| Aspecto | SQLite | PostgreSQL |
|--------|--------|-----------|
| **Concorrência** | ❌ Limitada | ✅ Excelente |
| **Múltiplas conexões** | ❌ Ruim | ✅ Pool de conexões |
| **Escalabilidade** | ❌ Limitada | ✅ Muito escalável |
| **Streamlit** | ⚠️ Problemático | ✅ Perfeito |
| **Produção** | ❌ Não recomendado | ✅ Ideal |
| **Compartilhar dados** | ❌ Arquivo local | ✅ Servidor remoto |

---

## 🚀 Setup Local (Desenvolvimento)

### 1️⃣ Instalar PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**Windows:**
- Download em: https://www.postgresql.org/download/windows/
- Executar installer e seguir instruções

### 2️⃣ Criar Banco de Dados

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco
CREATE DATABASE ml_crawler;

# Criar usuário (opcional, mais seguro)
CREATE USER ml_user WITH PASSWORD 'sua_senha_aqui';
ALTER ROLE ml_user SET client_encoding TO 'utf8';
ALTER ROLE ml_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ml_user SET default_transaction_deferrable TO on;
ALTER ROLE ml_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE ml_crawler TO ml_user;

# Sair
\q
```

### 3️⃣ Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

Edite `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ml_crawler
DB_USER=postgres
DB_PASSWORD=postgres
```

### 4️⃣ Instalar Dependência

```bash
pip install psycopg2-binary
```

---

## 🌐 Setup Remoto (Para Streamlit Cloud)

### Opção 1: Neon (Recomendado - Gratuito)

1. Acesse https://neon.tech
2. Crie conta (suporta GitHub login)
3. Crie novo projeto
4. Copie connection string

Vai parecer assim:
```
postgresql://user:password@ep-xxxx-xxxxx.neon.tech/dbname?sslmode=require
```

5. Parse e coloque no `.env`:
```
DB_HOST=ep-xxxx-xxxxx.neon.tech
DB_PORT=5432
DB_NAME=dbname
DB_USER=user
DB_PASSWORD=password
```

### Opção 2: Railway (Pago mas simples)

1. Acesse https://railway.app
2. Novo projeto → PostgreSQL
3. Copie variáveis de ambiente

### Opção 3: AWS RDS (Mais robusto)

1. Acesse AWS RDS Console
2. Create database → PostgreSQL
3. Copie endpoint e credenciais

---

## 🎯 Usar com Streamlit

### 1️⃣ Instalar Streamlit

```bash
pip install streamlit
```

### 2️⃣ Criar `app.py`

```python
import streamlit as st
from src.database_postgres import get_database
from src.config import CATEGORIAS

st.set_page_config(page_title="ML Crawler Dashboard", layout="wide")

st.title("📊 ML Crawler - Monitorador de Preços")

# Obter banco de dados
db = get_database()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    categoria = st.selectbox("Escolha uma categoria", list(CATEGORIAS.keys()))

# Conteúdo principal
if categoria:
    relatorio = db.obter_relatorio_categoria(categoria)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Produtos", relatorio["total_produtos"])
    
    with col2:
        st.metric("Preço Mínimo", f"R$ {relatorio['preco_minimo']:.2f}")
    
    with col3:
        st.metric("Preço Médio", f"R$ {relatorio['preco_medio']:.2f}")
    
    with col4:
        st.metric("Preço Máximo", f"R$ {relatorio['preco_maximo']:.2f}")
    
    st.markdown("---")
    
    # Lista de produtos
    st.subheader(f"Produtos em {categoria}")
    produtos = db.obter_produtos_por_categoria(categoria)
    
    for produto in produtos[:10]:  # Mostrar 10 primeiros
        with st.expander(f"📦 {produto['nome'][:60]}..."):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Preço:** R$ {produto['preco_atual']:.2f}")
            with col2:
                st.write(f"**Categoria:** {produto['categoria']}")
            with col3:
                st.write(f"**Atualizado:** {produto['ultima_atualizacao']}")
            
            st.markdown(f"[Abrir produto]({produto['link']})")
```

### 3️⃣ Rodar Localmente

```bash
streamlit run app.py
```

Acesse: http://localhost:8501

---

## 🌍 Deploy no Streamlit Cloud

### 1️⃣ Fazer Push para GitHub

```bash
git add .
git commit -m "Add PostgreSQL support"
git push origin main
```

### 2️⃣ Deploy

1. Acesse https://share.streamlit.io
2. Clique "New app"
3. Selecione seu repositório, branch e arquivo `app.py`
4. Clique "Deploy"

### 3️⃣ Adicionar Secrets

No Streamlit Cloud:
1. Vá para Settings → Secrets
2. Adicione suas variáveis de ambiente:

```toml
DB_HOST = "seu-host"
DB_PORT = "5432"
DB_NAME = "ml_crawler"
DB_USER = "seu_user"
DB_PASSWORD = "sua_senha"
```

---

## ✅ Checklist

- [ ] PostgreSQL instalado e rodando
- [ ] Banco `ml_crawler` criado
- [ ] `.env` configurado
- [ ] `psycopg2` instalado
- [ ] `database_postgres.py` testado
- [ ] Streamlit instalado
- [ ] `app.py` criado e rodando localmente
- [ ] GitHub pronto para deploy
- [ ] Secrets configurados no Streamlit Cloud

---

## 🚨 Troubleshooting

### Erro: "could not translate host name to address"
**Solução:** Verifique se PostgreSQL está rodando e `DB_HOST` está correto

### Erro: "password authentication failed"
**Solução:** Confira as credenciais no `.env`

### Erro: "Streamlit connection timeout"
**Solução:** Verifique se o banco remoto permite conexões de fora

### Erro: "too many connections"
**Solução:** Aumente o pool ou limite as conexões abertas

---

## 📊 Próximas Etapas

1. Refatorar `scraper.py` para usar `database_postgres.py`
2. Criar `tasks.py` com Prefect
3. Expandir dashboard Streamlit com gráficos
4. Deploy em Streamlit Cloud

**Tudo funcionará perfeitamente!** ✅
