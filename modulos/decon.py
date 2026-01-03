import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================================================================
# 1. PARÂMETROS TÁTICOS DE REFERÊNCIA
# =============================================================================
TIPOS_DECON = {
    "Descontaminação Técnica (Equipes)": {
        "tempo_medio": 10, # minutos por pessoa
        "desc": "Processo minucioso para operadores com roupas nível A/B. Requer escovação e múltiplas estações."
    },
    "Descontaminação em Massa (Público)": {
        "tempo_medio": 3, # minutos por pessoa
        "desc": "Banho rápido (chuveirinho) focado em remover o grosso do contaminante da pele e roupas."
    },
    "Vítimas Não-Ambulantes (Maca)": {
        "tempo_medio": 15, # minutos por pessoa
        "desc": "Vítimas inconscientes ou feridas. Requer 2 a 4 operadores para manipular a vítima na linha."
    }
}

# =============================================================================
# 2. MOTOR DE LOGÍSTICA (TEORIA DAS FILAS SIMPLIFICADA)
# =============================================================================
def simular_decon(num_vitimas, num_linhas, tempo_por_pessoa):
    """
    Calcula a dinâmica de processamento da descontaminação.
    """
    # Capacidade de processamento (Vítimas por hora)
    vazao_por_linha = 60 / tempo_por_pessoa
    vazao_total_hora = vazao_por_linha * num_linhas
    
    # Tempo total para limpar todo mundo (em horas)
    tempo_total_horas = num_vitimas / vazao_total_hora
    
    # Gerar dados para o gráfico de evolução
    horas = np.arange(0, tempo_total_horas + 1, 0.5)
    if horas[-1] < tempo_total_horas:
        horas = np.append(horas, tempo_total_horas)
        
    processadas = [min(num_vitimas, vazao_total_hora * h) for h in horas]
    pendentes = [num_vitimas - p for p in processadas]
    
    df_evolucao = pd.DataFrame({
        'Tempo (Horas)': horas,
        'Vítimas Processadas': processadas,
        'Vítimas na Fila (Zona Suja)': pendentes
    })
    
    return df_evolucao, vazao_total_hora, tempo_total_horas

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🚑 Logística de Descontaminação (DECON)")
    st.markdown("Dimensionamento de corredores de limpeza e tempo de resposta operacional.")
    st.markdown("---")

    with st.expander("📖 O Gargalo da Sobrevivência", expanded=True):
        st.markdown("""
        **O Desafio:** Em um incidente BNQR, a descontaminação é o "funil" da operação. 
        Se o processo for muito lento, as vítimas esperam demais na zona suja. Se for muito rápido, a limpeza pode ser ineficaz.
        
        **Cálculo Tático:** Este módulo ajuda a definir quantas **Linhas de Decon** (tendas/chuveiros) são necessárias para processar o público em um tempo aceitável.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Cenário de Vítimas")
        total_vitimas = st.number_input("Total de Vítimas Afetadas", value=100, min_value=1, step=10)
        
        tipo_alvo = st.selectbox("Perfil das Vítimas", list(TIPOS_DECON.keys()))
        tempo_base = TIPOS_DECON[tipo_alvo]['tempo_medio']
        
        st.info(f"⏱️ **Tempo estimado:** {tempo_base} min por pessoa para {tipo_alvo}.")

    with col2:
        st.subheader("2. Recursos Disponíveis")
        linhas = st.slider("Número de Linhas de Decon Ativas", 1, 10, 2, help="Cada linha é uma tenda ou corredor de banho completo.")
        
        tempo_ajustado = st.number_input("Ajuste de Tempo Manual (min/pessoa)", value=float(tempo_base), min_value=0.5, step=0.5)
        
        st.warning(f"⚙️ Capacidade do Sistema: **{ (60/tempo_ajustado)*linhas :.1f} vítimas/hora**.")

    # Botão de Ação
    if 'decon_calc' not in st.session_state: st.session_state['decon_calc'] = False
    
    if st.button("🚀 Simular Fluxo de Descontaminação", type="primary", use_container_width=True):
        st.session_state['decon_calc'] = True

    if st.session_state['decon_calc']:
        df, vazao, total_h = simular_decon(total_vitimas, linhas, tempo_ajustado)
        
        st.write("---")
        st.markdown("### 📊 Relatório de Operação")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tempo Total", f"{total_h:.1f} Horas", f"{total_h*60:.0f} min")
        m2.metric("Vazão do Sistema", f"{vazao:.0f} pessoas/h")
        m3.metric("Eficiência por Linha", f"{60/tempo_ajustado:.1f} p/h")

        # Alerta de Gestão
        if total_h > 2.0:
            st.error(f"🚨 **ALERTA DE SATURAÇÃO:** A operação levará mais de 2 horas. Muitas vítimas podem sofrer danos graves aguardando na fila. Considere dobrar o número de linhas.")
        elif total_h > 1.0:
            st.warning(f"⚠️ **OPERAÇÃO CRÍTICA:** Tempo de espera elevado. Monitore sinais vitais na fila.")
        else:
            st.success(f"✅ **FLUXO ADEQUADO:** Operação eficiente para o volume de vítimas.")

        # Gráfico de Evolução
        st.markdown("#### 📈 Evolução do Processamento")
        
        df_melt = df.melt('Tempo (Horas)', var_name='Status', value_name='Quantidade')
        
        chart = alt.Chart(df_melt).mark_area(opacity=0.6).encode(
            x='Tempo (Horas):Q',
            y=alt.Y('Quantidade:Q', stack=None),
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Vítimas Processadas', 'Vítimas na Fila (Zona Suja)'], range=['#2ecc71', '#e74c3c'])),
            tooltip=['Tempo (Horas)', 'Status', 'Quantidade']
        ).properties(height=300).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        st.caption("Nota: A área vermelha representa o acúmulo de pessoas expostas aguardando limpeza.")