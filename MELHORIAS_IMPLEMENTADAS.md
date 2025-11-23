# Melhorias Implementadas no ML Crawler

## 🎯 Objetivo
Melhorar o monitorador de preços para capturar:
- Preço original (antes do desconto)  
- Preço atual (com desconto)
- Percentual de desconto
- Imagem dos produtos

## ✅ Mudanças Realizadas

### 1. **Modelos de Dados** (`src/models.py`)
- ➕ `preco_original`: Preço antes do desconto
- ➕ `percentual_desconto`: Percentual de desconto aplicado  
- ➕ `imagem_url`: URL da imagem do produto
- 🔄 Atualizado exemplo de uso no schema

### 2. **Scraper** (`src/scraper.py`)
- 🔍 Novos seletores CSS para extrair:
  - Preço original: `s.andes-money-amount--previous`, `.price-tag-previous__label`
  - Imagens: `img.ui-search-result-image__element`, `img`
- 🧮 Cálculo automático do percentual de desconto
- 📊 Retorno de dados enriquecidos nos produtos

### 3. **Banco de Dados**

#### PostgreSQL (`src/database_postgres.py`)
- 🗃️ Novos campos na tabela `produtos`:
  - `preco_original NUMERIC(10, 2)`
  - `percentual_desconto NUMERIC(5, 2)`
  - `imagem_url TEXT`
- 🔄 Migração automática com `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- ✏️ Método `adicionar_produto()` atualizado

#### SQLite (`src/database.py`)
- 🗃️ Mesmos campos adicionados à tabela `produtos`
- 🔄 Migração com tratamento de exceção
- ➕ Método `obter_produto_por_id_ml()` adicionado
- ✏️ Método `adicionar_produto()` atualizado

### 4. **Dashboard** (`app.py`)
- 🏷️ **Badge de desconto** no título dos produtos
- 🖼️ **Exibição de imagens** dos produtos (120px)
- 💰 **Preços melhorados**:
  - Preço atual em destaque
  - Preço original riscado (quando há desconto)
  - Métricas de desconto atual vs. variação histórica
- 📊 Layout responsivo com colunas para imagem + informações

## 🚀 Como Testar

### Testar Scraper:
```bash
python test_scraper_melhorado.py
```

### Executar Coleta:
```bash
python -m src.main "https://lista.mercadolivre.com.br/celular" 20 2
```

### Ver Dashboard:
```bash
streamlit run app.py
```

## 📈 Resultados Esperados

### No Dashboard:
- ✅ Produtos com desconto mostram badge "🏷️ X% OFF"
- ✅ Preço original riscado quando há desconto
- ✅ Imagens dos produtos exibidas
- ✅ Diferenciação entre desconto atual e variação histórica

### Na Coleta:
- ✅ Captura automática de preços originais quando disponíveis
- ✅ Cálculo preciso de percentuais de desconto
- ✅ URLs de imagem coletadas e armazenadas
- ✅ Compatibilidade com produtos sem desconto

## 🔧 Compatibilidade
- ✅ **Retrocompatível**: produtos antigos continuam funcionando
- ✅ **Campos opcionais**: novos campos são opcionais
- ✅ **Migração automática**: banco atualizado automaticamente
- ✅ **Fallback**: dashboard funciona mesmo sem os novos dados

## 🎉 Próximos Passos Sugeridos
1. **Alertas de desconto**: notificar quando um produto entrar em promoção
2. **Histórico de descontos**: rastrear variações de desconto ao longo do tempo
3. **Comparação de preços**: comparar com outros sites
4. **Wishlist**: lista de produtos favoritos para monitoramento prioritário