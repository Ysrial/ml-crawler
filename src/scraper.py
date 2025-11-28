import requests
from bs4 import BeautifulSoup
from .utils import text_to_price
from .models import Produto
from .database_postgres import get_database
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus
import re
import time

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

# ============================================================
# 🔥 EXTRAI UM PRODUTO DA API E CONVERTE PARA O MESMO FORMATO DO HTML
# ============================================================
def extract_product_from_api_item(item):
    """
    Converte o item da API do Mercado Livre para o mesmo dicionário
    usado na função extract_products() do HTML.
    """

    nome = item.get("title")
    preco = item.get("price")
    link = item.get("permalink")
    produto_id_ml = item.get("id")

    thumbnail = item.get("thumbnail")
    thumbnail = thumbnail.replace("http://", "https://") if thumbnail else None

    # PREÇO ORIGINAL / DESCONTO
    preco_original = None
    percentual_desconto = None

    if "original_price" in item and item["original_price"]:
        preco_original = float(item["original_price"])
        if preco_original > preco:
            percentual_desconto = round(((preco_original - preco) / preco_original) * 100, 1)

    return {
        "nome": nome,
        "preco": preco,
        "preco_original": preco_original,
        "percentual_desconto": percentual_desconto,
        "imagem_url": thumbnail,
        "link": link,
        "produto_id_ml": produto_id_ml
    }


# ============================================================
# 🔥 NOVO SCRAPER USANDO A API (SEM MEXER NO HTML)
# ============================================================

# --- helper: busca produtos via API com headers, timeout e retries ---
def get_products_from_api(query: str, limit: int = 50, offset: int = 0, retries: int = 2, backoff: float = 0.5):
    """
    Consulta a API pública do Mercado Libre e retorna a lista 'results'.
    query: string de busca (ex: 'celular', 'iphone 12')
    """
    base_url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": query,
        "limit": limit,
        "offset": offset
    }
    headers = {
        "User-Agent": HEADERS.get("User-Agent", "ml-crawler/1.0"),
        "Accept": "application/json"
    }

    for attempt in range(1, retries + 2):
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get("results", []), data
            else:
                print(f"⚠️ API HTTP {r.status_code} — tentativa {attempt}: {r.text[:200]}")
        except Exception as e:
            print(f"⚠️ Erro na requisição API (tentativa {attempt}): {e}")

        if attempt <= retries:
            time.sleep(backoff * attempt)

    # se falhou todas as tentativas
    return [], None


# --- substitua por esta função no seu scraper.py ---
def scrape_all_pages_api(query: str, categoria: str, max_products: int = None, max_pages: int = 10):
    """
    Faz scraping via API do Mercado Libre, com paginação e salvando no banco.
    - query: texto de busca (ex: 'celular', 'iphone 12')
    - categoria: nome lógico usado para persistir a coleta
    - max_products: limite opcional de produtos (None = ilimitado)
    - max_pages: limite de páginas (50 itens por página da API)
    """
    db = get_database()
    coleta_id = db.iniciar_coleta(categoria)
    total_novos = 0
    total_atualizados = 0
    total_produtos = 0

    try:
        print("\n🚀 Iniciando scraping via API do Mercado Livre...")
        # normaliza query: se vier com '-' ou '_' transforma em espaços
        query_text = str(query).replace("-", " ").replace("_", " ").strip()

        for page in range(max_pages):
            offset = page * 50
            print(f"\n📄 Página {page+1} (offset {offset}) — query: '{query_text}'")

            resultados, raw = get_products_from_api(query_text, limit=50, offset=offset)
            if raw is None:
                print("❌ Falha ao consultar API (nenhuma resposta válida).")
            count = len(resultados)
            print(f"🔎 {count} produtos retornados pela API (página {page+1})")

            # se API não trouxe resultados já no primeiro page, vamos fazer fallback para o HTML
            if count == 0 and page == 0:
                print("⚠️ API retornou 0 resultados na primeira página — executando fallback para HTML.")
                # construir URL de busca padrão para o HTML scraper usando a categoria
                html_search_url = f"https://lista.mercadolivre.com.br/{categoria}"
                # chama o HTML scraper original (mantém testes intactos)
                fallback_result = scrape_all_pages(html_search_url, categoria, max_products=max_products, max_pages=max_pages)
                # garantir finalizar coleta atual (a função scrape_all_pages já finaliza a própria coleta no DB)
                db.finalizar_coleta(coleta_id, 0, 0, 0, True)
                return fallback_result

            if not resultados:
                print("⚠️ Sem resultados nesta página — parando paginação.")
                break

            for p in resultados:
                total_produtos += 1

                preco = p.get("price")
                preco_original = p.get("original_price")
                link = p.get("permalink")
                nome = p.get("title")
                imagem = p.get("thumbnail")
                produto_id_ml = p.get("id")

                percentual = None
                if preco_original and preco and preco_original > preco:
                    percentual = round(((preco_original - preco) / preco_original) * 100, 1)

                # salvar / atualizar no banco
                existente = None
                if produto_id_ml:
                    existente = db.obter_produto_por_id_ml(produto_id_ml)
                else:
                    existente = db.obter_produto_por_link(link) if link else None

                if existente:
                    db.atualizar_produto_completo(
                        existente["id"],
                        preco=preco,
                        preco_original=preco_original,
                        percentual_desconto=percentual,
                        imagem_url=imagem
                    )
                    total_atualizados += 1
                else:
                    produto = Produto(
                        nome=nome,
                        preco=preco,
                        preco_original=preco_original,
                        percentual_desconto=percentual,
                        imagem_url=imagem,
                        link=link,
                        categoria=categoria,
                        produto_id_ml=produto_id_ml
                    )
                    db.adicionar_produto(produto)
                    total_novos += 1

                # respeitar limite de produtos
                if max_products and total_produtos >= max_products:
                    print(f"📊 Limite de {max_products} produtos atingido.")
                    break

            if max_products and total_produtos >= max_products:
                break

            # pequeno delay para não pisar na API (e evitar rate-limits)
            time.sleep(0.2)

        db.finalizar_coleta(coleta_id, total_produtos, total_novos, total_atualizados, True)

        print("\n✅ Coleta via API finalizada com sucesso!")
        return {
            "status": "sucesso",
            "total_produtos": total_produtos,
            "total_novos": total_novos,
            "total_atualizados": total_atualizados
        }

    except Exception as e:
        db.finalizar_coleta(coleta_id, total_produtos, total_novos, total_atualizados, False, str(e))
        print(f"❌ Erro geral na coleta via API: {e}")
        return {
            "status": "erro",
            "erro": str(e),
            "total_produtos": total_produtos,
            "total_novos": total_novos,
            "total_atualizados": total_atualizados
        }

