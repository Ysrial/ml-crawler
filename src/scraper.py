import requests
from bs4 import BeautifulSoup
from .utils import text_to_price
from .models import Produto
from .database_postgres import get_database
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re

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


# 🔥 Função universal para extrair ID MLB, MLBU, MLB- etc.
def extract_ml_id(link: str):
    # cobre: MLB123, MLB-123, MLBU-123, etc
    pattern = r'\b(MLB[A-Z]*-?\d{5,})\b'
    match = re.search(pattern, link, re.IGNORECASE)

    if match:
        return match.group(1).replace("-", "")

    # tenta pegar nos parâmetros da URL
    parsed = urlparse(link)
    params = parse_qs(parsed.query)

    for values in params.values():
        for value in values:
            m2 = re.search(pattern, value, re.IGNORECASE)
            if m2:
                return m2.group(1).replace("-", "")

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

        # 👇 substituí aqui
        produto_id_ml = item.get("data-id") or extract_ml_id(link)

        if nome and preco and link:
            produtos.append({
                "nome": nome,
                "preco": preco,
                "link": link,
                "produto_id_ml": produto_id_ml
            })

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


def scrape_all_pages(base_url: str, categoria: str, max_products: int = None, max_pages: int = 10):
    """
    Realiza scraping de múltiplas páginas do Mercado Livre e salva no banco de dados.
    
    Args:
        base_url: URL da busca no Mercado Livre
        categoria: Nome da categoria (ex: 'celulares', 'notebooks')
        max_products: Número máximo de produtos a extrair (None = ilimitado)
        max_pages: Número máximo de páginas a fazer scraping
    
    Returns:
        Dicionário com estatísticas da coleta
    """
    db = get_database()
    
    # Iniciar coleta
    coleta_id = db.iniciar_coleta(categoria)
    total_novos = 0
    total_atualizados = 0
    total_produtos = 0
    
    try:
        for page in range(1, max_pages + 1):
            url_paginada = add_pagination_to_url(base_url, page)
            print(f"\n📄 Página {page}...")
            
            try:
                html = fetch_html(url_paginada)
                produtos_pagina = extract_products(html, limit=50)
                
                if not produtos_pagina:
                    print(f"⚠️  Nenhum produto encontrado na página {page}. Encerrando paginação.")
                    break
                
                # Salvar cada produto no banco
                for prod_data in produtos_pagina:
                    total_produtos += 1
                    
                    # Verificar se já existe
                    if prod_data["produto_id_ml"]:
                        existente = db.obter_produto_por_id_ml(prod_data["produto_id_ml"])
                    else:
                        existente = db.obter_produto_por_link(prod_data["link"])
                    
                    if existente:
                        # Atualizar preço
                        db.atualizar_preco(existente["id"], prod_data["preco"])
                        total_atualizados += 1
                    else:
                        # Criar novo
                        produto = Produto(
                            nome=prod_data["nome"],
                            preco=prod_data["preco"],
                            link=prod_data["link"],
                            categoria=categoria,
                            produto_id_ml=prod_data.get("produto_id_ml")
                        )
                        db.adicionar_produto(produto)
                        total_novos += 1
                    
                    # Para se atingiu o limite
                    if max_products and total_produtos >= max_products:
                        print(f"📊 Limite de {max_products} produtos atingido.")
                        break
                
                print(f"✅ {len(produtos_pagina)} produtos processados (novo: {total_novos}, atualizado: {total_atualizados})")
                
                if max_products and total_produtos >= max_products:
                    break
                    
            except Exception as e:
                print(f"❌ Erro ao fazer scraping da página {page}: {e}")
                break
        
        # Finalizar coleta com sucesso
        db.finalizar_coleta(coleta_id, total_produtos, total_novos, total_atualizados, True)
        
        return {
            "coleta_id": coleta_id,
            "categoria": categoria,
            "total_produtos": total_produtos,
            "total_novos": total_novos,
            "total_atualizados": total_atualizados,
            "status": "sucesso"
        }
        
    except Exception as e:
        db.finalizar_coleta(coleta_id, total_produtos, total_novos, total_atualizados, False, str(e))
        print(f"❌ Erro geral na coleta: {e}")
        return {
            "coleta_id": coleta_id,
            "categoria": categoria,
            "status": "erro",
            "erro": str(e)
        }
