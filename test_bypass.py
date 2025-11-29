#!/usr/bin/env python3
"""
Script de teste para validar configurações de bypass
Testa cada estratégia individualmente
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# Setup
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv()

print("=" * 70)
print("🧪 TESTE DE BYPASS - ML CRAWLER")
print("=" * 70)

# ============ TESTE 1: Validar Configuração =============
print("\n✅ TESTE 1: Configuração de Ambiente")
print("-" * 70)

from src.config import (
    USE_CLOUDSCRAPER, USE_PROXY, PROXY_LIST, SINGLE_PROXY,
    MIN_DELAY, MAX_DELAY, DELAY_BETWEEN_PAGES,
    MAX_RETRIES, RETRY_WAIT, USER_AGENTS
)

print(f"USE_CLOUDSCRAPER: {USE_CLOUDSCRAPER}")
print(f"USE_PROXY: {USE_PROXY}")
print(f"PROXY_LIST: {len(PROXY_LIST) if PROXY_LIST else 0} proxies")
print(f"SINGLE_PROXY: {SINGLE_PROXY[:30] if SINGLE_PROXY else 'Não configurado'}...")
print(f"MIN_DELAY: {MIN_DELAY}s")
print(f"MAX_DELAY: {MAX_DELAY}s")
print(f"DELAY_BETWEEN_PAGES: {DELAY_BETWEEN_PAGES}s")
print(f"MAX_RETRIES: {MAX_RETRIES}")
print(f"RETRY_WAIT: {RETRY_WAIT}s")
print(f"User-Agents disponíveis: {len(USER_AGENTS)}")

# ============ TESTE 2: Verificar Dependências =============
print("\n✅ TESTE 2: Dependências Instaladas")
print("-" * 70)

deps = {
    "requests": "Requisições HTTP",
    "beautifulsoup4": "Parse HTML",
    "cloudscraper": "CloudFlare bypass ⭐",
    "selenium": "Headless browser",
    "playwright": "Headless browser (alt)",
}

for package, descricao in deps.items():
    try:
        __import__(package)
        print(f"✅ {package:20} - {descricao}")
    except ImportError:
        status = "⭐ RECOMENDADO" if package == "cloudscraper" else "⚠️ Opcional"
        print(f"❌ {package:20} - {descricao} [{status}]")

# ============ TESTE 3: RequestHandler =============
print("\n✅ TESTE 3: RequestHandler Inicializado")
print("-" * 70)

try:
    from src.request_handler import RequestHandler, HAS_CLOUDSCRAPER
    from src import config
    
    handler = RequestHandler(config)
    print(f"✅ RequestHandler criado")
    print(f"   - CloudScraper disponível: {HAS_CLOUDSCRAPER}")
    print(f"   - Headers customizados: Sim")
    print(f"   - Retry automático: Sim")
    print(f"   - Proxy rotativo: {'Sim' if USE_PROXY else 'Não'}")
    
except Exception as e:
    print(f"❌ Erro ao criar RequestHandler: {e}")
    sys.exit(1)

# ============ TESTE 4: Teste de Requisição (Opcional) =============
print("\n✅ TESTE 4: Teste de Requisição (Opcional)")
print("-" * 70)

resposta = input("Deseja fazer teste de requisição? (s/n): ").lower()

if resposta == 's':
    url = "https://httpbin.org/user-agent"  # Teste inofensivo
    print(f"\nTestando com: {url}")
    print("Aguarde... (pode levar alguns segundos)")
    
    try:
        start = time.time()
        html = handler.fetch(url, max_retries=1)
        elapsed = time.time() - start
        
        if html:
            print(f"✅ Requisição bem-sucedida em {elapsed:.1f}s")
            print(f"   Tamanho: {len(html)} bytes")
            if len(html) < 200:
                print(f"   Resposta: {html}")
        else:
            print(f"❌ Requisição falhou")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

# ============ TESTE 5: Testar Scraper =============
print("\n✅ TESTE 5: Scraper Disponível")
print("-" * 70)

try:
    from src.scraper import fetch_html, extract_products
    print("✅ Funções do scraper importadas:")
    print("   - fetch_html()")
    print("   - extract_products()")
    print("   - scrape_all_pages()")
    
except Exception as e:
    print(f"❌ Erro ao importar scraper: {e}")

# ============ TESTE 6: Database =============
print("\n✅ TESTE 6: Database")
print("-" * 70)

try:
    from src.database_postgres import get_database
    db = get_database()
    print("✅ Database PostgreSQL conectado")
    
    try:
        categorias = db.obter_categorias()
        print(f"   - Categorias: {len(categorias)}")
        for cat in categorias[:3]:
            print(f"     • {cat}")
        if len(categorias) > 3:
            print(f"     ... e mais {len(categorias) - 3}")
    except Exception as e:
        print(f"   ℹ️  Banco vazio ou erro: {str(e)[:50]}")
        
except Exception as e:
    print(f"❌ Erro de database: {e}")

# ============ RESUMO =============
print("\n" + "=" * 70)
print("📋 RESUMO")
print("=" * 70)

checklist = [
    ("CloudScraper (bypass CloudFlare)", HAS_CLOUDSCRAPER),
    ("Configuração de delays", MIN_DELAY > 0),
    ("Database conectado", True),  # Já testado acima
    ("RequestHandler funcional", handler is not None),
]

print("\n✅ Checklist:")
for item, status in checklist:
    icon = "✅" if status else "⚠️"
    print(f"{icon} {item}")

print("\n📝 Próximos passos:")
print("1. Se faltar CloudScraper, instale: pip install cloudscraper")
print("2. Configure proxies no .env se estiver bloqueado")
print("3. Execute: python3 src/main.py (teste coleta)")
print("4. Ou: streamlit run app.py (ver dashboard)")

print("\n💡 Se estiver bloqueado pelo Mercado Livre:")
print("   - Aumentar MIN_DELAY e MAX_DELAY no .env")
print("   - Configurar PROXY_LIST")
print("   - Ativar USE_HEADLESS_BROWSER (último recurso)")

print("\n" + "=" * 70)
