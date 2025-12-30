import os
from pathlib import Path

CATEGORIAS = {
    "celular": {
        "url": "https://lista.mercadolivre.com.br/celular",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Smartphones"
    },
    "notebook": {
        "url": "https://lista.mercadolivre.com.br/notebook",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Notebooks"
    },
    "computador-desktop": {
        "url": "https://lista.mercadolivre.com.br/computador-desktop",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Computadores Desktop"
    },
    "eletrodomestico": {
        "url": "https://lista.mercadolivre.com.br/eletrodomestico",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrodomésticos: Linha branca e portáteis"
    },
    "roupa": {
        "url": "https://lista.mercadolivre.com.br/roupa",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Moda e Vestuário: Roupas, calçados e acessórios"
    },
    "cosmetica": {
        "url": "https://lista.mercadolivre.com.br/cosmetica",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Beleza e Cuidados: Cosméticos e perfumes"
    },
    "movel": {
        "url": "https://lista.mercadolivre.com.br/movel",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Casa e Decoração: Móveis e utensílios"
    },
    "higiene": {
        "url": "https://lista.mercadolivre.com.br/higiene",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Higiene e Limpeza: Bens de consumo"
    },
    "eletronicos": {
        "url": "https://lista.mercadolivre.com.br/eletronicos",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Eletrônicos e tecnologia"
    },
    "placa-mae": {
        "url": "https://lista.mercadolivre.com.br/placa-mae",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Placa Mãe"
    },
    "placa-de-video": {
        "url": "https://lista.mercadolivre.com.br/placa-de-video",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Placa de Vídeo"
    },
    "processador": {
        "url": "https://lista.mercadolivre.com.br/processador",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Processador"
    },
    "memoria-ram": {
        "url": "https://lista.mercadolivre.com.br/memoria-ram",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Memória RAM"
    },
    "fonte": {
        "url": "https://lista.mercadolivre.com.br/fonte",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Fonte"
    },
    "cooler": {
        "url": "https://lista.mercadolivre.com.br/cooler",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Cooler"
    },
    "monitor": {
        "url": "https://lista.mercadolivre.com.br/monitor",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Monitor"
    },
    "mouse": {
        "url": "https://lista.mercadolivre.com.br/mouse",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Mouse"
    },
    "teclado": {
        "url": "https://lista.mercadolivre.com.br/teclado",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Teclado"
    },
    "headset": {
        "url": "https://lista.mercadolivre.com.br/headset",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Headset"
    },
    "microfone": {
        "url": "https://lista.mercadolivre.com.br/microfone",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Microfone"
    },
    "webcam": {
        "url": "https://lista.mercadolivre.com.br/webcam",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Webcam"
    },
    "caixa-de-som": {
        "url": "https://lista.mercadolivre.com.br/caixa-de-som",
        "max_paginas": 4,
        "max_produtos_por_pagina": 200,
        "descricao": "Eletrônicos e Tecnologia: Caixa de Som"
    },
}

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

LOG_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DELAY_BETWEEN_REQUESTS = 5
DELAY_BETWEEN_CATEGORIES = 10

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / "ml_crawler.log"

SCHEDULE_CRON = "*/10 * * * *"
SCHEDULE_TIMEZONE = "America/Sao_Paulo"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ml_crawler")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ECHO_SQL = False

MAX_RETRIES = 3
RETRY_DELAY = 5
BATCH_SIZE = 100

print(f"✅ Configuração carregada")
print(f"   Database: PostgreSQL - {DB_HOST}:{DB_PORT}/{DB_NAME}")
print(f"   Categorias: {len(CATEGORIAS)}")
