"""
Modelos Pydantic para validação de dados.
Define a estrutura dos produtos e histórico de preços.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ProdutoBase(BaseModel):
    """Dados básicos de um produto"""
    nome: str = Field(..., min_length=3, max_length=500, description="Nome do produto")
    preco: float = Field(..., gt=0, description="Preço atual do produto")
    link: str = Field(..., description="URL do produto")
    categoria: str = Field(..., description="Categoria do produto")
    produto_id_ml: Optional[str] = Field(None, description="ID do produto no Mercado Livre")
    preco_original: Optional[float] = Field(None, description="Preço original (antes do desconto)")
    percentual_desconto: Optional[float] = Field(None, description="Percentual de desconto aplicado")
    imagem_url: Optional[str] = Field(None, description="URL da imagem do produto")
    
    @validator("nome")
    def nome_nao_vazio(cls, v):
        if not v or v.isspace():
            raise ValueError("Nome não pode estar vazio")
        return v.strip()
    
    @validator("link")
    def link_valido(cls, v):
        if not v.startswith("http"):
            raise ValueError("Link deve ser uma URL válida")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Samsung Galaxy A12 128GB",
                "preco": 599.99,
                "link": "https://produto.mercadolivre.com.br/...",
                "categoria": "celulares",
                "produto_id_ml": "MLB123456789",
                "preco_original": 699.99,
                "percentual_desconto": 14.3,
                "imagem_url": "https://http2.mlstatic.com/D_NQ_NP_123456-MLA47842095652_102021-O.webp"
            }
        }


class Produto(ProdutoBase):
    """Modelo completo de um produto"""
    id: Optional[int] = Field(None, description="ID do produto no banco")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de coleta")
    primeira_coleta: Optional[datetime] = None
    ultima_atualizacao: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Para compatibilidade com SQLAlchemy


class PrecosHistorico(BaseModel):
    """Histórico de preços de um produto"""
    id: Optional[int] = None
    produto_id: int = Field(..., description="ID do produto")
    preco: float = Field(..., gt=0, description="Preço neste momento")
    data: datetime = Field(default_factory=datetime.now, description="Data da coleta")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "produto_id": 1,
                "preco": 599.99,
                "data": "2024-11-20T10:30:00"
            }
        }


class EstatisticasPreco(BaseModel):
    """Estatísticas de preço de um produto"""
    produto_id: int
    nome: str
    categoria: str
    preco_minimo: float
    preco_maximo: float
    preco_medio: float
    preco_atual: float
    variacao_percentual: float = Field(..., description="Variação em percentual")
    total_coletas: int = Field(..., description="Quantas vezes foi coletado")
    primeira_coleta: datetime
    ultima_coleta: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "produto_id": 1,
                "nome": "Samsung Galaxy A12",
                "categoria": "celulares",
                "preco_minimo": 550.00,
                "preco_maximo": 650.00,
                "preco_medio": 599.99,
                "preco_atual": 599.99,
                "variacao_percentual": 8.5,
                "total_coletas": 10,
                "primeira_coleta": "2024-11-10T10:30:00",
                "ultima_coleta": "2024-11-20T10:30:00"
            }
        }


class RelatorioColeta(BaseModel):
    """Relatório de uma coleta"""
    id: Optional[int] = None
    categoria: str
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    total_produtos: int
    total_novos: int = 0
    total_atualizados: int = 0
    status: str = Field(..., description="'sucesso', 'erro', 'em_progresso'")
    mensagem_erro: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "categoria": "celulares",
                "data_inicio": "2024-11-20T10:30:00",
                "data_fim": "2024-11-20T10:35:00",
                "total_produtos": 100,
                "total_novos": 45,
                "total_atualizados": 55,
                "status": "sucesso"
            }
        }
