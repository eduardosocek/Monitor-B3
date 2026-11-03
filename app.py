import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Monitor B3", layout="wide")

# --- CONTROLE DE SENHA SIMPLES (SOLUÇÃO DE ACESSO TEMPORÁRIO) ---
st.sidebar.header("🔐 Segurança de Acesso")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
SENHA_MESTRE = "monitor123"  # Você pode alterar esta senha quando quiser!

if senha_digitada != SENHA_MESTRE:
    st.info("📌 **SA INTELIGÊNCIA EM DADOS | B3 MONITOR**")
    st.warning("⚠️ **Acesso Restrito:** Por favor, digite a senha correta na barra lateral para carregar o painel.")
    st.stop()  # Interrompe a execução até que a senha seja inserida corretamente

st.sidebar.success("✅ Acesso Liberado!")

# --- DICIONÁRIO DE USUÁRIOS E PLANILHAS ---
usuarios_planilhas = {
    "Eduardo (Principal)": "1tEjT52xO9lzoBdPE4rXKJyqowM_9Fi3x5bWc2oRw3eI",
    "Usuário 2": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_2_AQUI",
    "Usuário 3": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_3_AQUI"
}

st.sidebar.header("👤 Identificação")
nome_usuario = st.sidebar.selectbox("Selecione o Usuário:", list(usuarios_planilhas.keys()))
id_planilha = usuarios_planilhas[nome_usuario]

# Função para carregar e calcular os dados do Google Sheets de forma segura
@st.cache_data(ttl=300)
def carregar_e_processar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=HISTORICO_B3"
    df = pd.read_csv(url)
    
    # Limpar espaços em branco nos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Tratamento de colunas numéricas / financeiras
    colunas_para_tratar = ['Valor_Coberto', 'Valor_Descoberto', 'Exercicio']
    for col in colunas_para_tratar:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)\
                                         .str.replace('.', '', regex=False)\
                                         .str.replace(',', '.', regex=False)\
                                         .str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
            
    # Garantir ordenação cronológica por código e data
    if 'Data_Pregao' in df.columns and 'Codigo' in df.columns:
        df['Data_Pregao'] = pd.to_datetime(df['Data_Pregao'], errors='coerce')
        df = df.sort_values(by=['Codigo', 'Data_Pregao'])
        
        col_base = 'Valor_Descoberto' if 'Valor_Descoberto' in df.columns else 'Valor_Coberto'
        if col_base in df.columns:
            # 1. Variação Financeira (D x D-1) com suporte a valores negativos/positivos
            df['Variacao_Financeira'] = df.groupby('Codigo')[col_base].diff().round(2)
            
            # 2. Variação Percentual tratada para evitar divisão por zero e estouros
            val_anterior = df.groupby('Codigo')[col_base].shift(1)
            dif = df['Variacao_Financeira']
            pct = np.where((val_anterior <= 0.1) | (val_anterior.isna()), 0, (dif / val_anterior) * 100)
            df['Variacao_Percentual'] = pd.Series(pct, index=df.index).round(2)
            
    return df

