import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. BANCO DE DADOS: HVL (Half-Value Layer) em cm
# =============================================================================
# HVL (Camada Semirredutora): Espessura necessária para reduzir a radiação em 50%.
# Fonte: NCRP Report No. 49 / IAEA Safety Series
# Unidade: Centímetros (cm)

DADOS_BLINDAGEM = {
    "Cobalto-60 (Co-60)": {
        "gama_const": 13.0, # mSv/h a 1m por Ci
        "energia_desc": "Alta Energia (1.17 e 1.33 MeV)",
        "HVL": {
            "Chumbo (Pb)": 1.25,
            "Aço / Ferro": 2.2,
            "Concreto": 6.0,
            "Água / Corpo Humano": 11.0,
            "Terra Compactada": 9.0
        }
    },
    "Césio-137 (Cs-137)": {
        "gama_const": 3.3,
        "energia_desc": "Média Energia (0.662 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.65,
            "Aço / Ferro": 1.6,
            "Concreto": 4.8,
            "Água / Corpo Humano": 10.0,
            "Terra Compactada": 7.5
        }
    },
    "Irídio-192 (Ir-192)": {
        "gama_const": 4.8,
        "energia_desc": "Média Energia (Espectro complexo ~0.38 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.55, # Aproximado para blindagem prática
            "Aço / Ferro": 1.3,
            "Concreto": 4.3,
            "Água / Corpo Humano": 9.0,
            "Terra Compactada": 7.0
        }
    },
    "Iodo-131 (I-131)": {
        "gama_const": 2.2,
        "energia_desc": "Média-Baixa Energia (0.364 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.30,
            "Aço / Ferro": 1.1,
            "Concreto": 3.5,
            "Água / Corpo Humano": 7.0,
            "Terra Compactada": 5.5
        }
    },
    "Tecnécio-99m (Tc-99m)": {
        "gama_const": 0.78,
        "energia_desc": "Baixa Energia (0.140 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.03, # Muito fino! (Folha de papel de chumbo)
            "Aço / Ferro": 0.1,
            "Concreto": 2.0,
            "Água / Corpo Humano": 4.0,
            "Terra Compactada": 3.0
        }
    },
    "Amerício-241 (Am-241)": {
        "gama_const": 0.1,
        "energia_desc": "Baixíssima Energia (0.060 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.01, # Milimétrico
            "Aço / Ferro": 0.05,
            "Concreto": 1.0,
            "Água / Corpo Humano": 2.5,
            "Terra Compactada": 2.0
        }
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================
def calcular_dose_inicial(atividade_ci, distancia_m, gama):
    """Lei do Inverso do Quadrado para achar dose sem blindagem."""
    if distancia_m <= 0: return 0.0
    # Dose = (Gamma * Atividade) / Distancia^2
    dose_mSv_h = (gama * atividade_ci) / (distancia_m ** 2)
    return dose_mSv_h

