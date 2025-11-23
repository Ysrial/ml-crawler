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

    # seletor universal atualizado (li e div)
    items = soup.select("li.ui-search-layout__item, div.ui-search-result, div.poly-card")
    print(f"🧩 {len(items)} itens encontrados")

    produtos = []
    for item in items:
        if len(produtos) >= limit:
            break

        # --- TITLE / LINK ---
        title_tag = item.select_one("a.ui-search-link, a.poly-component__title, h3 a, h2 a, a.ui-search-link")
        nome = title_tag.get_text(strip=True) if title_tag else None
        link = title_tag.get("href") if title_tag else None

        # --- IMAGE ---
        imagem_tag = item.select_one("img.ui-search-result-image__element, img")
        imagem_url = None
        if imagem_tag:
            imagem_url = imagem_tag.get("data-src") or imagem_tag.get("src")

        preco = None
        preco_original = None
        percentual_desconto = None

        # ------ Estratégia A: andes-money-amount__fraction (PDP/search com andes)
        andes_fractions = item.select(".andes-money-amount__fraction")
        if andes_fractions:
            # Observação: às vezes a ordem varia entre páginas — vamos tentar interpretar:
            # - se houver >=2 fractions, muitas vezes a 1ª é original e a 2ª é atual (conforme você observou)
            try:
                if len(andes_fractions) >= 2:
                    # primeira = original, segunda = atual (sua observação)
                    preco_original = text_to_price(andes_fractions[0].get_text(strip=True))
                    preco = text_to_price(andes_fractions[1].get_text(strip=True))
                    print("debug: preço via andes_fractions (>=2) — original then atual")
                else:
                    # só uma fraction — pode ser o preço atual ou o original dependendo do layout
                    preco = text_to_price(andes_fractions[0].get_text(strip=True))
                    print("debug: preço via andes_fractions (1) — assumindo atual")
            except Exception as e:
                print(f"debug: erro ao parsear andes_fractions: {e}")

        # ------ Estratégia B: procurar span/elemento com aria-label contendo "Agora:"
        if preco is None:
            agora_tag = item.select_one('[aria-label^="Agora:"], span[aria-label^="Agora:"], .andes-money-amount[aria-label^="Agora:"]')
            if agora_tag:
                # aria-label pode vir como "Agora: 4.798 reais" ou "Agora: 4.798,00 reais"
                aria = agora_tag.get("aria-label") or agora_tag.get_text()
                # extrair números (mantemos para text_to_price)
                # normalizar: remover "Agora:" e "reais"
                aria_clean = re.sub(r'(?i)\bAgora:?\b', '', aria).replace('reais', '').strip()
                # text_to_price deve lidar com formatos brasileiros (ex: "4.798,00" ou "4798")
                try:
                    preco = text_to_price(aria_clean)
                    print("debug: preço via aria-label 'Agora:'")
                except Exception as e:
                    print(f"debug: falha ao parsear aria 'Agora': {e}")

        # ------ Estratégia C: procurar classe andes-money-amount--cents-superscript (desconto/centavos)
        # às vezes o preço atual está em dois elementos (inteiro + cents superscript)
        if preco is None:
            inteiro_tag = item.select_one(".andes-money-amount__unit, .andes-money-amount__main-value")
            cents_tag = item.select_one(".andes-money-amount--cents-superscript, .andes-money-amount__fraction--cents")
            if inteiro_tag and cents_tag:
                combined = f"{inteiro_tag.get_text(strip=True)},{cents_tag.get_text(strip=True)}"
                try:
                    preco = text_to_price(combined)
                    print("debug: preço via inteiro + cents_supsript")
                except Exception as e:
                    print(f"debug: falha ao parsear inteiro+cents: {e}")

        # ------ Estratégia D: fallback clássico (price-tag-fraction)
        if preco is None:
            price_tag_frac = item.select_one(".price-tag-fraction")
            if price_tag_frac:
                try:
                    preco = text_to_price(price_tag_frac.get_text(strip=True))
                    print("debug: preço via price-tag-fraction")
                except Exception as e:
                    print(f"debug: falha ao parsear price-tag-fraction: {e}")

        # ------ Tentativa extra de achar preco original se ainda não foi encontrado
        if preco_original is None:
            # procurar preço riscado ou subprice
            orig_tag = item.select_one(".price-tag-strike .price-tag-fraction, .price-tag__subprice .price-tag-fraction, .andes-money-amount__fraction.price-original, .andes-money-amount--original .andes-money-amount__fraction")
            if orig_tag:
                try:
                    preco_original = text_to_price(orig_tag.get_text(strip=True))
                    print("debug: preco_original via seletor riscado/subprice")
                except Exception as e:
                    print(f"debug: falha ao parsear preco_original: {e}")

        # ------ Se ainda temos original via andes_fractions (caso len >=2 mas não calculado antes)
        if preco_original is None and andes_fractions and len(andes_fractions) >= 2:
            try:
                preco_original = text_to_price(andes_fractions[0].get_text(strip=True))
                if preco is None:
                    preco = text_to_price(andes_fractions[1].get_text(strip=True))
                print("debug: preco_original recuperado de andes_fractions[0]")
            except Exception as e:
                print(f"debug: erro ao recuperar preco_original de andes_fractions: {e}")

        # ------ Calcular percentual de desconto, se possível
        if preco_original and preco and preco_original > preco:
            try:
                percentual_desconto = round(((preco_original - preco) / preco_original) * 100, 1)
            except Exception as e:
                print(f"debug: erro ao calcular desconto: {e}")
                percentual_desconto = None

        # --- ID ML ---
        produto_id_ml = item.get("data-id") or (extract_ml_id(link) if link else None)

        # --- ADICIONA AO RESULTADO (requer nome, link e preco atual) ---
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
            # debug para entender por que foi descartado
            print(f"debug: item descartado (nome={bool(nome)}, preco={bool(preco)}, link={bool(link)})")

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
