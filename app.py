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
    limite = st.slider("Mostrar", 5, 50, 10)

# Filtrar produtos
if busca:
    produtos_filtrados = [
        p for p in produtos 
        if busca.lower() in p["nome"].lower()
    ]
else:
    produtos_filtrados = produtos[:limite]

# Exibir produtos
if produtos_filtrados:
    for i, produto in enumerate(produtos_filtrados):
        try:
            stats = db.obter_estatisticas_produto(produto["id"])
            
            with st.expander(f"📦 {produto['nome'][:70]}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Preço Atual", f"R$ {produto['preco_atual']:.2f}")
                
                with col2:
                    if stats and stats["variacao_percentual"] != 0:
                        cor = "🔴" if stats["variacao_percentual"] > 0 else "🟢"
                        st.metric(
                            "Variação",
                            f"{stats['variacao_percentual']:.1f}%",
                            help=f"Desde primeira coleta"
                        )
                    else:
                        st.metric("Variação", "0%")
                
                with col3:
                    if stats:
                        st.metric("Mínimo", f"R$ {stats['preco_minimo']:.2f}")
                
                with col4:
                    if stats:
                        st.metric("Máximo", f"R$ {stats['preco_maximo']:.2f}")
                
                # Histórico
                if stats:
                    historico = db.obter_historico_preco(produto["id"], dias_historico)
                    
                    if historico:
                        df = pd.DataFrame(historico)
                        
                        # Gráfico
                        fig = px.line(
                            df,
                            x="data",
                            y="preco",
                            title="Histórico de Preço",
                            labels={
                                "preco": "Preço (R$)",
                                "data": "Data"
                            },
                            markers=True
                        )
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Link do produto
                st.markdown(f"[🔗 Abrir no Mercado Livre]({produto['link']})")
        
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar dados do produto {i+1}")

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
