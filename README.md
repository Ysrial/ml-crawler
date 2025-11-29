# ML Crawler 🕷️

Um sistema completo de monitoramento de preços do Mercado Livre Brasil com **scraping automático**, **banco de dados PostgreSQL**, **dashboard interativo** e **agendamento inteligente**.

## 📋 Descrição

ML Crawler é uma plataforma robusta desenvolvida em Python que permite coletar, armazenar e monitorar informações de produtos do Mercado Livre em tempo real. Ideal para análise de preços, pesquisa de mercado, acompanhamento de tendências e identificação de oportunidades de compra.

**Funcionalidades principais:**
- ✅ **Scraping inteligente** com detecção automática de layouts
- ✅ **Parsing robusto de preços** (suporta formatos BR e US)
- ✅ **Banco de dados PostgreSQL** com histórico completo
- ✅ **Dashboard interativo** com visualização em cards
- ✅ **Agendamento automático** via Prefect
- ✅ **Suporte a 22 categorias** de produtos
- ✅ **Atualização incremental** de produtos existentes
- ✅ **Scripts de limpeza** para manutenção automática
- ✅ **Gráficos de tendência** de preços
- ✅ **Detecção de descontos** e economia

## 🚀 Quick Start

### Pré-requisitos

- Python 3.9+
- Docker e Docker Compose
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/Ysrial/ml-crawler.git
cd ml-crawler
```

2. Crie e ative o ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

5. Inicie o banco de dados PostgreSQL:
```bash
docker compose up -d
```

6. Inicialize o banco de dados:
```bash
python3 -c "from src.database_postgres import get_database; get_database().initialize_db()"
```

### Uso

#### 1. Dashboard Interativo (Recomendado)

Visualize produtos e tendências de preços em tempo real:

```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

#### 2. Scraping Manual

Execute coleta de dados para todas as categorias:

```bash
./run_tasks.sh
```

Ou para uma categoria específica:

```bash
python3 -m src.main "https://lista.mercadolivre.com.br/celular"
```

#### 3. Scripts de Manutenção

**Remover produtos desatualizados (>5 dias):**
```bash
python3 scripts/cleanup_old_products.py --dias 5
```

## 📦 Estrutura do Projeto

```
ml-crawler/
├── src/
│   ├── main.py              # Ponto de entrada (scraping manual)
│   ├── scraper.py           # Lógica de scraping e paginação
│   ├── database_postgres.py # Gerenciamento do PostgreSQL
│   ├── models.py            # Modelos de dados (Pydantic)
│   ├── tasks.py             # Agendamento com Prefect
│   ├── config.py            # Configurações e categorias
│   └── utils.py             # Funções utilitárias
├── scripts/
│   └── cleanup_old_products.py    # Remove produtos desatualizados
├── app.py                   # Dashboard Streamlit
├── docker-compose.yml       # Configuração do PostgreSQL
├── requirements.txt         # Dependências do projeto
├── .env.example            # Exemplo de variáveis de ambiente
└── README.md               # Este arquivo
```

## 🔧 Componentes Principais

### Dashboard (`app.py`)
Interface web interativa construída com Streamlit:
- **Visualização em cards** de produtos
- **Gráficos de tendência** de preços (últimos 30 dias)
- **Filtros por categoria** (22 categorias disponíveis)
- **Busca de produtos** por nome
- **Badges de economia** mostrando valor economizado
- **Histórico de preços** expansível por produto

### Scraper (`scraper.py`)
Motor de coleta de dados com múltiplas estratégias:

- **`extract_products(html, limit)`**: Extração inteligente com fallbacks
  - Estratégia A: `.andes-money-amount__fraction` (layout moderno)
  - Estratégia B: `aria-label` com "Agora:"
  - Estratégia C: `.andes-money-amount--cents-superscript`
  - Estratégia D: `.price-tag-fraction` (layout clássico)

- **`scrape_all_pages(base_url, categoria, max_products, max_pages)`**:
  - Coleta até 200 produtos por categoria (4 páginas)
  - Atualização incremental de produtos existentes
  - Detecção automática de produtos duplicados

### Banco de Dados (`database_postgres.py`)
Gerenciamento completo do PostgreSQL:

**Tabelas:**
- `produtos`: Dados atuais dos produtos
- `precos_historico`: Histórico completo de preços
- `coletas`: Logs de execução do scraper

**Principais funções:**
- `adicionar_produto()`: Insere novo produto
- `atualizar_produto()`: Atualiza todos os campos
- `obter_historico_preco()`: Retorna tendências
- `obter_estatisticas_produto()`: Análise completa

### Agendamento (`tasks.py`)
Execução automática via Prefect:
- Coleta a cada 10 minutos (configurável)
- Processamento paralelo de categorias
- Logs estruturados de execução
- Retry automático em caso de falhas

### Utilitários (`utils.py`)

- **`text_to_price(s: str) -> float`**: Parsing inteligente de preços
  - Suporta formato brasileiro: `1.234,56`
  - Suporta formato americano: `1,234.56`
  - Detecta automaticamente separadores decimais
  - Trata casos ambíguos: `249.90` → `249.90` (não `24990`)

## 🎯 Categorias Suportadas

O sistema monitora **22 categorias** de produtos:

**Eletrônicos e Tecnologia:**
- Celulares, Notebooks, Computadores Desktop
- Placas-Mãe, Placas de Vídeo, Processadores
- Memória RAM, Fontes, Coolers, Monitores
- Mouse, Teclados, Headsets, Microfones
- Webcams, Caixas de Som

**Outros:**
- Eletrodomésticos, Roupas, Cosméticos
- Móveis, Produtos de Higiene

