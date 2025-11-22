# 🐳 Docker + Produção (Streamlit Cloud)

## 🎯 Visão Geral

```
Desenvolvimento Local          →        Produção (Streamlit Cloud)
┌──────────────────────┐                ┌──────────────────────┐
│ Docker Compose       │                │ Streamlit Cloud      │
│ PostgreSQL + App     │                │ Neon/Railway BD      │
│ (localhost:8501)     │                │ (share.streamlit.io) │
└──────────────────────┘                └──────────────────────┘
```

---

## 🚀 LOCAL COM DOCKER (Recomendado)

### Pré-requisitos
- Docker instalado
- Docker Compose instalado

### 1️⃣ Iniciar Container

```bash
# Subir PostgreSQL + criar banco
docker-compose up -d

# Verificar se está rodando
docker-compose ps
```

**Output esperado:**
```
NAME                 STATUS              PORTS
ml_crawler_db        Up 2 minutes        0.0.0.0:5432->5432/tcp
```

### 2️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3️⃣ Rodar App

```bash
streamlit run app.py
```

**Acesse:** http://localhost:8501

---

### ✅ Comandos Docker Úteis

```bash
# Ver logs
docker-compose logs postgres

# Acessar banco de dados
docker-compose exec postgres psql -U postgres -d ml_crawler

# Parar container
docker-compose down

# Remover volumes (limpar dados)
docker-compose down -v

# Reiniciar tudo
docker-compose restart
```

---

## 🌍 PRODUÇÃO (Streamlit Cloud)

### Opção 1: Neon.tech (Recomendado - Gratuito)

#### 1️⃣ Criar Banco Neon

1. Acesse: https://neon.tech
2. Sign up com GitHub
3. Create new project
4. Copie a connection string

**String será assim:**
```
postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require
```

#### 2️⃣ Extrair Credenciais

Da string acima:
```
DB_HOST=ep-xxxx.neon.tech
DB_PORT=5432
DB_NAME=dbname
DB_USER=user
DB_PASSWORD=password
```

#### 3️⃣ Configurar Secrets no Streamlit Cloud

No dashboard do Streamlit Cloud:
1. Settings → Secrets
2. Adicione em formato TOML:

```toml
DB_HOST = "ep-xxxx.neon.tech"
DB_PORT = "5432"
DB_NAME = "dbname"
DB_USER = "user"
DB_PASSWORD = "password"
```

#### 4️⃣ Fazer Push para GitHub

```bash
git add .
git commit -m "Add production config"
git push origin main
```

#### 5️⃣ Deploy no Streamlit Cloud

1. Acesse: https://share.streamlit.io
2. New app → Select repository
3. Branch: main
4. File path: app.py
5. Deploy!

---

### Opção 2: Railway.app (Pago mas Simples)

1. Acesse: https://railway.app
2. Create new project
3. Add a PostgreSQL service
4. Copie as credenciais
5. Adicione aos secrets do Streamlit

---

### Opção 3: AWS RDS (Mais Robusto)

1. AWS RDS Console → Create database
2. Engine: PostgreSQL
3. Copie endpoint
4. Adicione aos secrets

---

## 🔄 Como Funciona em Produção

```
Seu Código no GitHub
        ↓
   Streamlit Cloud
        ↓
  Lê .streamlit/secrets.toml
        ↓
  Conecta ao BD Remoto (Neon/Railway)
        ↓
  App roda em: https://seu-app.streamlit.app
```

---

## 📝 Arquivo de Configuração

O arquivo `src/config.py` detecta automaticamente se é LOCAL ou PRODUÇÃO:

```python
# Se estiver rodando no Streamlit Cloud, usa variáveis de environment
# Se não, tenta conectar ao localhost:5432

# Streamlit Cloud identifica por: os.getenv("STREAMLIT_SHARING_SECRET")
```

---

## ✅ Checklist Setup Docker

- [ ] Docker instalado? (`docker --version`)
- [ ] Docker Compose instalado? (`docker-compose --version`)
- [ ] Container subindo? (`docker-compose up -d`)
- [ ] App conecta ao BD? (sem erros no terminal)
- [ ] Dashboard funciona? (http://localhost:8501)

---

## ✅ Checklist Produção

- [ ] Neon.tech account criado
- [ ] PostgreSQL criado em Neon
- [ ] GitHub repo criado
- [ ] Código fazer push
- [ ] Streamlit Cloud configurado
- [ ] Secrets adicionados
- [ ] Deploy realizado
- [ ] App rodando em: https://seu-app.streamlit.app

---

## 🚨 Troubleshooting Docker

### ❌ "docker-compose: command not found"
```
Solução: Instalar Docker Desktop (inclui Compose)
https://www.docker.com/products/docker-desktop
```

### ❌ "Connection refused on 127.0.0.1:5432"
```
Solução: Container não está rodando
docker-compose up -d
docker-compose ps
```

### ❌ "Port 5432 already in use"
```
Solução: Outro serviço usando a porta
docker-compose down
# ou
docker-compose down -v  # remove volumes também
```

### ❌ "permission denied while trying to connect to Docker daemon"
```
Solução (Linux): sudo docker-compose up -d
ou adicione usuário ao grupo: sudo usermod -aG docker $USER
```

---

## 🚨 Troubleshooting Produção

### ❌ "Secrets not found" no Streamlit Cloud
```
Solução: Recarregar a página ou fazer novo deploy
git commit --allow-empty -m "Trigger redeploy"
git push
```

### ❌ "Connection timeout" no BD remoto
```
Solução: Verificar whitelist de IP
Neon.tech: Settings → Connection pooling
Railway: Settings → Networking
```

### ❌ "Password authentication failed"
```
Solução: Verificar credenciais nos secrets
Copiar exatamente como vem do Neon/Railway
```

---

## 📊 Próximos Passos

1. Usar Docker local para desenvolvimento
2. Deploy em Streamlit Cloud
3. Adicionar Prefect para agendamento
4. Expandir dashboard com mais gráficos

---

## 🎯 Resumo Rápido

### Local (Docker)
```bash
docker-compose up -d
pip install -r requirements.txt
streamlit run app.py
```

### Produção (Neon + Streamlit Cloud)
```bash
# 1. Criar BD no Neon
# 2. Copiar credenciais
# 3. Adicionar aos secrets do Streamlit
# 4. Fazer push para GitHub
# 5. Deploy em https://share.streamlit.io
```

---

**Pronto!** 🚀 Seu app rodará localmente com Docker e em produção com Streamlit Cloud!
