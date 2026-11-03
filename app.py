import streamlit as st
import pandas as pd
import gspread
from google.auth import default
import plotly.express as px

st.set_page_config(page_title="Monitor B3", layout="wide")

st.title("?? Monitor B3 — Painel de Análise")

# --- DICIONÁRIO DE USUÁRIOS E PLANILHAS ---
# Aqui você gerencia facilmente os 2 ou 3 usuários e os IDs das planilhas deles
usuarios_planilhas = {
    "Eduardo (Principal)": "1tEjT52xO9lzoBdPE4rXKJyqowM_9Fi3x5bWc2oRw3eI",
    "Usuário 2": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_2_AQUI",
    "Usuário 3": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_3_AQUI"
}

st.sidebar.header("?? Identificação")
nome_usuario = st.sidebar.selectbox("Selecione o Usuário:", list(usuarios_planilhas.keys()))
id_planilha = usuarios_planilhas[nome_usuario]

# Função para carregar e tratar os dados da planilha do usuário selecionado
@st.cache_data(ttl=300)
def carregar_dados(sheet_id):
    auth, _ = default()
    cliente = gspread.authorize(auth)
    planilha = cliente.open_by_key(sheet_id)
    aba = planilha.worksheet("HISTORICO_B3")
    df = pd.DataFrame(aba.get_all_records())
    
    # Tratamento de colunas financeiras
    colunas_financeiras = ['Valor_Coberto', 'Valor_Descoberto', 'Exercicio']
    for col in colunas_financeiras:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)\
                                         .str.replace('.', '', regex=False)\
                                         .str.replace(',', '.', regex=False)\
                                         .str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
            
    # Garantir ordenação por código e data
    df = df.sort_values(by=['Codigo', 'Data_Pregao'])
    
    # Cálculo da variação diária (D x D-1)
    df['Variacao_Coberto'] = df.groupby('Codigo')['Valor_Coberto'].diff().round(2)
    return df

try:
    df = carregar_dados(id_planilha)
    st.sidebar.success(f"Base carregada para: {nome_usuario}")
    
    # --- FILTROS ---
    st.sidebar.subheader("Filtros")
    codigos_disponiveis = df['Codigo'].unique().tolist()
    opcao_selecionada = st.sidebar.selectbox("Selecione a Opção/Ativo:", codigos_disponiveis)
    
    # Filtrar dados para o código selecionado
    df_filtrado = df[df['Codigo'] == opcao_selecionada]
    
    # --- VISUALIZAÇÃO PRINCIPAL ---
    col1, col2, col3 = st.columns(3)
    
    ultimo_registro = df_filtrado.iloc[-1] if not df_filtrado.empty else None
    if ultimo_registro is not None:
        col1.metric("Último Valor Coberto", f"R$ {ultimo_registro['Valor_Coberto']:.2f}")
        col2.metric("Variação (D x D-1)", f"R$ {ultimo_registro['Variacao_Coberto']:.2f}")
        if 'Exercicio' in df_filtrado.columns:
            col3.metric("Preço de Exercício (Strike)", f"R$ {ultimo_registro['Exercicio']:.2f}")

    st.markdown("---")
    
    # --- GRÁFICO DE HISTÓRICO COM VALOR DO ATIVO ---
    st.subheader(f"Evolução Temporal — {opcao_selecionada}")
    
    fig_historico = px.line(
        df_filtrado, 
        x='Data_Pregao', 
        y=['Valor_Coberto', 'Exercicio'],
        labels={'value': 'Valor (R$)', 'Data_Pregao': 'Data do Pregão', 'variable': 'Métrica'},
        title=f"Histórico de Valor Coberto vs. Preço de Exercício",
        markers=True
    )
    st.plotly_chart(fig_historico, use_container_width=True)
    
    # --- GRÁFICO TOP 10 ---
    st.subheader("?? Top 10 Opções por Valor Coberto (Último Pregão)")
    
    ultima_data = df['Data_Pregao'].max()
    df_ultimo_pregao = df[df['Data_Pregao'] == ultima_data]
    
    top10_opcoes = df_ultimo_pregao.nlargest(10, 'Valor_Coberto')
    
    fig_top10 = px.bar(
        top10_opcoes,
        x='Codigo',
        y='Valor_Coberto',
        text='Valor_Coberto',
        color='Valor_Coberto',
        color_continuous_scale='Viridis',
        labels={'Valor_Coberto': 'Valor Coberto (R$)', 'Codigo': 'Código da Opção'},
        title=f"Top 10 Opções mais movimentadas no Pregão de {ultima_data}"
    )
    fig_top10.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    st.plotly_chart(fig_top10, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar e processar a planilha: {e}")
