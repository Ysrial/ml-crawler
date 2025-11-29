"""
Configuração de categorias e URLs para coleta de dados.
Define as categorias de produtos a serem monitoradas.
"""

import os
from pathlib import Path

# Carregar variáveis do .env
try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).parent.parent
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    print("⚠️ python-dotenv não está instalado. Use: pip install python-dotenv")

# ========== CATEGORIAS DE PRODUTOS ==========
CATEGORIAS = {
    "celular": {
        "url": "https://lista.mercadolivre.com.br/celular",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Eletrônicos e Tecnologia: Smartphones"
    },
    "notebook": {
        "url": "https://lista.mercadolivre.com.br/notebook",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Eletrônicos e Tecnologia: Notebooks"
    },
    "computador-desktop": {
        "url": "https://lista.mercadolivre.com.br/computador-desktop",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Eletrônicos e Tecnologia: Computadores Desktop"
    },
    "eletrodomestico": {
        "url": "https://lista.mercadolivre.com.br/eletrodomestico",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Eletrodomésticos: Linha branca e portáteis"
    },
    "roupa": {
        "url": "https://lista.mercadolivre.com.br/roupa",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Moda e Vestuário: Roupas, calçados e acessórios"
    },
    "cosmetica": {
        "url": "https://lista.mercadolivre.com.br/cosmetica",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Beleza e Cuidados: Cosméticos e perfumes"
    },
    "movel": {
        "url": "https://lista.mercadolivre.com.br/movel",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Casa e Decoração: Móveis e utensílios"
    },
    "higiene": {
        "url": "https://lista.mercadolivre.com.br/higiene",
        "max_paginas": 6,
        "max_produtos_por_pagina": 50,
        "descricao": "Higiene e Limpeza: Bens de consumo"
    }
}

# ========== CAMINHOS E DIRETÓRIOS ==========
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

# Criar diretórios se não existirem
LOG_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# ========== CONFIGURAÇÕES DO SCRAPER ==========
REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ========== CONFIGURAÇÕES DE LOGGING ==========
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / "ml_crawler.log"

# ========== CONFIGURAÇÕES DO PREFECT ==========
# Schedule: Executar a cada 10 minutos
SCHEDULE_CRON = "*/10 * * * *"
SCHEDULE_TIMEZONE = "America/Sao_Paulo"

# ========== CONFIGURAÇÕES DE BANCO DE DADOS ==========
# PostgreSQL em Docker - variáveis de ambiente do .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ml_crawler")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ECHO_SQL = False  # Set True para debug SQL

# ========== LIMITES E TIMEOUTS ==========
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos
BATCH_SIZE = 100  # Inserir produtos em lotes

# ========== CONFIGURAÇÃO DE PROXIES ==========
# Habilitar proxies se Mercado Livre bloquear as requisições
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"

# Lista de proxies (formato: ip:porta ou http://ip:porta)
# Adicione seus proxies aqui ou na variável de ambiente PROXY_LIST
PROXY_LIST = [
    # Exemplo: "http://185.xx.xx.xx:8080",
    # Exemplo: "socks5://185.xx.xx.xx:1080",
]

# Se houver proxies na variável de ambiente, usar delas
if os.getenv("PROXY_LIST"):
    PROXY_LIST = os.getenv("PROXY_LIST").split(",")
    PROXY_LIST = [p.strip() for p in PROXY_LIST if p.strip()]

# Proxy único (se preferir usar apenas um)
SINGLE_PROXY = os.getenv("SINGLE_PROXY", None)
if SINGLE_PROXY:
    USE_PROXY = True

# ========== ESTRATÉGIAS DE BYPASS ==========
# Usar CloudScraper para contornar CloudFlare/WAF
USE_CLOUDSCRAPER = os.getenv("USE_CLOUDSCRAPER", "true").lower() == "true"

# Usar Selenium/Playwright como fallback (mais lento, mas mais efetivo)
USE_HEADLESS_BROWSER = os.getenv("USE_HEADLESS_BROWSER", "false").lower() == "true"
HEADLESS_BROWSER_TYPE = os.getenv("HEADLESS_BROWSER", "selenium")  # selenium ou playwright

# Configurações do Selenium
SELENIUM_TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "10"))           # Timeout de carregamento de página
SELENIUM_IMPLICIT_WAIT = int(os.getenv("SELENIUM_IMPLICIT_WAIT", "5")) # Espera implícita para elementos
SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"  # True = sem UI, False = com janela

# Delays entre requisições (em segundos)
MIN_DELAY = float(os.getenv("MIN_DELAY", "2"))      # Mínimo 2s
MAX_DELAY = float(os.getenv("MAX_DELAY", "8"))      # Máximo 8s
DELAY_BETWEEN_PAGES = float(os.getenv("DELAY_BETWEEN_PAGES", "5"))  # Delay entre páginas

# Número de retries
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_WAIT = float(os.getenv("RETRY_WAIT", "10"))   # Espera inicial (aumenta exponencialmente)

# ========== USER AGENTS ROTATIVO ==========
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

print(f"✅ Configuração carregada")
print(f"   Database: PostgreSQL - {DB_HOST}:{DB_PORT}/{DB_NAME}")
print(f"   Categorias: {len(CATEGORIAS)}")
if USE_PROXY:
    print(f"   Proxies: ATIVADO ({len(PROXY_LIST)} disponíveis)" if PROXY_LIST else "   Proxies: ATIVADO (usar SINGLE_PROXY)")
