import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. REFERÊNCIAS DE DENSIDADE (Pessoas por km²)
# =============================================================================
DENSIDADES = {
    "Área Rural / Industrial Isolada": 50,
    "Subúrbio / Residencial Baixo": 2500,
    "Urbano Denso (Centro da Cidade)": 8000,
    "Evento de Massa (Estádio/Show)": 25000,
    "Personalizado (Inserir Manualmente)": 0
}

# =============================================================================
# 2. MOTOR DE CÁLCULO ESTATÍSTICO (LÓGICA DE TRIAGEM)
# =============================================================================
def calcular_triage(populacao_exposta, gravidade_incidente):
    """
    Distribui a população exposta nas categorias START (Vermelho, Amarelo, Verde, Preto)
    baseado na gravidade do incidente (0.1 a 1.0).
    """
    # Lógica de distribuição estatística:
    # À medida que a gravidade sobe, a mortalidade (Preto) e casos críticos (Vermelho) sobem.
    f_preto = (gravidade_incidente ** 2.5) * 0.7  # Curva acelerada para óbitos
    f_vermelho = (gravidade_incidente ** 1.5) * 0.3
    f_amarelo = (1 - gravidade_incidente) * 0.4
    
    # O restante são os 'verdes' (feridos leves que conseguem caminhar)
    soma_criticos = f_preto + f_vermelho + f_amarelo
    f_verde = max(0, 1.0 - soma_criticos)
    
    vitimas = {
        "🔴 Vermelho (Imediato)": int(populacao_exposta * f_vermelho),
        "🟡 Amarelo (Retardado)": int(populacao_exposta * f_amarelo),
        "🟢 Verde (Leve)": int(populacao_exposta * f_verde),
        "⚫ Preto (Expectante/Óbito)": int(populacao_exposta * f_preto)
    }
    
    return vitimas

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🚑 Estimativa de Vítimas (Triage)")
    st.markdown("Cálculo de impacto populacional e necessidade de recursos médicos.")
    st.markdown("---")

    with st.expander("📖 Como funciona a estimativa?", expanded=True):
        st.markdown("""
        **Passo 1:** Calculamos a área da zona de risco (em $km^2$).  
        **Passo 2:** Multiplicamos pela densidade populacional local para achar o total de expostos.  
        **Passo 3:** Aplicamos a triagem **START** para prever a gravidade dos ferimentos baseada na 'Dose' recebida.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 1. População no Local")
        tipo_area = st.selectbox("Tipo de Ocupação da Área", list(DENSIDADES.keys()))
        
        if tipo_area == "Personalizado (Inserir Manualmente)":
            densidade_ref = st.number_input("Densidade (Pessoas/km²)", value=1000)
        else:
            densidade_ref = DENSIDADES[tipo_area]
            st.info(f"Referência: {densidade_ref} pessoas por $km^2$")

        area_afetada_m2 = st.number_input("Área da Zona de Risco ($m^2$)", value=50000, step=5000)
        area_km2 = area_afetada_m2 / 1_000_000
        
        total_expostos = int(area_km2 * densidade_ref)
        st.metric("Total de Pessoas Expostas", f"{total_expostos} pessoas")

    with col2:
        st.subheader("🔥 2. Severidade do Impacto")
        st.markdown("**Intensidade do Agente (Dose/Pressão)**")
        
        # Slider didático
        nivel_perigo = st.slider("Ajuste a intensidade observada", 0.0, 1.0, 0.5)

        # GUIA DIDÁTICO DINÂMICO DA SEVERIDADE
        if nivel_perigo <= 0.2:
            st.success("🟢 **Impacto Leve:** Odor perceptível, irritação ocular leve. Maioria das vítimas será 'Verde'.")
        elif nivel_perigo <= 0.5:
            st.warning("🟡 **Impacto Moderado:** Dificuldade respiratória, tontura ou danos estruturais leves (vidros).")
        elif nivel_perigo <= 0.8:
            st.error("🟠 **Impacto Grave:** Perda de consciência, queimaduras químicas severas ou colapso de paredes.")
        else:
            st.error("💀 **Impacto Catastrófico:** Ground Zero. Alta probabilidade de óbitos imediatos por trauma ou asfixia.")

        st.write("---")
        if st.button("📊 Gerar Relatório de Vítimas", type="primary", use_container_width=True):
            st.session_state['triage_calc'] = True

    if st.session_state.get('triage_calc'):
        resultado = calcular_triage(total_expostos, nivel_perigo)
        
        st.markdown("### 📋 Estimativa de Triagem START")
        
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Vermelhos", resultado["🔴 Vermelho (Imediato)"])
        c2.metric("🟡 Amarelos", resultado["🟡 Amarelo (Retardado)"])
        c3.metric("🟢 Verdes", resultado["🟢 Verde (Leve)"])
        c4.metric("⚫ Pretos", resultado["⚫ Preto (Expectante/Óbito)"])

        # Gráfico de Distribuição
        df_triage = pd.DataFrame({
            'Categoria': list(resultado.keys()),
            'Quantidade': list(resultado.values()),
            'Cor': ['#FF0000', '#FFD700', '#008000', '#000000']
        })

        chart = alt.Chart(df_triage).mark_bar().encode(
            x=alt.X('Quantidade:Q', title="Número de Vítimas"),
            y=alt.Y('Categoria:N', sort=None, title=None),
            color=alt.Color('Cor:N', scale=None),
            tooltip=['Categoria', 'Quantidade']
        ).properties(height=250)
        
        st.altair_chart(chart, use_container_width=True)

        # Logística de Resgate
        st.subheader("🚒 Necessidade de Recursos Médicos")
        
        usa = math.ceil(resultado["🔴 Vermelho (Imediato)"] / 2)
        usb = math.ceil(resultado["🟡 Amarelo (Retardado)"] / 5)
        
        col_log1, col_log2 = st.columns(2)
        with col_log1:
            st.write(f"🚑 **Ambulâncias UTI (USA):** {usa}")
            st.write(f"🚑 **Ambulâncias Básicas (USB):** {usb}")
        with col_log2:
            st.write(f"🏥 **Vagas de UTI Estimadas:** {resultado['🔴 Vermelho (Imediato)']}")
            st.write(f"📦 **Kits de Triagem/Óbito:** {total_expostos}")

        if resultado["🔴 Vermelho (Imediato)"] > 20:
            st.error("🚨 **ALERTA DE DESASTRE:** Capacidade hospitalar local provavelmente excedida. Acione ajuda mútua.")