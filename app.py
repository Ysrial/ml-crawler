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

# ========== CARD DE STATUS DE COLETA ==========
try:
    # Buscar últimas coletas
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM coletas 
        WHERE categoria = %s 
        ORDER BY data_inicio DESC 
        LIMIT 5
    """, (categoria_selecionada,))
    coletas_recentes = cursor.fetchall()
    cursor.close()
    db.release_connection(conn)
    
    if coletas_recentes:
        # Como usamos cursor simples, convertemos para dict
        # Colunas: id, categoria, data_inicio, data_fim, total_produtos, total_novos, total_atualizados, status, mensagem_erro
        ultima_coleta_raw = coletas_recentes[0]
        ultima_coleta = {
            'id': ultima_coleta_raw[0],
            'categoria': ultima_coleta_raw[1],
            'data_inicio': ultima_coleta_raw[2],
            'data_fim': ultima_coleta_raw[3],
            'total_produtos': ultima_coleta_raw[4],
            'total_novos': ultima_coleta_raw[5] or 0,
            'total_atualizados': ultima_coleta_raw[6] or 0,
            'status': ultima_coleta_raw[7],
        }
        
        # Card de status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_icon = "✅" if ultima_coleta.get("status") == "sucesso" else "❌"
            data_str = ultima_coleta['data_inicio'].strftime('%d/%m/%Y %H:%M') if ultima_coleta['data_inicio'] else 'N/A'
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>{status_icon} Última Coleta</h3>
                <p style="color: gray; font-size: 0.9em;">
                    {data_str}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>📦 Novos Produtos</h3>
                <p style="font-size: 1.5em; font-weight: bold;">
                    {ultima_coleta.get('total_novos', 0)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>🔄 Atualizados</h3>
                <p style="font-size: 1.5em; font-weight: bold;">
                    {ultima_coleta.get('total_atualizados', 0)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
except Exception as e:
    st.warning(f"⚠️ Erro ao carregar status de coleta: {e}")

st.markdown("")

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

# ========== CARD DE PRODUTOS EM DESTAQUE ==========
st.markdown("## 🔥 Produtos em Destaque")

tab1, tab2 = st.tabs(["Maiores Descontos", "Maior Variação de Preço"])

with tab1:
    # Produtos com maior desconto
    try:
        produtos_desconto = sorted(
            [p for p in produtos if p.get('percentual_desconto')],
            key=lambda x: x.get('percentual_desconto', 0),
            reverse=True
        )[:3]
        
        if produtos_desconto:
            for i, produto in enumerate(produtos_desconto, 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    **{i}. {produto['nome'][:60]}...**
                    - Desconto: **{produto['percentual_desconto']:.1f}%** 🏷️
                    - De: ~~R$ {produto['preco_original']:.2f}~~ → Agora: **R$ {produto['preco_atual']:.2f}**
                    """)
                with col2:
                    st.link_button("Abrir", produto['link'], use_container_width=True)
        else:
            st.info("Nenhum produto com desconto identificado nesta categoria.")
    except Exception as e:
        st.warning(f"Erro ao carregar produtos com desconto: {e}")

with tab2:
    # Produtos com maior variação de preço
    try:
        produtos_variacao = []
        for produto in produtos:
            try:
                stats = db.obter_estatisticas_produto(produto["id"])
                if stats and stats["variacao_percentual"] != 0:
                    produtos_variacao.append({
                        "nome": produto["nome"],
                        "variacao": stats["variacao_percentual"],
                        "preco_min": stats["preco_minimo"],
                        "preco_max": stats["preco_maximo"],
                        "preco_atual": stats["preco_atual"],
                        "link": produto["link"]
                    })
            except:
                pass
        
        if produtos_variacao:
            produtos_variacao_top = sorted(
                produtos_variacao,
                key=lambda x: abs(x["variacao"]),
                reverse=True
            )[:3]
            
            for i, produto in enumerate(produtos_variacao_top, 1):
                cor = "🔴" if produto["variacao"] > 0 else "🟢"
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    **{i}. {produto['nome'][:60]}...**
                    - Variação: {cor} **{produto['variacao']:+.1f}%**
                    - Mín: R$ {produto['preco_min']:.2f} | Máx: R$ {produto['preco_max']:.2f} | Agora: R$ {produto['preco_atual']:.2f}
                    """)
                with col2:
                    st.link_button("Abrir", produto['link'], use_container_width=True)
        else:
            st.info("Sem histórico de variação de preço para esta categoria.")
    except Exception as e:
        st.warning(f"Erro ao carregar variações: {e}")

st.markdown("---")

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
            
            # Título com badge de desconto
            titulo = f"📦 {produto['nome'][:70]}"
            if produto.get('percentual_desconto'):
                titulo += f" 🏷️ {produto['percentual_desconto']:.0f}% OFF"
            
            with st.expander(titulo):
                # Layout com imagem
                if produto.get('imagem_url'):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        try:
                            st.image(produto['imagem_url'], width=120, caption="Produto")
                        except:
                            st.write("🖼️ Sem imagem")
                    info_container = col_info
                else:
                    info_container = st
                
                with info_container:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Preço atual e original
                        if produto.get('preco_original') and produto.get('percentual_desconto'):
                            st.markdown(f"**Preço Atual**")
                            st.markdown(f"# R$ {produto['preco_atual']:.2f}")
                            st.markdown(f"~~R$ {produto['preco_original']:.2f}~~")
                        else:
                            st.metric("Preço Atual", f"R$ {produto['preco_atual']:.2f}")
                    
                    with col2:
                        if stats and stats["variacao_percentual"] != 0:
                            cor = "🔴" if stats["variacao_percentual"] > 0 else "🟢"
                            st.metric(
                                "Variação Histórica",
                                f"{stats['variacao_percentual']:.1f}%",
                                help=f"Desde primeira coleta"
                            )
                        elif produto.get('percentual_desconto'):
                            st.metric(
                                "Desconto Atual",
                                f"{produto['percentual_desconto']:.1f}%",
                                help="Desconto aplicado no preço"
                            )
                        else:
                            st.metric("Variação", "0%")
                    
                    with col3:
                        if stats:
                            st.metric("Mínimo Histórico", f"R$ {stats['preco_minimo']:.2f}")
                    
                    with col4:
                        if stats:
                            st.metric("Máximo Histórico", f"R$ {stats['preco_maximo']:.2f}")
                
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
