import requests
from bs4 import BeautifulSoup
from .utils import text_to_price
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_html(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"[HTTP] {resp.status_code} - {url}")
    return resp.text


def detect_selector(html: str):
    if "ui-search-layout__item" in html:
        return "li.ui-search-layout__item, div.ui-search-result__wrapper"
    if "poly-card--grid" in html:
        return "div.poly-card.poly-card--grid.poly-card--large"
    return None


def extract_products(html: str, limit: int = 10):
    soup = BeautifulSoup(html, "lxml")
    selector = detect_selector(html)

    if not selector:
        print("❌ Nenhum seletor compatível encontrado.")
        return []

    items = soup.select(selector)
    print(f"🧩 {len(items)} itens encontrados (usando '{selector}')")

    produtos = []
    for item in items:
        if len(produtos) >= limit:
            break

        title_tag = item.select_one("a.poly-component__title, h3 a, h2 a, a.ui-search-link")
        preco_tag = item.select_one("span.andes-money-amount__fraction, span.price-tag-fraction")

        nome = title_tag.get_text(strip=True) if title_tag else None
        preco = text_to_price(preco_tag.get_text(strip=True)) if preco_tag else None
        link = title_tag.get("href") if title_tag else None

        if nome and preco and link:
            produtos.append({"nome": nome, "preco": preco, "link": link})

    return produtos


def add_pagination_to_url(url: str, page: int) -> str:
    """Adiciona ou atualiza o parâmetro de paginação na URL do Mercado Livre."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Remove chaves vazias do dicionário
    params = {k: v[0] if v else '' for k, v in params.items()}
    
    # Define o número da página (Mercado Livre usa _Paging=page_number)
    params['_Paging'] = str(page)
    
    new_query = urlencode(params)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    
    return new_url


def scrape_all_pages(base_url: str, max_products: int = None, max_pages: int = 10):
    """
    Realiza scraping de múltiplas páginas do Mercado Livre.
    
    Args:
        base_url: URL da busca no Mercado Livre
        max_products: Número máximo de produtos a extrair (None = ilimitado)
        max_pages: Número máximo de páginas a fazer scraping
    
    Returns:
        Lista de produtos extraídos de todas as páginas
    """
    todos_produtos = []
    
    for page in range(1, max_pages + 1):
        url_paginada = add_pagination_to_url(base_url, page)
        print(f"\n📄 Página {page}...")
        
        try:
            html = fetch_html(url_paginada)
            produtos_pagina = extract_products(html)
            
            if not produtos_pagina:
                print(f"⚠️  Nenhum produto encontrado na página {page}. Encerrando paginação.")
                break
            
            todos_produtos.extend(produtos_pagina)
            print(f"✅ {len(produtos_pagina)} produtos adicionados (total: {len(todos_produtos)})")
            
            # Para se atingiu o limite de produtos
            if max_products and len(todos_produtos) >= max_products:
                todos_produtos = todos_produtos[:max_products]
                print(f"📊 Limite de {max_products} produtos atingido.")
                break
                
        except Exception as e:
            print(f"❌ Erro ao fazer scraping da página {page}: {e}")
            break
    
    return todos_produtos