## 📊 Estrutura de Dados

### Banco de Dados PostgreSQL

**Tabela `produtos`:**
```sql
id                  SERIAL PRIMARY KEY
nome                TEXT NOT NULL
link                TEXT NOT NULL UNIQUE
categoria           TEXT NOT NULL
produto_id_ml       TEXT (ID do Mercado Livre)
preco_atual         NUMERIC(10, 2)
preco_original      NUMERIC(10, 2)
percentual_desconto NUMERIC(5, 2)
imagem_url          TEXT
primeira_coleta     TIMESTAMP
ultima_atualizacao  TIMESTAMP
```

**Tabela `precos_historico`:**
```sql
id          SERIAL PRIMARY KEY
produto_id  INTEGER (FK para produtos)
preco       NUMERIC(10, 2)
data        TIMESTAMP
```

**Exemplo de dados:**
```json
{
  "id": 1,
  "nome": "Samsung Galaxy A54 5G 128GB",
  "preco_atual": 1499.00,
  "preco_original": 2199.00,
  "percentual_desconto": 31.8,
  "categoria": "celular",
  "imagem_url": "https://http2.mlstatic.com/...",
  "produto_id_ml": "MLB3583764605",
  "link": "https://produto.mercadolivre.com.br/...",
  "primeira_coleta": "2025-11-22T10:30:00",
  "ultima_atualizacao": "2025-11-29T13:00:00"
}
```

## 🛠️ Tecnologias Utilizadas

**Core:**
- **Python 3.9+**: Linguagem principal
- **PostgreSQL**: Banco de dados relacional
- **Docker**: Containerização do banco

**Web Scraping:**
- **Requests**: Requisições HTTP
- **BeautifulSoup4**: Parsing HTML
- **lxml**: Parser XML/HTML de alta performance

**Interface e Visualização:**
- **Streamlit**: Dashboard interativo
- **Plotly**: Gráficos interativos
- **Pandas**: Manipulação de dados

**Agendamento e Orquestração:**
- **Prefect**: Workflow orchestration
- **APScheduler**: Agendamento de tarefas

**Validação e Modelos:**
- **Pydantic**: Validação de dados
- **python-dotenv**: Gerenciamento de variáveis de ambiente

Veja `requirements.txt` para lista completa de dependências.

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

## 📈 Features Implementadas

### ✅ Fase 1: Monitoramento de Preços (Completo)
- [x] **Agendamento automático (Prefect)**
  - Execução a cada 10 minutos (configurável)
  - Histórico de coletas automático
  - Logs estruturados de execução
  - Retry automático em falhas

- [x] **Banco de dados PostgreSQL**
  - Armazenamento de histórico completo de preços
  - Rastreamento de mudanças por produto
  - Schema otimizado: `produtos`, `precos_historico`, `coletas`
  - Connection pooling para performance

- [x] **Monitoramento de mudanças de preço**
  - Detecção automática de variações
  - Comparação com preço anterior
  - Cálculo de variação percentual

### ✅ Fase 2: Análise e Visualização (Completo)
- [x] **Interface gráfica (Streamlit)**
  - Dashboard moderno com cards visuais
  - Gráficos interativos de tendências
  - Filtros por categoria (22 categorias)
  - Busca de produtos por nome
  - Badges de economia mostrando valor economizado

- [x] **Validação de dados (Pydantic)**
  - Schema de produto validado
  - Tratamento robusto de tipos
  - Mensagens de erro claras

- [x] **Análise de preços**
  - Preço mínimo/máximo/médio por produto
  - Histórico de 30 dias
  - Detecção de descontos

### 🚀 Próximas Melhorias

**v2.1** (Curto Prazo):
- [ ] Notificações por email/Telegram quando preço cai
- [ ] Exportação de relatórios em CSV/Excel
- [ ] Alertas personalizados por produto
- [ ] Comparação de preços entre vendedores

**v2.2** (Médio Prazo):
- [ ] API REST (FastAPI) para acesso programático
- [ ] Autenticação e multi-usuário
- [ ] Watchlist personalizada por usuário
- [ ] Recomendações de compra baseadas em ML

**v3.0** (Longo Prazo):
- [ ] Análise de sentimento de reviews
- [ ] Predição de tendências de preço
- [ ] Integração com outros marketplaces
- [ ] App mobile (React Native)

## 📝 Licença

Este projeto é fornecido como está para fins educacionais e de portfólio.

## 💡 Aprendizados e Tecnologias

Este projeto demonstra conhecimento avançado em:

**Web Scraping e Parsing:**
- Técnicas robustas de extração de dados
- Múltiplas estratégias de fallback
- Parsing inteligente de preços (BR/US formats)
- Detecção dinâmica de layouts

**Banco de Dados:**
- PostgreSQL com connection pooling
- Schema design otimizado
- Índices para performance
- Migrations e versionamento

**Arquitetura e Padrões:**
- Separação de responsabilidades (MVC-like)
- Modelos validados com Pydantic
- Configuração centralizada
- Logging estruturado

**Orquestração e Automação:**
- Workflow orchestration com Prefect
- Agendamento inteligente
- Retry policies e error handling
- Task dependencies

**Interface e Visualização:**
- Dashboard interativo com Streamlit
- Gráficos responsivos com Plotly
- UX/UI moderno com cards visuais
- Real-time data updates

**DevOps e Infraestrutura:**
- Docker e Docker Compose
- Variáveis de ambiente (.env)
- Scripts de manutenção automatizados
- Versionamento com Git (branches: main, develop, selenium)

**Boas Práticas:**
- Código modular e reutilizável
- Documentação completa
- Tratamento robusto de erros
- Type hints e validação de dados

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
