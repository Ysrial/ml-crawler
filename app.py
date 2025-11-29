"""
Dashboard Streamlit para ML Crawler - Versão Preliminar
Mostra estatísticas de preços e produtos monitorados.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar página
st.set_page_config(
    page_title="ML Crawler Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ========== IMPORTAR BANCO DE DADOS ==========
try:
    from src.database_postgres import get_database
    
    db = get_database()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco: {e}")
    st.stop()

# ========== HEADER ==========
st.title("📊 ML Crawler - Monitorador de Preços")
st.markdown("Dashboard para acompanhar variações de preço no Mercado Livre")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Obter categorias do banco de dados
    try:
        categorias = db.obter_categorias()
        if not categorias:
            st.warning("❌ Nenhuma categoria encontrada no banco!")
            st.info("Execute o scraper para começar a coletar dados!")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao obter categorias: {e}")
        st.stop()
    
    categoria_selecionada = st.selectbox(
        "Selecione uma categoria",
        categorias
    )


# ========== CONTEÚDO PRINCIPAL ==========

# Obter dados da categoria
try:
    relatorio = db.obter_relatorio_categoria(categoria_selecionada)
    produtos = db.obter_produtos_por_categoria(categoria_selecionada)
    
    if not produtos:
        st.warning(f"⚠️ Nenhum produto encontrado em {categoria_selecionada}")
        st.info("Execute o scraper para começar a coletar dados!")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Erro ao buscar dados: {e}")
    st.stop()

# ========== MÉTRICAS PRINCIPAIS ==========
st.markdown(f"## 📈 Análise: {categoria_selecionada.upper()}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Total de Produtos",
        f"{relatorio['total_produtos']}",
        help="Quantidade de produtos monitorados"
    )

with col2:
    st.metric(
        "💰 Preço Mínimo",
        f"R$ {relatorio['preco_minimo']:.2f}",
        help="Menor preço encontrado"
    )

with col3:
    st.metric(
        "📊 Preço Médio",
        f"R$ {relatorio['preco_medio']:.2f}",
        help="Preço médio dos produtos"
    )

with col4:
    st.metric(
        "💎 Preço Máximo",
        f"R$ {relatorio['preco_maximo']:.2f}",
        help="Maior preço encontrado"
    )

st.markdown("---")

# ========== INFORMAÇÕES DE COLETA ==========
if relatorio["ultima_coleta"]:
    coleta = relatorio["ultima_coleta"]
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"📅 Última coleta: {coleta['data_inicio']}")
    with col2:
        st.info(f"✅ {coleta['total_produtos']} produtos encontrados")
    with col3:
        st.info(f"🔄 Status: {coleta['status'].upper()}")

st.markdown("---")

# ========== LISTA DE PRODUTOS ==========
st.markdown("## 🛍️ Produtos Monitorados")

# Filtro e busca
col1, col2 = st.columns([3, 1])

with col1:
    busca = st.text_input("🔍 Buscar produto", "")

with col2:
    limite = st.slider("Mostrar", 5, 50, 12)

# Filtrar produtos
if busca:
    produtos_filtrados = [
        p for p in produtos 
        if busca.lower() in p["nome"].lower()
    ]
else:
    produtos_filtrados = produtos[:limite]

# CSS para cards
st.markdown("""
    <style>
    .product-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        border: 1px solid #e0e0e0;
    }
    .product-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .product-image {
        width: 100%;
        height: 180px;
        object-fit: contain;
        border-radius: 8px;
        margin-bottom: 12px;
        background: #f5f5f5;
    }
    .product-name {
        font-size: 14px;
        font-weight: 500;
        color: #333;
        margin-bottom: 8px;
        min-height: 40px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .price-current {
        font-size: 28px;
        font-weight: 700;
        color: #00a650;
        margin: 8px 0;
    }
    .price-original {
        font-size: 14px;
        color: #999;
        text-decoration: line-through;
        margin-bottom: 4px;
    }
    .discount-badge {
        background: #ff6b6b;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-top: 8px;
    }
    .savings-badge {
        background: #00a650;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-top: 8px;
    }
    .product-link {
        display: block;
        text-align: center;
        background: #3483fa;
        color: white !important;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        margin-top: 12px;
        font-weight: 500;
        transition: background 0.2s;
    }
    .product-link:hover {
        background: #2968c8;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# Exibir produtos em grid de cards
if produtos_filtrados:
    # Criar grid de 3 colunas
    for i in range(0, len(produtos_filtrados), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(produtos_filtrados):
                produto = produtos_filtrados[i + j]
                
                with col:
                    # Imagem do produto
                    if produto.get('imagem_url'):
                        st.image(produto['imagem_url'], use_column_width=True)
                    else:
                        st.markdown('<div style="height: 180px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">🖼️ Sem imagem</div>', unsafe_allow_html=True)
                    
                    # Nome do produto (truncado)
                    nome_truncado = produto['nome'][:60] + "..." if len(produto['nome']) > 60 else produto['nome']
                    st.markdown(f"**{nome_truncado}**")
                    
                    # Preço atual
                    st.markdown(f"<div style='font-size: 24px; font-weight: 700; color: #00a650; margin: 8px 0;'>R$ {produto['preco_atual']:.2f}</div>", unsafe_allow_html=True)
                    
                    # Preço original e economia
                    if produto.get('preco_original') and produto['preco_original'] > produto['preco_atual']:
                        economia = produto['preco_original'] - produto['preco_atual']
                        st.markdown(f"<div style='font-size: 13px; color: #999; text-decoration: line-through;'>R$ {produto['preco_original']:.2f}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='background: #00a650; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; margin-top: 4px;'>💰 Economize R$ {economia:.2f}</div>", unsafe_allow_html=True)
                    
                    # Botão de link
                    st.markdown(f"<a href='{produto['link']}' target='_blank' style='display: block; text-align: center; background: #3483fa; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; margin-top: 12px; font-weight: 500;'>Ver Produto</a>", unsafe_allow_html=True)
                    
                    # Expandir para ver histórico
                    with st.expander("📊 Ver histórico de preços"):
                        stats = db.obter_estatisticas_produto(produto["id"])
                        if stats:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Mínimo", f"R$ {stats['preco_minimo']:.2f}")
                            with col2:
                                st.metric("Máximo", f"R$ {stats['preco_maximo']:.2f}")
                            
                            historico = db.obter_historico_preco(produto["id"], 30)
                            if historico:
                                df = pd.DataFrame(historico)
                                fig = px.line(
                                    df,
                                    x="data",
                                    y="preco",
                                    labels={"preco": "Preço (R$)", "data": "Data"},
                                    markers=True
                                )
                                fig.update_layout(height=250, showlegend=False)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("---")

else:
    st.info("Nenhum produto encontrado com esses critérios.")

st.markdown("---")

# ========== FOOTER ==========
st.markdown(
    """
    <hr>
    <p style='text-align: center; color: gray; font-size: 0.8rem;'>
        ML Crawler © 2024 | Dashboard em desenvolvimento | 
        <a href="https://github.com/Ysrial/ml-crawler">GitHub</a>
    </p>
    """,
    unsafe_allow_html=True
)