def calcular_atenuacao(dose_inicial, espessura_cm, hvl_cm):
    """
    Fórmula Exponencial: I = I0 * (1/2)^(x / HVL)
    """
    if hvl_cm <= 0: return dose_inicial
    
    num_hvls = espessura_cm / hvl_cm
    fator_reducao = 2 ** num_hvls
    dose_final = dose_inicial / fator_reducao
    
    return dose_final, num_hvls, fator_reducao

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🛡️ Calculadora de Blindagem (Shielding)")
    st.markdown("Dimensionamento de barreiras físicas para proteção radiológica.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 Engenharia de Proteção: Como funciona?", expanded=True):
        st.markdown("""
        **O Conceito de HVL (Half-Value Layer):**
        A radiação não para de uma vez. Ela é atenuada camada por camada.
        * **1 HVL:** Reduz a dose para **50%**.
        * **2 HVLs:** Reduz a dose para **25%** (metade da metade).
        * **3 HVLs:** Reduz a dose para **12.5%**.
        * **7 HVLs:** Reduz para menos de **1%**.
        
        **Exemplo Prático:** Para parar o raio gama do Cobalto-60, você precisa de **1.25 cm de Chumbo** OU **6.0 cm de Concreto** para obter o mesmo efeito (1 HVL).
        """)

    # 1. DEFINIÇÃO DA FONTE
    st.subheader("1. Fonte Emissora")
    col1, col2 = st.columns(2)
    
    with col1:
        isotopo = st.selectbox("Selecione o Isótopo", list(DADOS_BLINDAGEM.keys()))
        dados = DADOS_BLINDAGEM[isotopo]
        st.caption(f"⚡ {dados['energia_desc']}")
    
    with col2:
        atividade = st.number_input("Atividade da Fonte (Ci)", value=10.0, step=1.0, help="Intensidade da fonte.")
        distancia = st.number_input("Distância do Alvo (metros)", value=2.0, min_value=0.1, step=0.5, help="Distância entre a fonte e a pessoa protegida.")

    # Cálculo da Dose "Crua"
    dose_sem_blindagem = calcular_dose_inicial(atividade, distancia, dados['gama_const'])
    
    # Alerta visual da dose inicial
    st.markdown(f"**Taxa de Dose SEM Blindagem:**")
    cor_alerta = "red" if dose_sem_blindagem > 1 else "orange"
    st.markdown(f"<h3 style='color:{cor_alerta}'>{dose_sem_blindagem:.2f} mSv/h</h3>", unsafe_allow_html=True)
    st.write("---")

    # 2. DEFINIÇÃO DA BLINDAGEM
    st.subheader("2. Configuração da Barreira")
    
    c_mat, c_esp = st.columns(2)
    with c_mat:
        material = st.selectbox("Material da Barreira", list(dados['HVL'].keys()))
        hvl_atual = dados['HVL'][material]
        st.info(f"🧱 **{material}**: 1 HVL = **{hvl_atual} cm**")
        
    with c_esp:
        espessura = st.slider("Espessura da Parede (cm)", 0.0, 100.0, 5.0, step=0.5)

    # CÁLCULO FINAL
    dose_final, num_hvls, fator = calcular_atenuacao(dose_sem_blindagem, espessura, hvl_atual)
    
    # 3. RESULTADOS E ANÁLISE
    st.markdown("### 📊 Resultado da Proteção")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Dose Final (Com Barreira)", f"{dose_final:.4f} mSv/h", f"-{((1-1/fator)*100):.1f}%")
    col_res2.metric("Camadas HVL", f"{num_hvls:.1f}", help="Quantas vezes a dose foi dividida por 2.")
    col_res3.metric("Fator de Atenuação", f"1 / {int(fator)}", help="Quantas vezes a radiação foi reduzida.")

    # Diagnóstico de Segurança
    limite_publico = 0.0005 # 0.5 µSv/h (Aprox. fundo natural + margem)
    limite_trabalhador = 0.02 # 20 µSv/h (Zona Controlada)
    
    if dose_final < limite_publico:
        st.success("✅ **SEGURO PARA PÚBLICO GERAL:** Dose indistinguível do fundo natural.")
    elif dose_final < limite_trabalhador:
        st.warning("⚠️ **ZONA CONTROLADA:** Seguro apenas para trabalhadores monitorados (Radiação ocupacional).")
    else:
        st.error("🚨 **PERIGO:** Blindagem insuficiente! A dose ainda é alta para permanência.")

    # 4. GRÁFICO INTERATIVO
    st.subheader("📉 Curva de Atenuação")
    
    # Gerar dados para o gráfico (de 0 até 2x a espessura selecionada ou pelo menos 50cm)
    range_max = max(espessura * 1.5, 20.0)
    x_cm = np.linspace(0, range_max, 50)
    y_dose = [calcular_atenuacao(dose_sem_blindagem, x, hvl_atual)[0] for x in x_cm]
    
    df_chart = pd.DataFrame({'Espessura (cm)': x_cm, 'Dose (mSv/h)': y_dose})
    
    chart = alt.Chart(df_chart).mark_line(color='#00FF00', size=3).encode(
        x='Espessura (cm)',
        y='Dose (mSv/h)',
        tooltip=['Espessura (cm)', 'Dose (mSv/h)']
    ).properties(height=300)
    
    # Linha vertical marcando a escolha do usuário
    rule = alt.Chart(pd.DataFrame({'x': [espessura]})).mark_rule(color='red', strokeDash=[5,5]).encode(x='x')
    
    # Texto na linha
    text = alt.Chart(pd.DataFrame({'x': [espessura], 'y': [dose_final], 't': [f'Sua Blindagem ({espessura}cm)']})).mark_text(
        align='left', dx=5, dy=-5, color='red'
    ).encode(x='x', y='y', text='t')

    st.altair_chart(chart + rule + text, use_container_width=True)