#!/usr/bin/env python3
"""
Script para remover produtos que não foram atualizados há muito tempo.

Remove produtos onde:
- ultima_atualizacao > X dias (padrão: 5 dias)

Isso limpa produtos que saíram das primeiras páginas ou não estão mais disponíveis.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database_postgres import get_database
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def identificar_produtos_desatualizados(db, dias: int = 5):
    """Identifica produtos que não foram atualizados há X dias"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # Query para encontrar produtos desatualizados
        cursor.execute("""
            SELECT 
                id, 
                nome, 
                preco_atual, 
                categoria,
                ultima_atualizacao,
                link
            FROM produtos
            WHERE ultima_atualizacao < NOW() - INTERVAL '%s days'
            ORDER BY ultima_atualizacao ASC
        """, (dias,))
        
        produtos = cursor.fetchall()
        return produtos
        
    finally:
        db.release_connection(conn)


def exibir_produtos(produtos, dias: int):
    """Exibe lista de produtos identificados"""
    if not produtos:
        print(f"✅ Nenhum produto desatualizado há mais de {dias} dias!")
        return False
    
    print(f"\n🔍 Encontrados {len(produtos)} produtos sem atualização há mais de {dias} dias:\n")
    print("-" * 140)
    print(f"{'ID':<6} {'Última Atualização':<20} {'Preço':<12} {'Categoria':<20} {'Nome':<60}")
    print("-" * 140)
    
    for produto in produtos:
        id_prod, nome, preco_atual, categoria, ultima_atualizacao, link = produto
        nome_truncado = nome[:57] + "..." if len(nome) > 60 else nome
        
        # Calcular há quantos dias foi atualizado
        dias_atras = (datetime.now() - ultima_atualizacao).days
        data_str = f"{ultima_atualizacao.strftime('%Y-%m-%d %H:%M')} ({dias_atras}d)"
        
        print(f"{id_prod:<6} {data_str:<20} R$ {preco_atual:<9.2f} {categoria:<20} {nome_truncado:<60}")
    
    print("-" * 140)
    return True


def remover_produtos(db, produto_ids):
    """Remove produtos e seu histórico do banco de dados"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # Remover histórico de preços
        cursor.execute("""
            DELETE FROM precos_historico 
            WHERE produto_id = ANY(%s)
        """, (produto_ids,))
        
        historico_removido = cursor.rowcount
        
        # Remover produtos
        cursor.execute("""
            DELETE FROM produtos 
            WHERE id = ANY(%s)
        """, (produto_ids,))
        
        produtos_removidos = cursor.rowcount
        
        conn.commit()
        
        print(f"\n✅ Removidos:")
        print(f"   - {produtos_removidos} produtos")
        print(f"   - {historico_removido} registros de histórico")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao remover produtos: {e}")
        raise
    finally:
        db.release_connection(conn)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove produtos desatualizados do banco de dados')
    parser.add_argument('--dias', type=int, default=5, 
                       help='Número de dias sem atualização para considerar produto desatualizado (padrão: 5)')
    parser.add_argument('--auto', action='store_true',
                       help='Executar automaticamente sem confirmação (use com cuidado!)')
    
    args = parser.parse_args()
    
    print("=" * 140)
    print(f"🧹 LIMPEZA DE PRODUTOS DESATUALIZADOS (>{args.dias} dias)")
    print("=" * 140)
    
    # Conectar ao banco
    try:
        db = get_database()
        print("✅ Conectado ao banco de dados PostgreSQL")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return 1
    
    # Identificar produtos desatualizados
    print(f"\n🔍 Buscando produtos sem atualização há mais de {args.dias} dias...")
    produtos = identificar_produtos_desatualizados(db, args.dias)
    
    # Exibir produtos
    if not exibir_produtos(produtos, args.dias):
        return 0
    
    # Se modo automático, pular confirmação
    if args.auto:
        print("\n⚡ Modo automático ativado - removendo produtos...")
    else:
        # Confirmar remoção
        print("\n⚠️  ATENÇÃO: Esta ação é IRREVERSÍVEL!")
        print("   Os produtos e todo seu histórico de preços serão removidos permanentemente.")
        print(f"   Estes produtos não foram atualizados há mais de {args.dias} dias.")
        print("   Provavelmente saíram das primeiras 4 páginas ou não estão mais disponíveis.")
        
        resposta = input("\n❓ Deseja prosseguir com a remoção? (sim/não): ").strip().lower()
        
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("\n❌ Operação cancelada pelo usuário.")
            return 0
    
    # Remover produtos
    produto_ids = [p[0] for p in produtos]
    print(f"\n🗑️  Removendo {len(produto_ids)} produtos...")
    
    try:
        remover_produtos(db, produto_ids)
        print("\n✅ Limpeza concluída com sucesso!")
        print(f"\n💡 Dica: Produtos que voltarem às primeiras 4 páginas serão coletados novamente.")
        return 0
    except Exception as e:
        print(f"\n❌ Erro durante a limpeza: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
