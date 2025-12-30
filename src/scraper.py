import requests
from bs4 import BeautifulSoup
from .utils import text_to_price
from .models import Produto
from .database_postgres import get_database
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
import time
from .config import DELAY_BETWEEN_REQUESTS

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


def extract_ml_id(link: str):
    pattern = r'\b(MLB[A-Z]*-?\d{5,})\b'
    match = re.search(pattern, link, re.IGNORECASE)

    if match:
        return match.group(1).replace("-", "")

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

    items = soup.select("li.ui-search-layout__item, div.ui-search-result, div.poly-card")

    produtos = []
    for item in items:
        if len(produtos) >= limit:
            break

        title_tag = item.select_one("a.ui-search-link, a.poly-component__title, h3 a, h2 a, a.ui-search-link")
        nome = title_tag.get_text(strip=True) if title_tag else None
        link = title_tag.get("href") if title_tag else None

        imagem_tag = item.select_one("img.ui-search-result-image__element, img")
        imagem_url = None
        if imagem_tag:
            imagem_url = imagem_tag.get("data-src") or imagem_tag.get("src")

        preco = None
        preco_original = None
        percentual_desconto = None

        andes_fractions = item.select(".andes-money-amount__fraction")
        if andes_fractions:
            try:
                if len(andes_fractions) >= 2:
                    preco_original = text_to_price(andes_fractions[0].get_text(strip=True))
                    preco = text_to_price(andes_fractions[1].get_text(strip=True))
                else:
                    preco = text_to_price(andes_fractions[0].get_text(strip=True))
            except Exception as e:
                print(f"debug: erro ao parsear andes_fractions: {e}")

        if preco is None:
            agora_tag = item.select_one('[aria-label^="Agora:"], span[aria-label^="Agora:"], .andes-money-amount[aria-label^="Agora:"]')
            if agora_tag:
                aria = agora_tag.get("aria-label") or agora_tag.get_text()
                aria_clean = re.sub(r'(?i)\bAgora:?\b', '', aria).replace('reais', '').strip()
                try:
                    preco = text_to_price(aria_clean)
                except Exception as e:
                    print(f"debug: falha ao parsear aria 'Agora': {e}")

        if preco is None:
            inteiro_tag = item.select_one(".andes-money-amount__unit, .andes-money-amount__main-value")
            cents_tag = item.select_one(".andes-money-amount--cents-superscript, .andes-money-amount__fraction--cents")
            if inteiro_tag and cents_tag:
                combined = f"{inteiro_tag.get_text(strip=True)},{cents_tag.get_text(strip=True)}"
                try:
                    preco = text_to_price(combined)
                except Exception as e:
                    print(f"debug: falha ao parsear inteiro+cents: {e}")

        if preco is None:
            price_tag_frac = item.select_one(".price-tag-fraction")
            if price_tag_frac:
                try:
                    preco = text_to_price(price_tag_frac.get_text(strip=True))
                except Exception as e:
                    print(f"debug: falha ao parsear price-tag-fraction: {e}")

        if preco_original is None:
            orig_tag = item.select_one(".price-tag-strike .price-tag-fraction, .price-tag__subprice .price-tag-fraction, .andes-money-amount__fraction.price-original, .andes-money-amount--original .andes-money-amount__fraction")
            if orig_tag:
                try:
                    preco_original = text_to_price(orig_tag.get_text(strip=True))
                except Exception as e:
                    print(f"debug: falha ao parsear preco_original: {e}")

        if preco_original is None and andes_fractions and len(andes_fractions) >= 2:
            try:
                preco_original = text_to_price(andes_fractions[0].get_text(strip=True))
                if preco is None:
                    preco = text_to_price(andes_fractions[1].get_text(strip=True))
            except Exception as e:
                print(f"debug: erro ao recuperar preco_original de andes_fractions: {e}")

        if preco_original and preco and preco_original > preco:
            try:
                percentual_desconto = round(((preco_original - preco) / preco_original) * 100, 1)
            except Exception as e:
                print(f"debug: erro ao calcular desconto: {e}")
                percentual_desconto = None

        produto_id_ml = item.get("data-id") or (extract_ml_id(link) if link else None)

        if nome and preco and link:
            produtos.append({
                "nome": nome,
                "preco": preco,
                "preco_original": preco_original,
                "percentual_desconto": percentual_desconto,
                "imagem_url": imagem_url,
                "link": link,
                "produto_id_ml": produto_id_ml
            })
        else:
            print(f"debug: item descartado (nome={bool(nome)}, preco={bool(preco)}, link={bool(link)})")

    return produtos

def add_pagination_to_url(url: str, page: int) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    
    params = {k: v[0] if v else '' for k, v in params.items()}
    
    params['_Paging'] = str(page)
    
    new_query = urlencode(params)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    
    return new_url


def scrape_all_pages(base_url: str, categoria: str, max_products: int = None, max_pages: int = 10):
    db = get_database()
    
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
                
                for prod_data in produtos_pagina:
                    total_produtos += 1
                    
                    if prod_data["produto_id_ml"]:
                        existente = db.obter_produto_por_id_ml(prod_data["produto_id_ml"])
                    else:
                        existente = db.obter_produto_por_link(prod_data["link"])
                    
                    if existente:
                        db.atualizar_produto(
                            existente["id"], 
                            prod_data["preco"],
                            preco_original=prod_data.get("preco_original"),
                            percentual_desconto=prod_data.get("percentual_desconto"),
                            imagem_url=prod_data.get("imagem_url")
                        )
                        total_atualizados += 1
                    else:
                        produto = Produto(
                            nome=prod_data["nome"],
                            preco=prod_data["preco"],
                            preco_original=prod_data.get("preco_original"),
                            percentual_desconto=prod_data.get("percentual_desconto"),
                            imagem_url=prod_data.get("imagem_url"),
                            link=prod_data["link"],
                            categoria=categoria,
                            produto_id_ml=prod_data.get("produto_id_ml")
                        )
                        db.adicionar_produto(produto)
                        total_novos += 1
                    
                    if max_products and total_produtos >= max_products:
                        print(f"📊 Limite de {max_products} produtos atingido.")
                        break
                
                print(f"✅ {len(produtos_pagina)} produtos processados (novo: {total_novos}, atualizado: {total_atualizados})")
                
                if page < max_pages:
                    print(f"⏳ Aguardando {DELAY_BETWEEN_REQUESTS} segundos antes da próxima página...")
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                
                if max_products and total_produtos >= max_products:
                    break
                    
            except Exception as e:
                print(f"❌ Erro ao fazer scraping da página {page}: {e}")
                break
        
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