def extract_price_from_product_page(link: str):
    try:
        html = fetch_html(link)
        soup = BeautifulSoup(html, "lxml")

        preco = None
        preco_original = None

        # ==============================
        # 1) PREÇO ATUAL (3 formas)
        # ==============================

        # Forma A — padrão (meta tag)
        meta_price = soup.select_one('meta[itemprop="price"]')
        if meta_price:
            try:
                preco = float(meta_price["content"])
            except:
                pass

        # Forma B — layout novo (span fraction + cents)
        if preco is None:
            price_container = soup.select_one(
                ".ui-pdp-price__second-line .andes-money-amount"
            )
            if price_container:
                frac = price_container.select_one(".andes-money-amount__fraction")
                cents = price_container.select_one(".andes-money-amount__cents")
                if frac:
                    f = frac.get_text(strip=True)
                    c = cents.get_text(strip=True) if cents else "00"
                    try:
                        preco = float(f"{f}.{c}")
                    except:
                        pass

        # Forma C — fallback para QUALQUER preço visível
        if preco is None:
            number = soup.select_one("[itemprop=price]")
            if number and number.get("content"):
                try:
                    preco = float(number["content"])
                except:
                    pass

        # ==============================
        # 2) PREÇO ORIGINAL (antes do desconto)
        # ==============================
        orig = soup.select_one("s.andes-money-amount--previous")
        if orig:
            frac = orig.select_one(".andes-money-amount__fraction")
            cents = orig.select_one(".andes-money-amount__cents")

            if frac:
                f = frac.get_text(strip=True)
                c = cents.get_text(strip=True) if cents else "00"
                try:
                    preco_original = float(f"{f}.{c}")
                except:
                    pass

        return preco, preco_original

    except Exception as e:
        print(f"❌ Erro ao extrair preço da página interna: {e}")
        return None, None

