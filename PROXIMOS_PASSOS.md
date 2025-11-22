# 🚀 Guia: Próximos Passos

## ✅ O que foi criado até agora:

1. **`config.py`** - Configuração centralizada com categorias
2. **`models.py`** - Modelos Pydantic para validação
3. **`database.py`** - Gerenciador completo de BD SQLite
4. **`requirements.txt`** - Dependências atualizadas

---

## 📋 Próximas Etapas (em ordem):

### 1️⃣ **Instalar Dependências** ⚡
```bash
pip install -r requirements.txt
```

### 2️⃣ **Testar o Banco de Dados** 🧪
```bash
python -c "from src.database import db; print('✅ BD criado em: data/ml_crawler.db')"
```

### 3️⃣ **Refatorar `scraper.py`** 🔄
Modificar a função `scrape_all_pages()` para:
- Receber a categoria como parâmetro
- Salvar produtos no banco de dados
- Criar histórico de preços
- Retornar estatísticas da coleta

**Mudanças principais:**
```python
def scrape_all_pages(categoria: str, url: str, max_pages: int):
    """
    Coleta produtos e salva no banco de dados
    """
    from .database import db
    from .models import Produto
    
    coleta_id = db.iniciar_coleta(categoria)
    total_novos = 0
    total_atualizados = 0
    
    for page in range(1, max_pages + 1):
        # ... scraping ...
        for produto_data in produtos:
            produto = Produto(
                nome=produto_data["nome"],
                preco=produto_data["preco"],
                link=produto_data["link"],
                categoria=categoria
            )
            
            # Verifica se já existe
            existente = db.obter_produto_por_link(produto.link)
            if existente:
                db.atualizar_preco(existente["id"], produto.preco)
                total_atualizados += 1
            else:
                db.adicionar_produto(produto)
                total_novos += 1
    
    db.finalizar_coleta(coleta_id, len(produtos), total_novos, total_atualizados, True)
```

### 4️⃣ **Criar `tasks.py`** (Prefect) 📅
Criar tasks Prefect para:
- Scraping de cada categoria
- Flow que executa todas as categorias
- Schedule para rodar a cada 6 horas

### 5️⃣ **Criar `analysis.py`** 📊
Scripts para:
- Gerar estatísticas de produtos
- Relatórios por categoria
- Exportar dados para CSV/JSON

### 6️⃣ **Atualizar `main.py`** 🎛️
Adicionar commands para:
- Executar coleta manual de uma categoria
- Visualizar estatísticas
- Gerar relatórios

---

## 🎯 Meta da Fase 1

Ter um sistema funcional que:
- ✅ Coleta produtos de 5 categorias
- ✅ Salva no banco de dados
- ✅ Cria histórico de preços
- ✅ Executa automaticamente a cada 6 horas
- ✅ Gera relatórios básicos

---

## 🧪 Teste Rápido

Depois de instalar, rode:

```bash
# Testar configuração
python -c "from src.config import CATEGORIAS; print(f'Categorias: {list(CATEGORIAS.keys())}')"

# Testar models
python -c "from src.models import Produto; p = Produto(nome='Teste', preco=100, link='https://test.com', categoria='teste'); print(p)"

# Testar banco
python -c "from src.database import db; print('✅ Banco criado!')"
```

---

## 📝 Checklist Hands-On

- [ ] Instalou dependências? (`pip install -r requirements.txt`)
- [ ] BD foi criado? (verifique em `data/ml_crawler.db`)
- [ ] Modelos estão funcionando?
- [ ] Database testes passam?
- [ ] Pronto para refatorar `scraper.py`?

---

**Próximo: Refatore o `scraper.py` para integrar com o banco! 🚀**
