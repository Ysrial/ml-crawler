"""
Gerenciamento do banco de dados com PostgreSQL.
Otimizado para Streamlit com caching de conexões.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime
from pathlib import Path
import logging
import os
from typing import List, Optional, Dict
import streamlit as st

from .config import LOG_DIR
from .models import Produto, PrecosHistorico, RelatorioColeta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabasePostgres:
    """Gerenciador de banco de dados PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.init_connection_pool()
    
    @staticmethod
    def get_db_config():
        """Obtém configuração do banco de dados do ambiente"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "ml_crawler"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
        }

    def executar(self, sql: str, params: tuple = None, fetch: bool = False):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            if fetch:
                result = cursor.fetchall()
            else:
                result = None

            conn.commit()
            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro em executar(): {e}")
            raise e

        finally:
            self.release_connection(conn)

    def obter_produto_por_id_ml(self, produto_id_ml: str):
              conn = self.get_connection()
              try:
                  cursor = conn.cursor(cursor_factory=RealDictCursor)
                  cursor.execute(
                      "SELECT * FROM produtos WHERE produto_id_ml = %s",
                      (produto_id_ml,)
                  )
                  return cursor.fetchone()
              finally:
                  self.release_connection(conn)

    
    def init_connection_pool(self):
        """Inicializa pool de conexões"""
        try:
            config = self.get_db_config()
            self.pool = SimpleConnectionPool(1, 20, **config)
            logger.info("✅ Pool de conexões criado")
        except Exception as e:
            logger.error(f"❌ Erro ao criar pool: {e}")
            raise
    
    def get_connection(self):
        """Obtém conexão do pool"""
        if not self.pool:
            self.init_connection_pool()
        return self.pool.getconn()
    
    def release_connection(self, conn):
        """Devolve conexão ao pool"""
        if self.pool:
            self.pool.putconn(conn)
    
    def initialize_db(self):
        """Cria as tabelas se não existirem"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Tabela de Produtos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    link TEXT NOT NULL UNIQUE,
                    categoria TEXT NOT NULL,
                    produto_id_ml TEXT,
                    preco_atual NUMERIC(10, 2),
                    primeira_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de Histórico de Preços
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS precos_historico (
                    id SERIAL PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    preco NUMERIC(10, 2) NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de Coletas (logs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coletas (
                    id SERIAL PRIMARY KEY,
                    categoria TEXT NOT NULL,
                    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_fim TIMESTAMP,
                    total_produtos INTEGER,
                    total_novos INTEGER DEFAULT 0,
                    total_atualizados INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'em_progresso',
                    mensagem_erro TEXT
                )
            """)
            
            # Índices para performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_categoria 
                ON produtos(categoria)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produto_id 
                ON precos_historico(produto_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_data 
                ON precos_historico(data)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_coleta_categoria 
                ON coletas(categoria)
            """)
            
            conn.commit()
            logger.info("✅ Banco de dados PostgreSQL inicializado")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro ao inicializar BD: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    # ========== OPERAÇÕES COM PRODUTOS ==========
    
    def adicionar_produto(self, produto: Produto) -> Optional[int]:
        """Adiciona novo produto e retorna o ID, verifica duplicata por produto_id_ml"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Verificar se produto já existe pelo produto_id_ml
            if produto.produto_id_ml:
                cursor.execute(
                    "SELECT id FROM produtos WHERE produto_id_ml = %s",
                    (produto.produto_id_ml,)
                )
                resultado = cursor.fetchone()
                if resultado:
                    produto_id = resultado[0]
                    logger.warning(f"⚠️ Produto duplicado (ID ML: {produto.produto_id_ml}): {produto.nome}")
                    return produto_id  # Retorna ID existente
            
            # Inserir novo produto
            cursor.execute("""
                INSERT INTO produtos (nome, link, categoria, preco_atual, produto_id_ml)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (produto.nome, produto.link, produto.categoria, produto.preco, produto.produto_id_ml))
            
            produto_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"✅ Produto adicionado: {produto.nome} (ID: {produto_id})")
            return produto_id
            
        except psycopg2.IntegrityError:
            conn.rollback()
            logger.warning(f"⚠️ Produto duplicado (por constraint): {produto.nome}")
            # Tentar recuperar ID existente
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM produtos WHERE link = %s", (produto.link,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro ao adicionar produto: {e}")
            return None
        finally:
            self.release_connection(conn)
    
    def obter_produto_por_link(self, link: str) -> Optional[Dict]:
        """Obtém produto pelo link"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM produtos WHERE link = %s", (link,))
            return cursor.fetchone()
        finally:
            self.release_connection(conn)
    
    def obter_produtos_por_categoria(self, categoria: str) -> List[Dict]:
        """Lista todos os produtos de uma categoria"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM produtos 
                WHERE categoria = %s 
                ORDER BY nome
            """, (categoria,))
            return cursor.fetchall()
        finally:
            self.release_connection(conn)
    
    def atualizar_preco(self, produto_id: int, novo_preco: float):
        """Atualiza preço atual e cria histórico"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Atualizar preço atual
            cursor.execute("""
                UPDATE produtos 
                SET preco_atual = %s, ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (novo_preco, produto_id))
            
            # Adicionar ao histórico
            cursor.execute("""
                INSERT INTO precos_historico (produto_id, preco)
                VALUES (%s, %s)
            """, (produto_id, novo_preco))
            
            conn.commit()
            logger.info(f"💰 Preço atualizado para produto ID {produto_id}: R$ {novo_preco}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro ao atualizar preço: {e}")
        finally:
            self.release_connection(conn)
    
    def obter_todos_produtos(self, limite: int = 1000) -> List[Dict]:
        """Obtém todos os produtos com limite"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM produtos 
                ORDER BY ultima_atualizacao DESC 
                LIMIT %s
            """, (limite,))
            return cursor.fetchall()
        finally:
            self.release_connection(conn)
    
    # ========== OPERAÇÕES COM COLETAS ==========
    
    def iniciar_coleta(self, categoria: str) -> int:
        """Inicia uma nova coleta e retorna o ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO coletas (categoria, status)
                VALUES (%s, 'em_progresso')
                RETURNING id
            """, (categoria,))
            coleta_id = cursor.fetchone()[0]
            conn.commit()
            return coleta_id
        finally:
            self.release_connection(conn)
    
    def finalizar_coleta(self, coleta_id: int, total_produtos: int, 
                        total_novos: int, total_atualizados: int, 
                        sucesso: bool, erro: Optional[str] = None):
        """Finaliza uma coleta com estatísticas"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            status = "sucesso" if sucesso else "erro"
            cursor.execute("""
                UPDATE coletas 
                SET data_fim = CURRENT_TIMESTAMP, 
                    total_produtos = %s, 
                    total_novos = %s,
                    total_atualizados = %s,
                    status = %s,
                    mensagem_erro = %s
                WHERE id = %s
            """, (total_produtos, total_novos, total_atualizados, status, erro, coleta_id))
            conn.commit()
            logger.info(f"✅ Coleta {coleta_id} finalizada: {total_produtos} produtos")
        finally:
            self.release_connection(conn)
    
    # ========== ANÁLISES E RELATÓRIOS ==========
    
    def obter_estatisticas_produto(self, produto_id: int) -> Optional[Dict]:
        """Obtém estatísticas completo de um produto"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Dados do produto
            cursor.execute("""
                SELECT * FROM produtos WHERE id = %s
            """, (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                return None
            
            # Histórico de preços
            cursor.execute("""
                SELECT preco, data FROM precos_historico 
                WHERE produto_id = %s 
                ORDER BY data
            """, (produto_id,))
            historico = cursor.fetchall()
            
            if not historico:
                return None
            
            precos = [h['preco'] for h in historico]
            
            return {
                "produto_id": produto_id,
                "nome": produto["nome"],
                "categoria": produto["categoria"],
                "preco_minimo": float(min(precos)),
                "preco_maximo": float(max(precos)),
                "preco_medio": float(sum(precos) / len(precos)),
                "preco_atual": float(produto["preco_atual"]),
                "variacao_percentual": float(((precos[-1] - precos[0]) / precos[0] * 100) if precos[0] > 0 else 0),
                "total_coletas": len(historico),
                "primeira_coleta": produto["primeira_coleta"],
                "ultima_coleta": historico[-1]["data"] if historico else None
            }
        finally:
            self.release_connection(conn)
    
    def obter_relatorio_categoria(self, categoria: str) -> Dict:
        """Gera relatório completo de uma categoria"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM produtos WHERE categoria = %s
            """, (categoria,))
            total = cursor.fetchone()["total"]
            
            cursor.execute("""
                SELECT 
                    AVG(preco_atual::float) as preco_medio,
                    MIN(preco_atual::float) as preco_minimo,
                    MAX(preco_atual::float) as preco_maximo
                FROM produtos 
                WHERE categoria = %s
            """, (categoria,))
            stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT * FROM coletas 
                WHERE categoria = %s 
                ORDER BY data_inicio DESC 
                LIMIT 1
            """, (categoria,))
            ultima_coleta = cursor.fetchone()
            
            return {
                "categoria": categoria,
                "total_produtos": total,
                "preco_medio": float(stats["preco_medio"]) if stats["preco_medio"] else 0,
                "preco_minimo": float(stats["preco_minimo"]) if stats["preco_minimo"] else 0,
                "preco_maximo": float(stats["preco_maximo"]) if stats["preco_maximo"] else 0,
                "ultima_coleta": dict(ultima_coleta) if ultima_coleta else None
            }
        finally:
            self.release_connection(conn)
    
    def obter_historico_preco(self, produto_id: int, dias: int = 30) -> List[Dict]:
        """Obtém histórico de preço dos últimos X dias"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT preco, data FROM precos_historico 
                WHERE produto_id = %s 
                AND data >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                ORDER BY data ASC
            """, (produto_id, dias))
            return cursor.fetchall()
        finally:
            self.release_connection(conn)
    
    def limpar_dados_antigos(self, dias: int = 90):
        """Remove histórico de preços com mais de X dias"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM precos_historico 
                WHERE data < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (dias,))
            deletados = cursor.rowcount
            conn.commit()
            logger.info(f"🗑️  Removidos {deletados} registros com mais de {dias} dias")
        finally:
            self.release_connection(conn)
    
    def obter_categorias(self) -> List[str]:
        """Obtém lista de categorias com produtos"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT categoria 
                FROM produtos 
                ORDER BY categoria
            """)
            result = cursor.fetchall()
            return [row['categoria'] for row in result] if result else []
        except Exception as e:
            logger.error(f"❌ Erro ao obter categorias: {e}")
            return []
        finally:
            self.release_connection(conn)

    def close_pool(self):
        """Fecha pool de conexões"""
        if self.pool:
            self.pool.closeall()
            logger.info("✅ Pool de conexões fechado")


# ========== INTEGRAÇÃO COM STREAMLIT ==========

# @st.cache_resource
def get_database():
    """
    Obtém instância do banco de dados em cache do Streamlit.
    Reusa a mesma conexão entre reruns.
    """
    db = DatabasePostgres()
    db.initialize_db()
    return db


# Instância global
db = get_database()
