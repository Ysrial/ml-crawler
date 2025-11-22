# 📋 Roadmap: ML Crawler com Monitoramento de Preços

## Objetivo
Transformar o scraper em um **monitorador de preços com histórico**, coletando dados de múltiplas categorias automaticamente via Prefect.

---

## 📂 Estrutura Final do Projeto

```
ml-crawler/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI principal
│   ├── scraper.py              # Scraping (refatorado)
│   ├── utils.py                # Utilitários
│   ├── models.py               # ✨ NOVO: Modelos Pydantic
│   ├── database.py             # ✨ NOVO: Gerenciamento BD
│   ├── config.py               # ✨ NOVO: Categorias e URLs
│   ├── tasks.py                # ✨ NOVO: Tasks Prefect
│   └── analysis.py             # ✨ NOVO: Análise de dados
├── data/
│   └── ml_crawler.db           # ✨ NOVO: Banco SQLite
├── logs/                       # ✨ NOVO: Logs de execução
├── reports/                    # ✨ NOVO: Relatórios gerados
├── produtos.json               # (Manter compatibilidade)
├── requirements.txt            # (Atualizar dependências)
└── README.md
```

---

## 🎯 Passo a Passo de Implementação

### PASSO 1️⃣: Definir Categorias de Produtos
**Arquivo:** `src/config.py`

```python
CATEGORIAS = {
    "celulares": {
        "url": "https://lista.mercadolivre.com.br/celular",
        "max_paginas": 5,
        "descricao": "Smartphones e celulares"
    },
    "pcs": {
        "url": "https://lista.mercadolivre.com.br/computador-desktop",
        "max_paginas": 5,
        "descricao": "Computadores desktop"
    },
    "notebooks": {
        "url": "https://lista.mercadolivre.com.br/notebook",
        "max_paginas": 5,
        "descricao": "Notebooks e laptops"
    },
    "eletronicos": {
        "url": "https://lista.mercadolivre.com.br/eletronico",
        "max_paginas": 3,
        "descricao": "Eletrônicos em geral"
    },
    "casa_lar": {
        "url": "https://lista.mercadolivre.com.br/movel",
        "max_paginas": 3,
        "descricao": "Móveis e artigos de casa"
    }
}

DATABASE_PATH = "data/ml_crawler.db"
LOG_DIR = "logs"
REPORT_DIR = "reports"
```

### PASSO 2️⃣: Criar Modelo de Dados (Pydantic)
**Arquivo:** `src/models.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Produto(BaseModel):
    nome: str
    preco: float
    link: str
    categoria: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Samsung Galaxy A12",
                "preco": 599.99,
                "link": "https://...",
                "categoria": "celulares",
                "timestamp": "2024-11-20T10:30:00"
            }
        }

class ProdutoHistorico(BaseModel):
    produto_id: int
    preco: float
    data: datetime = Field(default_factory=datetime.now)
```

### PASSO 3️⃣: Configurar Banco de Dados
**Arquivo:** `src/database.py`

**Schema:**
```sql
-- Tabela de Produtos
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    link TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL,
    preco_atual REAL,
    primeira_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Histórico de Preços
CREATE TABLE IF NOT EXISTS precos_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    preco REAL NOT NULL,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- Tabela de Coletas
CREATE TABLE IF NOT EXISTS coletas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    total_produtos INTEGER,
    status TEXT -- 'sucesso', 'erro'
);
```

### PASSO 4️⃣: Integrar Scraper com BD
**Modificação:** `src/scraper.py`

Ao invés de retornar apenas a lista, salvar direto no BD:

```python
def salvar_produto_bd(db, produto: Produto):
    """Salva produto no BD e cria histórico de preço"""
    try:
        # Verifica se já existe
        produto_existente = db.query(Produto).filter_by(
            nome=produto.nome, 
            link=produto.link
        ).first()
        
        if produto_existente:
            # Atualiza preço
            produto_existente.preco_atual = produto.preco
            produto_existente.ultima_atualizacao = datetime.now()
            db.add(PrecosHistorico(
                produto_id=produto_existente.id,
                preco=produto.preco
            ))
        else:
            # Cria novo
            db.add(produto)
            db.flush()
            db.add(PrecosHistorico(
                produto_id=produto.id,
                preco=produto.preco
            ))
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao salvar: {e}")
```

### PASSO 5️⃣: Configurar Prefect para Agendamento
**Arquivo:** `src/tasks.py`

```python
from prefect import flow, task
from datetime import datetime, timedelta
import schedule

@task
def scrape_categoria(categoria: str):
    """Task Prefect para scraping de uma categoria"""
    print(f"🚀 Iniciando scraping: {categoria}")
    # Executar scraper e salvar BD
    
@flow
def coleta_diaria():
    """Flow que coleta todas as categorias"""
    categorias = list(CATEGORIAS.keys())
    for cat in categorias:
        scrape_categoria(cat)
    print("✅ Coleta diária concluída")

# Agendar para rodar a cada 6 horas
if __name__ == "__main__":
    coleta_diaria.serve(
        cron="0 0,6,12,18 * * *"  # A cada 6 horas
    )
```

### PASSO 6️⃣: Análise de Histórico
**Arquivo:** `src/analysis.py`

```python
def gerar_relatorio_variacao(produto_id: int):
    """Analisa variação de preço de um produto"""
    historico = db.query(PrecosHistorico).filter_by(
        produto_id=produto_id
    ).all()
    
    precos = [h.preco for h in historico]
    
    return {
        "preco_minimo": min(precos),
        "preco_maximo": max(precos),
        "preco_medio": sum(precos) / len(precos),
        "variacao_percentual": ((precos[-1] - precos[0]) / precos[0]) * 100
    }
```

---

## 📦 Dependências Novas

```
prefect==3.0.0           # Agendamento e orquestração
pydantic==2.5.0          # Validação de dados
sqlalchemy==2.0.0        # ORM para BD
sqlite3                  # Já vem com Python
python-dotenv==1.1.0     # Variáveis de ambiente
```

---

## 🚀 Ordem de Implementação

1. **Instalar dependências** → `pip install -r requirements.txt`
2. **Criar `config.py`** → Definir categorias
3. **Criar `models.py`** → Modelos Pydantic
4. **Criar `database.py`** → Schema e funções BD
5. **Refatorar `scraper.py`** → Integrar com BD
6. **Criar `tasks.py`** → Prefect tasks e flows
7. **Criar `analysis.py`** → Scripts de análise
8. **Testar manualmente** → Rodar uma coleta
9. **Ativar schedule** → Deixar rodando

---

## ✅ Checklist de Implementação

- [ ] Passo 1: Categorias configuradas
- [ ] Passo 2: Modelos Pydantic criados
- [ ] Passo 3: Banco de dados configurado
- [ ] Passo 4: Scraper integrado com BD
- [ ] Passo 5: Prefect tasks criadas
- [ ] Passo 6: Scripts de análise prontos
- [ ] Banco com histórico de 1 semana
- [ ] Dashboard básico funcionando
- [ ] README atualizado

---

## 📊 Resultado Esperado

Após implementar tudo:

```
✅ Coletas automáticas a cada 6 horas
✅ Banco de dados com histórico de preços
✅ 5+ categorias monitoradas
✅ Relatórios de variação de preço
✅ Base de dados para comparação
✅ Pronto para fase 2: Comparador de Preços
```

---

**Próximo Passo:** Começar pelo Passo 1 (Categorias)
