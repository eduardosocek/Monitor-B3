import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Monitor B3", layout="wide")

# --- DICIONÁRIO DE USUÁRIOS E PLANILHAS ---
usuarios_planilhas = {
    "Eduardo (Principal)": "1tEjT52xO9lzoBdPE4rXKJyqowM_9Fi3x5bWc2oRw3eI",
    "Usuário 2": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_2_AQUI",
    "Usuário 3": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_3_AQUI"
}

st.sidebar.header("🔐 Identificação")
nome_usuario = st.sidebar.selectbox("Selecione o Usuário:", list(usuarios_planilhas.keys()))
id_planilha = usuarios_planilhas[nome_usuario]

# Função para carregar os dados públicos do Google Sheets
@st.cache_data(ttl=300)
def carregar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=HISTORICO_B3"
    df = pd.read_csv(url)
    
    # Tratamento de colunas financeiras e numéricas
    colunas_numericas = ['Valor_Coberto', 'Valor_Descoberto', 'Exercicio', 'Variacao_Financeira', 'Variacao_Percentual']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)\
                                         .str.replace('.', '', regex=False)\
                                         .str.replace(',', '.', regex=False)\
                                         .str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
            
    if 'Data_Pregao' in df.columns:
        df = df.sort_values(by=['Codigo', 'Data_Pregao'])
        
    return df

try:
    df = carregar_dados(id_planilha)
    st.sidebar.success(f"Base carregada para: {nome_usuario}")
    
    # --- CABEÇALHO ESTILO PLANILHA ---
    st.markdown("""
        <div style="background-color: #1f77b4; padding: 10px; border-radius: 5px; text-align: center; color: white; margin-bottom: 20px;">
            <h3 style="margin: 0;">SA INTELIGÊNCIA EM DADOS | B3 MONITOR</h3>
        </div>
    """, unsafe_allow_html=True)
    
    ultima_data = df['Data_Pregao'].max() if 'Data_Pregao' in df.columns else "N/A"
    total_pregoes = df['Data_Pregao'].nunique() if 'Data_Pregao' in df.columns else 0
    
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Último Pregão", str(ultima_data))
    col_h2.metric("Pregões Carregados", str(total_pregoes))
    col_h3.metric("Status", "Atualizado com sucesso")
    
    st.markdown("---")
    
    # --- FILTRO / SELETOR DE ATIVO PRINCIPAL ---
    codigos_disponiveis = df['Codigo'].unique().tolist() if 'Codigo' in df.columns else []
    
    st.sidebar.subheader("Filtro de Ativo")
    opcao_selecionada = st.sidebar.selectbox("Selecione a Opção / Ativo:", codigos_disponiveis)
    
    df_filtrado = df[df['Codigo'] == opcao_selecionada] if 'Codigo' in df.columns else pd.DataFrame()
    
    # --- CARTÕES / MÉTRICAS DO ATIVO SELECIONADO ---
    st.subheader(f"📊 Painel do Ativo: {opcao_selecionada}")
    
    if not df_filtrado.empty:
        ultimo_registro = df_filtrado.iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Valor Coberto", f"R$ {ultimo_registro.get('Valor_Coberto', 0):.2f}")
        c2.metric("Valor Descoberto", f"R$ {ultimo_registro.get('Valor_Descoberto', 0):.2f}")
        c3.metric("Preço de Exercício (Strike)", f"R$ {ultimo_registro.get('Exercicio', 0):.2f}")
        c4.metric("Data Ref.", str(ultimo_registro.get('Data_Pregao', 'N/A')))
        
        # Gráfico de Evolução Temporal (Ativo + Preço / Strike)
        if 'Data_Pregao' in df_filtrado.columns:
            fig_evolucao = px.line(
                df_filtrado,
                x='Data_Pregao',
                y=['Valor_Coberto', 'Valor_Descoberto', 'Exercicio'],
                markers=True,
                title=f"Evolução Temporal e Preços — {opcao_selecionada}",
                labels={'value': 'Valor (R$)', 'Data_Pregao': 'Data do Pregão', 'variable': 'Métrica'}
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
    st.markdown("---")
    
    # --- TOP 10 DESTAQUES (MAIORES VARIAÇÕES) ---
    st.subheader("🔥 Top 10 — Maiores Variações do Último Pregão")
    
    df_ultimo = df[df['Data_Pregao'] == ultima_data] if 'Data_Pregao' in df.columns else df
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**Maiores Variações Financeiras (Top 10)**")
        if 'Variacao_Financeira' in df_ultimo.columns:
            top10_fin = df_ultimo.nlargest(10, 'Variacao_Financeira')
            fig_fin = px.bar(
                top10_fin,
                x='Codigo',
                y='Variacao_Financeira',
                text='Variacao_Financeira',
                color='Variacao_Financeira',
                color_continuous_scale='RdBu',
                labels={'Variacao_Financeira': 'Variação (R$)', 'Codigo': 'Ativo'}
            )
            fig_fin.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
            st.plotly_chart(fig_fin, use_container_width=True)
        else:
            st.info("Coluna 'Variacao_Financeira' não encontrada na base.")
            
    with col_t2:
        st.markdown("**Maiores Variações Percentuais (Top 10)**")
        if 'Variacao_Percentual' in df_ultimo.columns:
            top10_pct = df_ultimo.nlargest(10, 'Variacao_Percentual')
            fig_pct = px.bar(
                top10_pct,
                x='Codigo',
                y='Variacao_Percentual',
                text='Variacao_Percentual',
                color='Variacao_Percentual',
                color_continuous_scale='Greens',
                labels={'Variacao_Percentual': 'Variação (%)', 'Codigo': 'Ativo'}
            )
            fig_pct.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info("Coluna 'Variacao_Percentual' não encontrada na base.")

    st.markdown("---")
    
    # --- ANÁLISE DETALHADA — TODAS AS OPÇÕES (TABELA COMPLETA) ---
    st.subheader("📋 Análise Detalhada — Todas as Opções (Tabela Completa)")
    st.markdown("Acompanhe abaixo a consolidação completa de todos os ativos e comparativos por data.")
    
    # Exibe a tabela interativa completa com ordenação e busca
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar e processar os dados: {e}")
