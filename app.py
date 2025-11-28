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

# Tema e estilos personalizados
st.markdown("""
    <style>
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    
    /* Cards de produtos */
    .product-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        height: 100%;
        border: 1px solid #e0e0e0;
    }
    
    .product-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .product-image {
        width: 100%;
        height: 200px;
        object-fit: contain;
        border-radius: 8px;
        background: #f8f9fa;
        padding: 10px;
    }
    
    .product-name {
        font-size: 0.95rem;
        font-weight: 500;
        color: #333;
        margin: 12px 0;
        min-height: 48px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .price-current {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00a650;
        margin: 8px 0;
    }
    
    .price-original {
        font-size: 0.9rem;
        color: #999;
        text-decoration: line-through;
        margin-bottom: 4px;
    }
    
    .discount-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00a650 0%, #00b359 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .product-link {
        display: inline-block;
        background: #3483fa;
        color: white !important;
        padding: 10px 20px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 500;
        text-align: center;
        width: 100%;
        margin-top: 12px;
        transition: background 0.2s;
    }
    
    .product-link:hover {
        background: #2968c8;
        text-decoration: none;
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
    
    dias_historico = st.slider(
        "Histórico de dias",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )
    
    st.markdown("---")
    st.info(
        "💡 **Dica:** Acompanhe as variações de preço ao longo do tempo "
        "para identificar as melhores oportunidades de compra!"
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
        st.info(f"✅ {coleta['total_produtos']} produtos processados na coleta")
    with col3:
        st.info(f"🔄 Status: {coleta['status'].upper()}")

st.markdown("---")

# ========== GRID DE PRODUTOS EM CARDS ==========
st.markdown("## 🛍️ Produtos Monitorados")

# Filtro e busca
col1, col2 = st.columns([3, 1])

with col1:
    busca = st.text_input("🔍 Buscar produto", "")

with col2:
    limite = st.slider("Mostrar", 6, 48, 12, step=6)

# Filtrar produtos
if busca:
    produtos_filtrados = [
        p for p in produtos 
        if busca.lower() in p["nome"].lower()
    ]
else:
    produtos_filtrados = produtos[:limite]

# Exibir produtos em grid de cards
if produtos_filtrados:
    # Criar grid de 3 colunas
    num_cols = 3
    rows = [produtos_filtrados[i:i+num_cols] for i in range(0, len(produtos_filtrados), num_cols)]
    
    for row in rows:
        cols = st.columns(num_cols)
        
        for idx, produto in enumerate(row):
            with cols[idx]:
                # Card HTML
                imagem_url = produto.get('imagem_url', '')
                nome = produto['nome'][:80]
                preco_atual = produto['preco_atual']
                preco_original = produto.get('preco_original')
                percentual_desconto = produto.get('percentual_desconto')
                link = produto['link']
                
                # Construir HTML do card
                card_html = f"""
                <div class="product-card">
                    <img src="{imagem_url}" class="product-image" onerror="this.src='https://via.placeholder.com/200x200?text=Sem+Imagem'">
                    <div class="product-name">{nome}</div>
                """
                
                # Badge de desconto (mostrar valor em reais)
                if preco_original and preco_original > preco_atual:
                    desconto_reais = preco_original - preco_atual
                    card_html += f'<div class="discount-badge">R$ {desconto_reais:.0f} OFF</div>'
                
                # Preço original (se houver desconto)
                if preco_original and preco_original > preco_atual:
                    card_html += f'<div class="price-original">De R$ {preco_original:.2f}</div>'

                
                # Preço atual
                card_html += f'<div class="price-current">R$ {preco_atual:.2f}</div>'
                
                # Link para o produto
                card_html += f"""
                    <a href="{link}" target="_blank" class="product-link">Ver no Mercado Livre</a>
                </div>
                """
                
                st.markdown(card_html, unsafe_allow_html=True)

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
