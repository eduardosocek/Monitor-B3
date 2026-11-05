import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Monitor B3", layout="wide")

st.title("🔐 SA INTELIGÊNCIA EM DADOS | B3 MONITOR")
st.markdown("---")

# Dicionário de planilhas
usuarios_planilhas = {
    "Eduardo (Principal)": "1tEjT52xO9lzoBdPE4rXKJyqowM_9Fi3x5bWc2oRw3eI",
    "Usuário 2": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_2_AQUI",
    "Usuário 3": "COLOQUE_O_ID_DA_PLANILHA_DO_CLIENTE_3_AQUI"
}

st.sidebar.markdown("### 👤 Configurações")
nome_usuario = st.sidebar.radio("Selecione o Usuário:", list(usuarios_planilhas.keys()))
id_planilha = usuarios_planilhas[nome_usuario]

@st.cache_data(ttl=300)
def carregar_e_processar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=HISTORICO_B3"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    
    colunas_para_tratar = ['Valor_Coberto', 'Valor_Descoberto', 'Exercicio']
    for col in colunas_para_tratar:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)\
                                         .str.replace('.', '', regex=False)\
                                         .str.replace(',', '.', regex=False)\
                                         .str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
            
    if 'Data_Pregao' in df.columns and 'Codigo' in df.columns:
        df['Data_Pregao'] = pd.to_datetime(df['Data_Pregao'], errors='coerce')
        df = df.sort_values(by=['Codigo', 'Data_Pregao'])
        
        col_base = 'Valor_Descoberto' if 'Valor_Descoberto' in df.columns else 'Valor_Coberto'
        if col_base in df.columns:
            df['Variacao_Financeira'] = df.groupby('Codigo')[col_base].diff().round(2)
            val_anterior = df.groupby('Codigo')[col_base].shift(1)
            dif = df['Variacao_Financeira']
            pct = np.where((val_anterior <= 0.1) | (val_anterior.isna()), 0, (dif / val_anterior) * 100)
            df['Variacao_Percentual'] = pd.Series(pct, index=df.index).round(2)
            
    return df

try:
    df = carregar_e_processar_dados(id_planilha)
    st.sidebar.success(f"Base carregada: {nome_usuario}")
    
    ultima_data = df['Data_Pregao'].max().strftime('%d/%m/%Y') if 'Data_Pregao' in df.columns and not df['Data_Pregao'].isna().all() else "N/A"
    total_pregoes = df['Data_Pregao'].nunique() if 'Data_Pregao' in df.columns else 0
    
    st.markdown(f"""
    > **Resumo da Base:** Último Pregão: **{ultima_data}** | Pregões Carregados: **{total_pregoes}** | Status: **Atualizado com Sucesso**
    """)
    st.markdown("---")
    
    if 'Codigo' in df.columns and 'Exercicio' in df.columns:
        df_ultimos_ativos = df.drop_duplicates(subset=['Codigo'], keep='last')
        mapa_rotulos = {
            row['Codigo']: f"{row['Codigo']} (R$ {row['Exercicio']:,.2f})"
            for _, row in df_ultimos_ativos.iterrows()
        }
        df['Ativo_Formatado'] = df['Codigo'].map(mapa_rotulos)
    else:
        df['Ativo_Formatado'] = df['Codigo']
        
    lista_opcoes = df['Ativo_Formatado'].unique().tolist() if 'Ativo_Formatado' in df.columns else []
    
    st.sidebar.markdown("### Filtro de Ativo")
    opcao_selecionada = st.sidebar.selectbox("Ativo:", lista_opcoes)
    
    df_filtrado = df[df['Ativo_Formatado'] == opcao_selecionada] if 'Ativo_Formatado' in df.columns else pd.DataFrame()
    
    st.markdown(f"### 📊 Painel do Ativo Selecionado: {opcao_selecionada}")
    
    if not df_filtrado.empty:
        ultimo_registro = df_filtrado.iloc[-1]
        val_coberto = ultimo_registro.get('Valor_Coberto', 0)
        val_descoberto = ultimo_registro.get('Valor_Descoberto', 0)
        exercicio = ultimo_registro.get('Exercicio', 0)
        data_ref = ultimo_registro.get('Data_Pregao')
        data_ref_str = data_ref.strftime('%d/%m/%Y') if pd.notna(data_ref) else 'N/A'
        
        st.markdown(f"""
        | Valor Coberto | Valor Descoberto | Preço de Exercício (Strike) | Data Ref. |
        | :--- | :--- | :--- | :--- |
        | R$ {val_coberto:,.2f} | R$ {val_descoberto:,.2f} | R$ {exercicio:,.2f} | {data_ref_str} |
        """)
        
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
            # Ajuste de layout para evitar cortes nas margens e centralizar o zero se necessário
            fig_evolucao.update_layout(margin=dict(l=20, r=20, t=50, b=20), xaxis_title="Data do Pregão", yaxis_title="Valor (R$)")
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
    st.markdown("---")
    st.markdown("### 📈 Evolução Temporal — Top 10 Maiores Valores Descobertos")
    
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
        fig_top10_desc.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_top10_desc, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔥 Top 10 — Maiores Variações do Último Pregão (Call / Put)")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**Maiores Variações Financeiras (Top 10)**")
        if 'Variacao_Financeira' in df_ultimo.columns and not df_ultimo['Variacao_Financeira'].isna().all():
            top10_fin = df_ultimo.dropna(subset=['Variacao_Financeira']).sort_values(by='Variacao_Financeira', ascending=True).tail(10)
            
            # Gráfico com barras direcionadas (positivo para cima/direita, negativo para baixo/esquerda, garantindo o zero no centro)
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
            # Força o texto para fora/dentro sem cortar e garante margens seguras
            fig_fin.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            fig_fin.update_layout(
                margin=dict(l=20, r=80, t=30, b=20),  # Margem direita maior para o texto do gráfico não cortar
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray') # Garante o zero bem visível no centro
            )
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
            fig_pct.update_layout(
                margin=dict(l=20, r=80, t=30, b=20),
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray') # Zero centralizado
            )
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a variação percentual.")

except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