def extract_products(html: str, limit: int = 10):
    print("\n======================")
    print("🔍 INICIANDO extract_products")
    print("======================")

    soup = BeautifulSoup(html, "lxml")

    # Mostrar início do HTML (para debug de layout)
    print("\n[DEBUG] HTML inicial (500 chars):")
    print(html[:500])
    print("\n------------------------------------\n")

    # Testar todos seletores conhecidos
    SELECTORES_TESTE = {
        "layout_antigo": "li.ui-search-layout__item",
        "layout_novo": "div.ui-search-result",
        "wrapper": "div.ui-search-result__wrapper",
        "poly-card": "div.poly-card",
        "poly-large": "div.poly-card--large",
        "grid": "a.ui-search-link"
    }

    for nome, seletor in SELECTORES_TESTE.items():
        encontrados = soup.select(seletor)
        print(f"[DEBUG] seletor '{nome}' = {len(encontrados)} itens")

    # Seletor final
    items = soup.select(
        "li.ui-search-layout__item, "
        "div.ui-search-result__wrapper, "
        "div.ui-search-result"
    )

    print(f"[ML DEBUG] Cards encontrados com seletor novo: {len(items)}")

    if len(items) == 0:
        print("❌ NENHUM item encontrado — layout mudou!")
        return []

    produtos = []

    for index, item in enumerate(items):
        if len(produtos) >= limit:
            break

        print("\n------------------------------")
        print(f"📌 ITEM {index+1}")
        print("------------------------------")

        # Log do HTML do item
        print("[DEBUG] HTML do item (300 chars):")
        print(str(item)[:300])
        print("--------------------------------")

        # ---------------- TITLE / LINK ----------------
        title_tag = item.select_one("a.ui-search-link, a.poly-component__title, h3 a, h2 a")
        nome = title_tag.get_text(strip=True) if title_tag else None
        link = title_tag.get("href") if title_tag else None

        print(f"📝 Nome: {nome}")
        print(f"🔗 Link: {link}")

        # ---------------- IMAGE ----------------
        imagem_tag = item.select_one("img.ui-search-result-image__element, img")
        imagem_url = None
        if imagem_tag:
            imagem_url = imagem_tag.get("data-src") or imagem_tag.get("src")
        print(f"🖼️ Imagem: {imagem_url}")

        preco = None
        preco_original = None

        # ============================================================
        # 1) META PRICE
        # ============================================================
        meta_price = item.select_one('meta[itemprop="price"]')
        if meta_price:
            try:
                preco = float(meta_price["content"])
                print(f"💰 Preço META encontrado: {preco}")
            except:
                print("⚠️ Falha ao converter META price")

        # ============================================================
        # 2) PREÇO ORIGINAL
        # ============================================================
        orig_tag = item.select_one(
            ".andes-money-amount--previous, "
            ".price-tag-strike .price-tag-fraction, "
            ".andes-money-amount--original .andes-money-amount__fraction"
        )
        if orig_tag:
            try:
                preco_original = text_to_price(orig_tag.get_text(strip=True))
                print(f"🏷️ Preço ORIGINAL encontrado: {preco_original}")
            except:
                print("⚠️ Falha ao converter preço original")

        # ============================================================
        # 3) PREÇO ATUAL
        # ============================================================
        preco_atual_tag = item.select_one(
            ".andes-money-amount__fraction, "
            ".ui-search-price__second-line .andes-money-amount__fraction"
        )
        if preco_atual_tag and preco is None:
            try:
                preco = text_to_price(preco_atual_tag.get_text(strip=True))
                print(f"💵 Preço ATUAL encontrado: {preco}")
            except:
                print("⚠️ Falha ao converter preço atual")

        # ============================================================
        # FALLBACK FRACTIONS
        # ============================================================
        if preco is None:
            fractions = item.select(".andes-money-amount__fraction")
            print(f"[DEBUG] Fractions encontradas: {len(fractions)}")

            if len(fractions) >= 1:
                try:
                    valores = [text_to_price(x.get_text(strip=True)) for x in fractions]
                    print(f"[DEBUG] valores fractions: {valores}")

                    if len(valores) >= 2 and valores[0] != valores[1]:
                        maior = max(valores)
                        menor = min(valores)

                        preco_original = maior
                        preco = menor

                        print(f"🔥 FALLBACK → original={maior}, atual={menor}")
                    else:
                        preco = valores[0]
                        print(f"🔥 FALLBACK → preco único={preco}")

                except Exception as e:
                    print(f"⚠️ Erro ao processar fractions: {e}")

        # ============================================================
        # FALLBACK FINAL
        # ============================================================
        if preco is None:
            frac = item.select_one(".price-tag-fraction")
            if frac:
                preco = text_to_price(frac.get_text(strip=True))
                print(f"🔥 FALLBACK FINAL → preco={preco}")

        # ============================================================
        # VERY IMPORTANT: BUSCAR NA PÁGINA INTERNA!
        # ============================================================
        if (preco is None or preco_original is None) and link:
            print("➡️ Indo buscar preços na página interna...")
            preco2, preco_original2 = extract_price_from_product_page(link)
            print(f"🔙 Page internal → preco={preco2}, original={preco_original2}")

            if preco is None: preco = preco2
            if preco_original is None: preco_original = preco_original2

        # ============================================================
        # DESCONTO
        # ============================================================
        percentual_desconto = None
        if preco_original and preco and preco_original > preco:
            percentual_desconto = round(((preco_original - preco) / preco_original) * 100, 1)
            print(f"💸 Desconto calculado: {percentual_desconto}%")

        # ============================================================
        # ID ML
        # ============================================================
        produto_id_ml = item.get("data-id") or (extract_ml_id(link) if link else None)
        print(f"🆔 ID ML: {produto_id_ml}")

        # ============================================================
        # VALIDAÇÃO
        # ============================================================
        if not nome: print("❌ Sem nome — descartado")
        if not preco: print("❌ Sem preço — descartado")
        if not link: print("❌ Sem link — descartado")

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
            print("✅ Produto adicionado!")

    print("\n======================")
    print(f"🏁 FINAL — {len(produtos)} produtos extraídos")
    print("======================\n")

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
                        db.atualizar_produto_completo(
                            existente["id"],
                            preco=prod_data["preco"],
                            preco_original=prod_data.get("preco_original"),
                            percentual_desconto=prod_data.get("percentual_desconto"),
                            imagem_url=prod_data.get("imagem_url")
                        )
                    else:
                        # Criar novo
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
