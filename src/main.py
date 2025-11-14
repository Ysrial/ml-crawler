from .scraper import scrape_all_pages
import json
import sys

# URL padrão - pode ser substituída por linha de comando
URL_PADRAO = "https://lista.mercadolivre.com.br/"

def main():
    # Se passou uma URL como argumento, usa ela; senão usa a padrão
    url = sys.argv[1] if len(sys.argv) > 1 else URL_PADRAO
    
    # Parâmetros opcionais de linha de comando
    max_produtos = int(sys.argv[2]) if len(sys.argv) > 2 else None
    max_paginas = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print(f"🚀 Iniciando scraping com paginação...")
    print(f"URL: {url}")
    print(f"Máximo de produtos: {max_produtos if max_produtos else 'Ilimitado'}")
    print(f"Máximo de páginas: {max_paginas}\n")
    
    produtos = scrape_all_pages(url, max_products=max_produtos, max_pages=max_paginas)

    with open("produtos.json", "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(produtos)} produtos salvos em produtos.json")


if __name__ == "__main__":
    main()
