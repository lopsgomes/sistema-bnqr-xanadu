import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. FUNÇÕES MATEMÁTICAS (TEORIA DAS FILAS M/M/s)
# =============================================================================
def calcular_probabilidade_espera(s, rho):
    """
    Cálculo simplificado da probabilidade de um paciente encontrar todos os leitos ocupados.
    Baseado na fórmula de Erlang-C.
    """
    if rho >= 1: return 1.0
    # Aproximação para sistemas de saúde em emergência
    pw = (rho ** s) / (math.factorial(s) * (1 - rho))
    divisor = sum([(rho ** n) / math.factorial(n) for n in range(s)]) + pw
    return min(pw / divisor, 1.0)

def simular_fila_hospitalar(taxa_chegada, cap_atendimento, num_leitos):
    # rho = taxa de ocupação do sistema
    rho = taxa_chegada / (num_leitos * cap_atendimento)
    
    if rho >= 1:
        return {
            "status": "🚨 COLAPSO TOTAL",
            "ocupacao": rho,
            "espera_min": float('inf'),
            "prob_espera": 100.0
        }
    
    # Tempo médio na fila (Wq) em horas
    pw = calcular_probabilidade_espera(num_leitos, rho * num_leitos / num_leitos) # Simplificação tática
    espera_horas = (pw / (num_leitos * cap_atendimento - taxa_chegada))
    
    return {
        "status": "✅ OPERACIONAL" if rho < 0.8 else "⚠️ SATURAÇÃO IMINENTE",
        "ocupacao": rho,
        "espera_min": espera_horas * 60,
        "prob_espera": pw * 100
    }

# =============================================================================
# 2. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🚑 Gestão de Colapso Hospitalar")
    st.markdown("Simulação de fluxo de vítimas e saturação da infraestrutura de saúde.")
    st.markdown("---")

    with st.expander("📖 Entendendo a Logística de Saúde em Desastres", expanded=False):
        st.markdown("""
        **Modelo M/M/s:**
        - **Taxa de Chegada ($\lambda$):** Vítimas que chegam do local do desastre por hora.
        - **Capacidade ($\mu$):** Quantas vítimas cada leito/equipe atende por hora.
        - **Leitos ($s$):** Capacidade instalada total.
        
        O colapso ocorre quando a taxa de chegada supera a capacidade de saída, criando uma fila que cresce exponencialmente.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Entrada de Vítimas")
        taxa_vimas = st.number_input("Vítimas chegando por hora", min_value=1, value=20, help="Dado vindo da Triagem/Campo")
        tempo_atendimento = st.slider("Tempo médio de atendimento (minutos)", 10, 120, 30)
        # Converte tempo em capacidade por hora (mu)
        cap_mu = 60 / tempo_atendimento

    with col2:
        st.subheader("🏥 Capacidade Local")
        leitos_disponiveis = st.number_input("Número de Leitos/Equipes", min_value=1, value=10)
        reserva_emergencia = st.checkbox("Considerar reserva de contingência (+20%)")
        
        if reserva_emergencia:
            leitos_disponiveis = int(leitos_disponiveis * 1.2)

    # --- PROCESSAMENTO ---
    resultado = simular_fila_hospitalar(taxa_vimas, cap_mu, leitos_disponiveis)

    st.markdown("---")

    # --- DASHBOARD DE RESULTADOS ---
    st.subheader(f"Status do Sistema: {resultado['status']}")
    
    m1, m2, m3 = st.columns(3)
    
    # Cor do indicador de ocupação
    cor_delta = "normal" if resultado['ocupacao'] < 0.8 else "inverse"
    
    m1.metric("Ocupação dos Leitos", f"{resultado['ocupacao']*100:.1f}%", delta=f"{resultado['status']}", delta_color=cor_delta)
    
    espera = f"{resultado['espera_min']:.1f} min" if resultado['espera_min'] != float('inf') else "Indeterminado"
    m2.metric("Tempo de Espera Fila", espera)
    
    m3.metric("Probabilidade de Fila", f"{resultado['prob_espera']:.1f}%")

    # --- GRÁFICO DE PROJEÇÃO ---
    st.markdown("#### 📈 Projeção de Saturação (Próximas 6 Horas)")
    
    horas = np.arange(0, 7, 1)
    # Simulação simples de acúmulo de fila
    vimas_acumuladas = [max(0, (taxa_vimas - (leitos_disponiveis * cap_mu)) * h) for h in horas]
    
    df_projecao = pd.DataFrame({
        'Horas após o Início': horas,
        'Pacientes Aguardando': vimas_acumuladas
    })
    
    chart = alt.Chart(df_projecao).mark_line(point=True, color='red' if resultado['ocupacao'] >= 1 else 'orange').encode(
        x='Horas após o Início',
        y='Pacientes Aguardando',
        tooltip=['Horas após o Início', 'Pacientes Aguardando']
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)

    # --- ALERTAS DE COMANDO ---
    if resultado['ocupacao'] >= 1.0:
        st.error("""
            **🚨 ALERTA CRÍTICO DE COLAPSO:** A taxa de chegada excede a capacidade de processamento. 
            - Acione IMEDIATAMENTE o protocolo de transbordo regional.
            - Converta áreas de triagem em leitos de observação.
            - Reavalie critérios de triagem (Protocolo de Catástrofe).
        """)
    elif resultado['ocupacao'] >= 0.8:
        st.warning("""
            **⚠️ RISCO DE SATURAÇÃO:** O sistema está operando próximo ao limite. Pequenas oscilações causarão filas longas.
            - Considere suspender cirurgias eletivas.
            - Prepare equipes extras de plantão.
        """)
    else:
        st.success("✅ **SISTEMA RESILIENTE:** A infraestrutura atual suporta o fluxo de vítimas.")

