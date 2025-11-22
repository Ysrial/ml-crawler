"""
Gerenciamento do banco de dados SQLite.
Define o schema e fornece funções para CRUD de produtos e histórico de preços.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from contextlib import contextmanager
from typing import List, Optional

from .config import DATABASE_PATH, LOG_DIR
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


class Database:
    """Gerenciador de banco de dados SQLite"""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.initialize_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões seguras"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na transação: {e}")
            raise
        finally:
            conn.close()
    
    def initialize_db(self):
        """Cria as tabelas se não existirem"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Produtos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    link TEXT NOT NULL UNIQUE,
                    categoria TEXT NOT NULL,
                    preco_atual REAL,
                    primeira_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de Histórico de Preços
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS precos_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    preco REAL NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de Coletas (logs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coletas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_categoria ON produtos(categoria)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_id ON precos_historico(produto_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_data ON precos_historico(data)")
            
            logger.info("✅ Banco de dados inicializado")
    
    # ========== OPERAÇÕES COM PRODUTOS ==========
    
    def adicionar_produto(self, produto: Produto) -> int:
        """Adiciona novo produto e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO produtos (nome, link, categoria, preco_atual)
                    VALUES (?, ?, ?, ?)
                """, (produto.nome, produto.link, produto.categoria, produto.preco))
                
                produto_id = cursor.lastrowid
                logger.info(f"✅ Produto adicionado: {produto.nome} (ID: {produto_id})")
                return produto_id
            except sqlite3.IntegrityError:
                logger.warning(f"⚠️ Produto duplicado: {produto.nome}")
                return None
    
    def obter_produto_por_link(self, link: str) -> Optional[dict]:
        """Obtém produto pelo link"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE link = ?", (link,))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
    
    def obter_produtos_por_categoria(self, categoria: str) -> List[dict]:
        """Lista todos os produtos de uma categoria"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM produtos 
                WHERE categoria = ? 
                ORDER BY nome
            """, (categoria,))
            return [dict(row) for row in cursor.fetchall()]
    
    def atualizar_preco(self, produto_id: int, novo_preco: float):
        """Atualiza preço atual e cria histórico"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Atualizar preço atual
            cursor.execute("""
                UPDATE produtos 
                SET preco_atual = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_preco, produto_id))
            
            # Adicionar ao histórico
            cursor.execute("""
                INSERT INTO precos_historico (produto_id, preco)
                VALUES (?, ?)
            """, (produto_id, novo_preco))
            
            logger.info(f"💰 Preço atualizado para produto ID {produto_id}: R$ {novo_preco}")
    
    # ========== OPERAÇÕES COM COLETAS ==========
    
    def iniciar_coleta(self, categoria: str) -> int:
        """Inicia uma nova coleta e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO coletas (categoria, status)
                VALUES (?, 'em_progresso')
            """, (categoria,))
            return cursor.lastrowid
    
    def finalizar_coleta(self, coleta_id: int, total_produtos: int, 
                        total_novos: int, total_atualizados: int, 
                        sucesso: bool, erro: Optional[str] = None):
        """Finaliza uma coleta com estatísticas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            status = "sucesso" if sucesso else "erro"
            cursor.execute("""
                UPDATE coletas 
                SET data_fim = CURRENT_TIMESTAMP, 
                    total_produtos = ?, 
                    total_novos = ?,
                    total_atualizados = ?,
                    status = ?,
                    mensagem_erro = ?
                WHERE id = ?
            """, (total_produtos, total_novos, total_atualizados, status, erro, coleta_id))
            
            logger.info(f"✅ Coleta {coleta_id} finalizada: {total_produtos} produtos")
    
    # ========== ANÁLISES E RELATÓRIOS ==========
    
    def obter_estatisticas_produto(self, produto_id: int) -> dict:
        """Obtém estatísticas completas de um produto"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Dados do produto
            cursor.execute("""
                SELECT * FROM produtos WHERE id = ?
            """, (produto_id,))
            produto = dict(cursor.fetchone())
            
            # Histórico de preços
            cursor.execute("""
                SELECT preco, data FROM precos_historico 
                WHERE produto_id = ? 
                ORDER BY data
            """, (produto_id,))
            historico = [dict(row) for row in cursor.fetchall()]
            
            if not historico:
                return None
            
            precos = [h["preco"] for h in historico]
            
            return {
                "produto_id": produto_id,
                "nome": produto["nome"],
                "categoria": produto["categoria"],
                "preco_minimo": min(precos),
                "preco_maximo": max(precos),
                "preco_medio": sum(precos) / len(precos),
                "preco_atual": produto["preco_atual"],
                "variacao_percentual": ((precos[-1] - precos[0]) / precos[0] * 100) if precos[0] > 0 else 0,
                "total_coletas": len(historico),
                "primeira_coleta": produto["primeira_coleta"],
                "ultima_coleta": historico[-1]["data"] if historico else None
            }
    
    def obter_relatorio_categoria(self, categoria: str) -> dict:
        """Gera relatório completo de uma categoria"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM produtos WHERE categoria = ?
            """, (categoria,))
            total = cursor.fetchone()["total"]
            
            cursor.execute("""
                SELECT 
                    AVG(preco_atual) as preco_medio,
                    MIN(preco_atual) as preco_minimo,
                    MAX(preco_atual) as preco_maximo
                FROM produtos 
                WHERE categoria = ?
            """, (categoria,))
            stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT * FROM coletas 
                WHERE categoria = ? 
                ORDER BY data_inicio DESC 
                LIMIT 1
            """, (categoria,))
            ultima_coleta = cursor.fetchone()
            
            return {
                "categoria": categoria,
                "total_produtos": total,
                "preco_medio": stats["preco_medio"],
                "preco_minimo": stats["preco_minimo"],
                "preco_maximo": stats["preco_maximo"],
                "ultima_coleta": dict(ultima_coleta) if ultima_coleta else None
            }
    
    def limpar_dados_antigos(self, dias: int = 30):
        """Remove histórico de preços com mais de X dias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM precos_historico 
                WHERE data < datetime('now', '-' || ? || ' days')
            """, (dias,))
            logger.info(f"🗑️  Removidos históricos com mais de {dias} dias")


# Instância global
db = Database()


if __name__ == "__main__":
    # Teste
    db.initialize_db()
    print("✅ Banco de dados criado com sucesso!")
