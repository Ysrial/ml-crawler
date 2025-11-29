# 📋 Resumo das Alterações - ML Crawler

## ✅ Correções Implementadas

### 1. **Parsing de Preços com Vírgula** ✨
**Arquivo**: `src/utils.py`

**Problema**: Função `text_to_price()` não diferenciava entre:
- `249.90` (ponto como separador decimal)
- `249,90` (vírgula como separador decimal - português)
- `1.249,50` (ponto como separador de milhares + vírgula decimal)

**Solução**:
- Detecta automaticamente o formato brasileiro
- Trata casos com múltiplos separadores
- Valida valores absurdos (< 0.01 ou > 1.000.000)
- Retorna float arredondado com 2 casas decimais

```python
# Exemplos que agora funcionam:
text_to_price("249,90")      # → 249.90
text_to_price("1.249,50")    # → 1249.50
text_to_price("249.90")      # → 249.90
text_to_price("R$ 1.249,99") # → 1249.99
```

---

### 2. **Extração de Preço Único** 🔧
**Arquivo**: `src/scraper.py`

**Problema**: Quando havia apenas uma fração de preço, não diferenciava se era preço original ou atual.

**Solução**:
- Analisa classe CSS do elemento pai
- Se detecta "strike", "original" ou "subprice" → preço original
- Caso contrário → preço atual
- Melhor compatibilidade com layouts variados do ML

```python
# Debug melhorado:
# debug: preço via andes_fractions (1) — detectado como ORIGINAL
# debug: preço via andes_fractions (1) — assumindo ATUAL
```

---

### 3. **Suporte a Proxies** 🌐
**Arquivos**: `src/config.py`, `src/scraper.py`

**Problema**: Mercado Livre bloqueia requisições repetidas do mesmo IP (429/403).

**Solução Implementada**:

#### Em `config.py`:
- Variável `USE_PROXY` para habilitar/desabilitar
- Lista de múltiplos proxies com rotação automática
- Suporte a proxy único ou lista
- User-agents rotativos (9 diferentes)

#### Em `scraper.py`:
- Nova função `fetch_html()` com suporte a proxies
- Escolhe proxy aleatório de `PROXY_LIST`
- Fallback automático (sem proxy se proxy falhar)
- Headers melhorados com idioma e compressão
- Timeout aumentado para 15s

**Como usar**:

```bash
# Ativar suporte a proxies
USE_PROXY=true

# Opção 1: Proxy único
SINGLE_PROXY=http://185.123.456.789:8080

# Opção 2: Múltiplos proxies (recomendado)
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080,http://proxy3.com:8080

# Suporta SOCKS5
SINGLE_PROXY=socks5://185.123.456.789:1080
```

---

### 4. **Novo Card no Dashboard** 📊
**Arquivo**: `app.py`

#### Card 1: Status da Última Coleta
```
[✅ Última Coleta] [📦 Novos Produtos] [🔄 Atualizados]
   28/11 15:30          125 produtos        42 preços
```
- Exibe data/hora da última coleta
- Total de novos produtos encontrados
- Total de preços atualizados

#### Card 2: Produtos em Destaque
Duas abas:

**Maiores Descontos**:
- Top 3 produtos com maior desconto
- Mostra preço original vs. atual
- Link direto para Mercado Livre
- Ícone 🏷️ destacando desconto

**Maior Variação de Preço**:
- Top 3 produtos com maior variação histórica
- Indicadores 🔴 (aumento) e 🟢 (redução)
- Mostra preço mín/máx/atual
- Link direto para cada produto

---

## 📂 Arquivos Novos

### `PROXIES.md`
Documentação completa sobre:
- Como configurar proxies
- Onde encontrar (gratuitos e pagos)
- Como testar funcionamento
- Dicas de troubleshooting
- Alternativas (ScraperAPI)

### `.env.example`
Atualizado com:
- Variáveis de proxy
- Exemplos de configuração
- Links úteis para recursos

---

## 🔄 Fluxo de Requisição Melhorado

```
┌─────────────────────────────────────┐
│ Requisição HTTP para Mercado Livre  │
├─────────────────────────────────────┤
│ 1. Escolher User-Agent aleatório    │ (9 opções)
│ 2. Se USE_PROXY=true:               │
│    - Escolher proxy de PROXY_LIST    │
│    - Ou usar SINGLE_PROXY            │
│ 3. Enviar requisição                │ (timeout 15s)
│ 4. Se proxy falhar → retry sem proxy│ (fallback)
│ 5. Parse HTML com Beautiful Soup    │
│ 6. Extrair preço com text_to_price()│ (novo parsing)
└─────────────────────────────────────┘
```

---

## 🧪 Como Testar

### Testar Parsing de Preços:
```bash
cd /home/israel/ml-crawler
python3 -c "from src.utils import text_to_price; print(text_to_price('1.249,99'))"
# Output: 1249.99
```

### Testar com Proxies:
```bash
# Editar .env
USE_PROXY=true
SINGLE_PROXY=http://seu-proxy:8080

# Rodar scraper
python3 src/main.py
# Logs mostrarão: [PROXY] Usando proxy único: http://...
```

### Testar Dashboard:
```bash
streamlit run app.py
# Acessar: http://localhost:8501
# Ver novo card com coletas e produtos em destaque
```

---

## 📊 Status Final

| Funcionalidade | Status | Detalhes |
|---|---|---|
| Parsing de preços | ✅ Corrigido | Suporta formatos brasileiros |
| Preço único | ✅ Melhorado | Detecta original vs. atual |
| Suporte a proxies | ✅ Implementado | Rotação automática + fallback |
| Card dashboard | ✅ Adicionado | Status + top produtos |
| Documentação | ✅ Criada | PROXIES.md completo |

---

## 🚀 Próximas Sugestões

1. **Rate Limiting**: Adicionar delay entre requisições
2. **Proxy Validation**: Testar proxies antes de usar
3. **Cache de HTML**: Evitar re-scraping do mesmo conteúdo
4. **Alerts**: Notificar quando desconto > 50% ou preço cai
5. **Export**: Gerar relatórios em PDF/Excel

---

**Data**: 28/11/2025
**Versão**: ML Crawler v1.1
