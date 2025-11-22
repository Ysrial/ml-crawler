from .scraper import scrape_all_pages
from urllib.parse import urlparse
import sys

def extrair_categoria_da_url(url: str) -> str:
    """Extrai a categoria da URL do Mercado Livre."""
    # Exemplo: "https://lista.mercadolivre.com.br/celular" -> "celular"
    path = urlparse(url).path
    categoria = path.strip("/").split("/")[0] if path else "geral"
    return categoria.lower()

def main():
    # Se passou uma URL como argumento, usa ela; senão exibe erro
    if len(sys.argv) < 2:
        print("Uso: python -m src.main <url> [max_produtos] [max_paginas]")
        print("Exemplo: python -m src.main 'https://lista.mercadolivre.com.br/celular' 50 3")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Parâmetros opcionais de linha de comando
    max_produtos = int(sys.argv[2]) if len(sys.argv) > 2 else None
    max_paginas = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # Extrair categoria da URL
    categoria = extrair_categoria_da_url(url)
    
    print(f"🚀 Iniciando scraping com integração ao banco de dados...")
    print(f"URL: {url}")
    print(f"Categoria: {categoria}")
    print(f"Máximo de produtos: {max_produtos if max_produtos else 'Ilimitado'}")
    print(f"Máximo de páginas: {max_paginas}\n")
    
    # Realizar scraping com integração ao banco de dados
    resultado = scrape_all_pages(url, categoria, max_produtos, max_paginas)

    if resultado["status"] == "sucesso":
        print(f"\n✅ Coleta finalizada com sucesso!")
        print(f"   Total de produtos processados: {resultado['total_produtos']}")
        print(f"   Novos produtos: {resultado['total_novos']}")
        print(f"   Preços atualizados: {resultado['total_atualizados']}")
    else:
        print(f"\n❌ Erro na coleta: {resultado.get('erro', 'Erro desconhecido')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
