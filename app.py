st.markdown("---")
    st.markdown("### 🔥 Top 10 — Maiores Variações do Último Pregão (Call vs Put)")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**Maiores Variações Financeiras (Call = Positivo / Put = Negativo)**")
        if 'Variacao_Financeira' in df_ultimo.columns and not df_ultimo['Variacao_Financeira'].isna().all():
            df_val_limpo = df_ultimo.dropna(subset=['Variacao_Financeira']).copy()
            
            # Se a coluna 'Tipo' existir, inverte o sinal das Puts visualmente para irem para o lado esquerdo (negativo)
            if 'Tipo' in df_val_limpo.columns:
                # Normaliza para maiúsculo para evitar erro de digitação (ex: 'CALL', 'PUT', 'Call', 'Put')
                df_val_limpo['Tipo_Upper'] = df_val_limpo['Tipo'].astype(str).str.upper()
                df_val_limpo['Variacao_Grafico'] = np.where(
                    df_val_limpo['Tipo_Upper'].str.contains('PUT'),
                    -abs(df_val_limpo['Variacao_Financeira']),
                    abs(df_val_limpo['Variacao_Financeira'])
                )
            else:
                df_val_limpo['Variacao_Grafico'] = df_val_limpo['Variacao_Financeira']
                
            # Pega as 5 maiores e as 5 menores para balancear o gráfico dos dois lados do zero
            top_neg = df_val_limpo.nsmallest(5, 'Variacao_Grafico')
            top_pos = df_val_limpo.nlargest(5, 'Variacao_Grafico')
            top10_fin = pd.concat([top_neg, top_pos]).drop_duplicates().sort_values(by='Variacao_Grafico', ascending=True)
            
            fig_fin = px.bar(
                top10_fin,
                x='Variacao_Grafico',
                y='Ativo_Formatado',
                orientation='h',
                text='Variacao_Financeira', # Mostra o valor real original no rótulo
                color='Variacao_Grafico',
                color_continuous_scale='RdBu',
                labels={'Variacao_Grafico': 'Variação Direcional (R$)', 'Ativo_Formatado': 'Ativo'}
            )
            fig_fin.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            fig_fin.update_layout(
                margin=dict(l=20, r=100, t=30, b=20),
                xaxis=dict(zeroline=True, zerolinewidth=3, zerolinecolor='black')
            )
            st.plotly_chart(fig_fin, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a variação financeira.")
            
    with col_t2:
        st.markdown("**Maiores Variações Percentuais (Call vs Put)**")
        if 'Variacao_Percentual' in df_ultimo.columns and not df_ultimo['Variacao_Percentual'].isna().all():
            df_pct_limpo = df_ultimo.dropna(subset=['Variacao_Percentual']).copy()
            
            if 'Tipo' in df_pct_limpo.columns:
                df_pct_limpo['Tipo_Upper'] = df_pct_limpo['Tipo'].astype(str).str.upper()
                df_pct_limpo['Percentual_Grafico'] = np.where(
                    df_pct_limpo['Tipo_Upper'].str.contains('PUT'),
                    -abs(df_pct_limpo['Variacao_Percentual']),
                    abs(df_pct_limpo['Variacao_Percentual'])
                )
            else:
                df_pct_limpo['Percentual_Grafico'] = df_pct_limpo['Variacao_Percentual']
                
            top_neg_pct = df_pct_limpo.nsmallest(5, 'Percentual_Grafico')
            top_pos_pct = df_pct_limpo.nlargest(5, 'Percentual_Grafico')
            top10_pct = pd.concat([top_neg_pct, top_pos_pct]).drop_duplicates().sort_values(by='Percentual_Grafico', ascending=True)
            
            fig_pct = px.bar(
                top10_pct,
                x='Percentual_Grafico',
                y='Ativo_Formatado',
                orientation='h',
                text='Variacao_Percentual', # Mantém o texto percentual real
                color='Percentual_Grafico',
                color_continuous_scale='Greens',
                labels={'Percentual_Grafico': 'Variação Direcional (%)', 'Ativo_Formatado': 'Ativo'}
            )
            fig_pct.update_traces(texttemplate='%{text:,.2f}%', textposition='outside')
            fig_pct.update_layout(
                margin=dict(l=20, r=100, t=30, b=20),
                xaxis=dict(zeroline=True, zerolinewidth=3, zerolinecolor='black')
            )
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a variação percentual.")
