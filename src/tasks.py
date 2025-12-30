import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from prefect import flow, task, get_run_logger
from src.config import CATEGORIAS, SCHEDULE_CRON, SCHEDULE_TIMEZONE, DELAY_BETWEEN_CATEGORIES
from src.scraper import scrape_all_pages
from src.database_postgres import get_database
from datetime import datetime
import time

@task(name="Scrape Categoria", retries=3, retry_delay_seconds=60)
def scrape_categoria(categoria: str, config: dict) -> dict:
    logger = get_run_logger()
    logger.info(f"🔍 Iniciando scraping da categoria: {categoria}")
    
    try:
        base_url = config["url"]
        max_paginas = config.get("max_paginas", 6)
        max_produtos = config.get("max_produtos_por_pagina", 50)
        
        resultado = scrape_all_pages(
            base_url=base_url,
            categoria=categoria,
            max_products=max_produtos,
            max_pages=max_paginas
        )
        
        db = get_database()
        historicos_salvos = 0
        
        try:
            produtos_categoria = db.obter_produtos_por_categoria(categoria)
            
            for produto in produtos_categoria:
                produto_id = produto.get("id")
                preco_atual = produto.get("preco_atual")
                
                if produto_id and preco_atual:
                    query = """
                    SELECT preco, data FROM precos_historico 
                    WHERE produto_id = %s 
                    ORDER BY data DESC 
                    LIMIT 1
                    """
                    historico_anterior = db.executar(query, (produto_id,), fetch=True)
                    
                    if historico_anterior:
                        preco_anterior = historico_anterior[0][0]
                        data_anterior = historico_anterior[0][1]
                        
                        if float(preco_anterior) != float(preco_atual):
                            db.executar(
                                """
                                INSERT INTO precos_historico (produto_id, preco, data)
                                VALUES (%s, %s, NOW())
                                """,
                                (produto_id, preco_atual)
                            )
                            historicos_salvos += 1
                            diferenca = float(preco_atual) - float(preco_anterior)
                            percentual = (diferenca / float(preco_anterior) * 100) if preco_anterior > 0 else 0
                            logger.info(f"💾 Histórico salvo: {produto['nome']} - R${preco_anterior:.2f} → R${preco_atual:.2f} ({percentual:+.1f}%)")
                        else:
                            logger.debug(f"ℹ️ Produto sem variação: {produto['nome']} - R${preco_atual:.2f}")
                    else:
                        db.executar(
                            """
                            INSERT INTO precos_historico (produto_id, preco, data)
                            VALUES (%s, %s, NOW())
                            """,
                            (produto_id, preco_atual)
                        )
                        historicos_salvos += 1
                        logger.info(f"📝 Primeiro histórico: {produto['nome']} - R${preco_atual:.2f}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar histórico: {str(e)}")
        
        logger.info(f"✅ Scraping concluído para {categoria}")
        logger.info(f"   - Total processados: {resultado.get('total_produtos', 0)}")
        logger.info(f"   - Novos: {resultado.get('total_novos', 0)}")
        logger.info(f"   - Atualizados: {resultado.get('total_atualizados', 0)}")
        logger.info(f"   - Históricos salvos: {historicos_salvos}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping de {categoria}: {str(e)}")
        raise


@flow(
    name="ML Crawler - Coleta Automática",
    description="Coleta de dados de todas as categorias configuradas"
)
def coletar_todas_categorias():
    logger = get_run_logger()
    
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando coleta automática em {datetime.now()}")
    logger.info("=" * 60)
    
    resultados = {}
    total_geral = 0
    novos_geral = 0
    atualizados_geral = 0
    
    categorias_list = list(CATEGORIAS.items())
    total_categorias = len(categorias_list)
    
    for idx, (categoria, config) in enumerate(categorias_list, 1):
        try:
            resultado = scrape_categoria(categoria, config)
            resultados[categoria] = resultado
            
            total_geral += resultado.get("total_produtos", 0)
            novos_geral += resultado.get("total_novos", 0)
            atualizados_geral += resultado.get("total_atualizados", 0)
            
            if idx < total_categorias:  
                logger.info(f"⏳ Aguardando {DELAY_BETWEEN_CATEGORIES} segundos antes da próxima categoria...")
                time.sleep(DELAY_BETWEEN_CATEGORIES)
            
        except Exception as e:
            logger.error(f"❌ Falha na coleta de {categoria}: {str(e)}")
            resultados[categoria] = {"status": "erro", "erro": str(e)}
    
    logger.info("=" * 60)
    logger.info("📊 RESUMO DA COLETA")
    logger.info("=" * 60)
    logger.info(f"✅ Total de produtos processados: {total_geral}")
    logger.info(f"🆕 Novos produtos: {novos_geral}")
    logger.info(f"🔄 Preços atualizados: {atualizados_geral}")
    logger.info(f"⏰ Finalizado em: {datetime.now()}")
    logger.info("=" * 60)
    
    return {
        "status": "completo",
        "resultados": resultados,
        "total_produtos": total_geral,
        "novos": novos_geral,
        "atualizados": atualizados_geral,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    coletar_todas_categorias()
