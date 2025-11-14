# ML Crawler 🕷️

Um web scraper poderoso e eficiente para extrair dados de produtos do Mercado Livre Brasil com suporte a **paginação automática**.

## 📋 Descrição

ML Crawler é uma ferramenta desenvolvida em Python que permite coletar informações de produtos (nome, preço e link) diretamente do Mercado Livre. Ideal para análise de preços, pesquisa de mercado, comparação de produtos e estudo de web scraping.

**Funcionalidades principais:**
- ✅ Extração automática de dados de produtos
- ✅ Suporte a paginação (múltiplas páginas)
- ✅ Detecção dinâmica de seletores CSS
- ✅ Exportação em JSON
- ✅ Tratamento robusto de erros
- ✅ Logs informativos em tempo real

## 🚀 Quick Start

### Pré-requisitos

- Python 3.7+
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:
```bash
git clone <seu-repositório>
cd ml-crawler
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Uso Básico

Execute o script com uma URL do Mercado Livre:

```bash
# Scraping da URL padrão
python -m src.main

# Scraping com URL específica
python -m src.main "https://lista.mercadolivre.com.br/celular"

# Com limite de produtos (ex: 100 produtos)
python -m src.main "https://lista.mercadolivre.com.br/celular" 100

# Com limite de produtos E páginas (ex: 100 produtos, máximo 5 páginas)
python -m src.main "https://lista.mercadolivre.com.br/celular" 100 5
```

## 📦 Estrutura do Projeto

```
ml-crawler/
├── src/
│   ├── main.py          # Ponto de entrada da aplicação
│   ├── scraper.py       # Lógica de scraping e paginação
│   └── utils.py         # Funções utilitárias
├── produtos.json        # Arquivo de saída com produtos extraídos
├── requirements.txt     # Dependências do projeto
└── README.md           # Este arquivo
```

## 🔧 Componentes

### `main.py`
Orquestra a execução do scraper. Recebe parâmetros via linha de comando:
- `URL`: URL do Mercado Livre (opcional)
- `max_produtos`: Número máximo de produtos (opcional)
- `max_paginas`: Número máximo de páginas (opcional, padrão: 10)

### `scraper.py`
Contém as principais funções de scraping:

- **`fetch_html(url: str) -> str`**
  - Faz requisição HTTP à URL
  - Retorna o HTML da página
  - Exibe status HTTP

- **`detect_selector(html: str) -> str`**
  - Detecta automaticamente qual seletor CSS usar
  - Suporta múltiplos layouts do Mercado Livre
  - Retorna None se nenhum seletor for encontrado

- **`extract_products(html: str, limit: int) -> list`**
  - Extrai produtos do HTML
  - Limita quantidade de produtos por página
  - Retorna lista com nome, preço e link

- **`add_pagination_to_url(url: str, page: int) -> str`**
  - Adiciona/atualiza parâmetro `_Paging` na URL
  - Preserva outros parâmetros existentes
  - Retorna URL paginada

- **`scrape_all_pages(base_url: str, max_products: int, max_pages: int) -> list`**
  - Itera sobre múltiplas páginas
  - Para automaticamente quando não há mais produtos
  - Respeita limites de produtos e páginas

### `utils.py`
Utilitários para processamento de dados:

- **`text_to_price(s: str) -> float`**
  - Converte texto em preço numérico
  - Remove caracteres especiais
  - Trata vírgulas e pontos corretamente

## 📊 Formato de Saída

O arquivo `produtos.json` gerado contém:

```json
[
  {
    "nome": "Samsung Galaxy A12 128GB",
    "preco": 599.99,
    "link": "https://produto.mercadolivre.com.br/..."
  },
  {
    "nome": "iPhone 12 64GB",
    "preco": 3299.00,
    "link": "https://produto.mercadolivre.com.br/..."
  }
]
```

## 🎯 Exemplos de Uso

### Exemplo 1: Buscar Todos os Celulares (sem limites)
```bash
python -m src.main "https://lista.mercadolivre.com.br/celular"
```

### Exemplo 2: Primeiros 50 produtos de Notebooks
```bash
python -m src.main "https://lista.mercadolivre.com.br/notebook" 50
```

### Exemplo 3: Análise de Laptops (3 páginas, máximo 150 produtos)
```bash
python -m src.main "https://lista.mercadolivre.com.br/laptop" 150 3
```

### Exemplo 4: Busca com filtros do Mercado Livre
```bash
python -m src.main "https://lista.mercadolivre.com.br/smartphone/_PriceRange_100000-500000" 100 5
```

## 🛠️ Requisitos

Veja `requirements.txt`:

```
requests==2.31.0      # Requisições HTTP
beautifulsoup4==4.12.2 # Parsing HTML
lxml==4.9.3           # Parser XML/HTML rápido
```

## ⚠️ Notas Importantes

- **Respeite o `robots.txt`**: Mercado Livre pode ter limitações para scraping automático
- **Delays entre requisições**: Considere adicionar delays para não sobrecarregar os servidores
- **Mudanças na estrutura HTML**: O site pode mudar, afetando os seletores CSS
- **Termos de Serviço**: Verifique a viabilidade legal do seu projeto

## 🚨 Troubleshooting

### Problema: "❌ Nenhum seletor compatível encontrado"
**Solução:** O HTML do Mercado Livre pode ter mudado. Atualize os seletores em `detect_selector()`

### Problema: "Timeout Error"
**Solução:** Aumente o timeout em `fetch_html()` ou verifique sua conexão

### Problema: Preços não estão sendo extraídos
**Solução:** Verifique se a função `text_to_price()` está processando corretamente o formato

## 📈 Melhorias Futuras

### Fase 1: Monitoramento de Preços
- [ ] **Agendamento automático (APScheduler)**
  - Executar scraping em intervalos regulares (ex: a cada 6 horas)
  - Histórico de coletas automático
  - Logs de execução

- [ ] **Banco de dados (SQLite/PostgreSQL)**
  - Armazenar histórico de preços
  - Rastrear mudanças de preço por produto
  - Schema: `produtos`, `precos_historico`, `buscas`

- [ ] **Monitoramento de mudanças de preço**
  - Alertas quando preço cai/sobe
  - Comparação com preço anterior
  - Relatórios de variação percentual

### Fase 2: Análise e Visualização
- [ ] **Interface gráfica (Streamlit)**
  - Dashboard com gráficos de preços
  - Filtros por categoria/produto
  - Visualização de tendências

- [ ] **Exportação de dados**
  - CSV e Excel com histórico completo
  - Gráficos em PDF
  - Relatórios automáticos por email

### Fase 3: Dados e Validação
- [ ] **Validação de dados (Pydantic)**
  - Schema de produto validado
  - Tratamento de tipos de dados
  - Mensagens de erro claras

- [ ] **Análise de preços**
  - Preço mínimo/máximo/médio
  - Detecção de outliers
  - Recomendações de compra


### Roadmap de Implementação

**v1.1** (Próxima):
```
- Banco de dados SQLite
- Histórico de preços
- Validação com Pydantic
```

**v1.2**:
```
- APScheduler para execução automática
- Alertas de mudança de preço
- Logs estruturados
```

**v1.3**:
```
- Dashboard Streamlit básico
- Gráficos de tendências
- Exportação CSV
```

**v2.0**:
```
- PostgreSQL para escala
- API REST (FastAPI)
- Notificações por email/Telegram
- Dashboard avançado
```

## 📝 Licença

Este projeto é fornecido como está para fins educacionais e de portfólio.

## 💡 Aprendizados

Este projeto demonstra conhecimento em:
- **Web Scraping**: Técnicas de extração de dados da web
- **Parsing HTML**: Uso de BeautifulSoup e XPath
- **Programação Python**: Modularização, tratamento de erros
- **APIs HTTP**: Requisições e headers
- **Processamento de Dados**: Limpeza e formatação
- **Estrutura de Projetos**: Organização e boas práticas

## 👤 Autor

Wyvig Israel

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas! Sinta-se livre para:
- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Propor otimizações

---

**Desenvolvido com ❤️ para estudos e portfolio**