try:
    df = carregar_e_processar_dados(id_planilha)
    st.sidebar.success(f"Base carregada para: {nome_usuario}")
    
    # --- CABEÇALHO PADRÃO STREAMLIT ---
    st.info("📌 **SA INTELIGÊNCIA EM DADOS | B3 MONITOR**")
    
    ultima_data = df['Data_Pregao'].max().strftime('%d/%m/%Y') if 'Data_Pregao' in df.columns and not df['Data_Pregao'].isna().all() else "N/A"
    total_pregoes = df['Data_Pregao'].nunique() if 'Data_Pregao' in df.columns else 0
    
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Último Pregão", str(ultima_data))
    col_h2.metric("Pregões Carregados", str(total_pregoes))
    col_h3.metric("Status", "Atualizado com sucesso")
    
    st.markdown("---")
    
    # --- CRIAR RÓTULO PERSONALIZADO (Ex: PETRA1 (R$ 15,00)) ---
    if 'Codigo' in df.columns and 'Exercicio' in df.columns:
        df_ultimos_ativos = df.drop_duplicates(subset=['Codigo'], keep='last')
        mapa_rotulos = {
            row['Codigo']: f"{row['Codigo']} (R$ {row['Exercicio']:,.2f})"
            for _, row in df_ultimos_ativos.iterrows()
        }
        df['Ativo_Formatado'] = df['Codigo'].map(mapa_rotulos)
    else:
        df['Ativo_Formatado'] = df['Codigo']
        
    # --- FILTRO / SELETOR DE ATIVO PRINCIPAL ---
    lista_opcoes = df['Ativo_Formatado'].unique().tolist() if 'Ativo_Formatado' in df.columns else []
    
    st.sidebar.subheader("Filtro de Ativo")
    opcao_selecionada = st.sidebar.selectbox("Selecione a Opção / Ativo:", lista_opcoes)
    
    df_filtrado = df[df['Ativo_Formatado'] == opcao_selecionada] if 'Ativo_Formatado' in df.columns else pd.DataFrame()
    
    # --- CARTÕES / MÉTRICAS DO ATIVO SELECIONADO ---
    st.subheader(f"📊 Painel do Ativo Selecionado: {opcao_selecionada}")
    
    if not df_filtrado.empty:
        ultimo_registro = df_filtrado.iloc[-1]
        
        val_coberto = ultimo_registro.get('Valor_Coberto', 0)
        val_descoberto = ultimo_registro.get('Valor_Descoberto', 0)
        exercicio = ultimo_registro.get('Exercicio', 0)
        data_ref = ultimo_registro.get('Data_Pregao')
        data_ref_str = data_ref.strftime('%d/%m/%Y') if pd.notna(data_ref) else 'N/A'
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Valor Coberto", f"R$ {val_coberto:,.2f}" if pd.notna(val_coberto) else "R$ 0,00")
        c2.metric("Valor Descoberto", f"R$ {val_descoberto:,.2f}" if pd.notna(val_descoberto) else "R$ 0,00")
        c3.metric("Preço de Exercício (Strike)", f"R$ {exercicio:,.2f}" if pd.notna(exercicio) else "R$ 0,00")
        c4.metric("Data Ref.", data_ref_str)
        
        # Gráfico de Evolução Temporal (Apenas Valor Descoberto e Strike)
        if 'Data_Pregao' in df_filtrado.columns:
            colunas_grafico = [c for c in ['Valor_Descoberto', 'Exercicio'] if c in df_filtrado.columns]
            fig_evolucao = px.line(
                df_filtrado,
                x='Data_Pregao',
                y=colunas_grafico,
                markers=True,
                title=f"Evolução Temporal (Valor Descoberto e Strike) — {opcao_selecionada}",
                labels={'value': 'Valor (R$)', 'Data_Pregao': 'Data do Pregão', 'variable': 'Métrica'}
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
    st.markdown("---")
    
    # --- EVOLUÇÃO TEMPORAL — TOP 10 VALOR DESCOBERTO ---
    st.subheader("📈 Evolução Temporal — Top 10 Maiores Valores Descobertos")
    
    max_dt = df['Data_Pregao'].max()
    df_ultimo = df[df['Data_Pregao'] == max_dt] if 'Data_Pregao' in df.columns else df
    
    if 'Valor_Descoberto' in df_ultimo.columns:
        top10_codigos = df_ultimo.nlargest(10, 'Valor_Descoberto')['Codigo'].tolist()
        df_top10_temporal = df[df['Codigo'].isin(top10_codigos)]
        
        fig_top10_desc = px.line(
            df_top10_temporal,
            x='Data_Pregao',
            y='Valor_Descoberto',
            color='Ativo_Formatado',
            markers=True,
            title="Evolução Temporal do Valor Descoberto — Top 10 Ativos",
            labels={'Valor_Descoberto': 'Valor Descoberto (R$)', 'Data_Pregao': 'Data do Pregão', 'Ativo_Formatado': 'Ativo'}
        )
        st.plotly_chart(fig_top10_desc, use_container_width=True)

    st.markdown("---")
    
    # --- TOP 10 DESTAQUES (BARRAS HORIZONTAIS) ---
    st.subheader("🔥 Top 10 — Maiores Variações do Último Pregão")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**Maiores Variações Financeiras (Top 10)**")
        if 'Variacao_Financeira' in df_ultimo.columns and not df_ultimo['Variacao_Financeira'].isna().all():
            top10_fin = df_ultimo.dropna(subset=['Variacao_Financeira']).sort_values(by='Variacao_Financeira', ascending=True).tail(10)
            
            fig_fin = px.bar(
                top10_fin,
                x='Variacao_Financeira',
                y='Ativo_Formatado',
                orientation='h',
                text='Variacao_Financeira',
                color='Variacao_Financeira',
                color_continuous_scale='RdBu',
                labels={'Variacao_Financeira': 'Variação (R$)', 'Ativo_Formatado': 'Ativo'}
            )
            fig_fin.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            st.plotly_chart(fig_fin, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a variação financeira.")
            
    with col_t2:
        st.markdown("**Maiores Variações Percentuais (Top 10)**")
        if 'Variacao_Percentual' in df_ultimo.columns and not df_ultimo['Variacao_Percentual'].isna().all():
            top10_pct = df_ultimo.dropna(subset=['Variacao_Percentual']).sort_values(by='Variacao_Percentual', ascending=True).tail(10)
            
            fig_pct = px.bar(
                top10_pct,
                x='Variacao_Percentual',
                y='Ativo_Formatado',
                orientation='h',
                text='Variacao_Percentual',
                color='Variacao_Percentual',
                color_continuous_scale='Greens',
                labels={'Variacao_Percentual': 'Variação (%)', 'Ativo_Formatado': 'Ativo'}
            )
            fig_pct.update_traces(texttemplate='%{text:,.2f}%', textposition='outside')
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a variação percentual.")

except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
