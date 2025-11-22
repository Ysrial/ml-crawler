# ⚡ RODAR APP - RESUMO RÁPIDO

## 🎯 Forma Mais Fácil (Docker - Recomendado)

### Pré-requisitos
- Docker Desktop instalado

### 1 Comando:
```bash
docker-compose up -d && pip install -r requirements.txt && streamlit run app.py
```

Pronto! Acesse: http://localhost:8501

---

## 🐳 OU Script Automático

```bash
bash start.sh
```

Depois:
```bash
streamlit run app.py
```

---

## 📋 OU Manual em 4 Passos (Docker)

```bash
# 1. Subir PostgreSQL
docker-compose up -d

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar app
streamlit run app.py

# 4. Acessar
# http://localhost:8501
```

---

## 🧪 Testar Depois

Para popular com dados:

```bash
# Fazer scraping de celulares (50 produtos, 2 páginas)
python -m src.main "https://lista.mercadolivre.com.br/celular" 50 2
```

Depois volta no browser e dá refresh no Streamlit!

---

## ✅ Checklist

- [ ] PostgreSQL rodando? (`psql --version`)
- [ ] Banco criado? (`psql -l` e procure por `ml_crawler`)
- [ ] Dependências instaladas? (`pip list | grep streamlit`)
- [ ] `.env` configurado? (`cat .env`)
- [ ] App rodando? (`streamlit run app.py`)
- [ ] Pode acessar? (`http://localhost:8501`)

---

**Dúvida?** Veja: `RODAR_APP.md` ou `SETUP_POSTGRES_STREAMLIT.md`
