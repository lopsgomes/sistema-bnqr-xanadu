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
        "gama_const": 13.0,  # mSv/h a 1m por Ci
        "energia_desc": "Alta Energia (1.17 e 1.33 MeV)",
        "HVL": {
            "Chumbo (Pb)": 1.25,
            "Tungstênio (W)": 0.95,
            "Urânio Depletado (DU)": 0.85,
            "Bismuto (Bi)": 1.15,
            "Aço / Ferro": 2.2,
            "Aço Inoxidável": 2.3,
            "Concreto": 6.0,
            "Concreto com Bário": 5.2,
            "Gesso": 7.5,
            "Tijolo": 7.8,
            "Água / Corpo Humano": 11.0,
            "Terra Compactada": 9.0,
            "Terra Úmida": 8.5,
            "Alumínio": 4.8,
            "Grafite": 5.5,
            "Madeira (Pinho)": 18.0,
            "Vidro Chumbo": 1.3,
            "Ferro Fundido": 2.0,
            "Cobre": 1.8,
            "Latão": 1.9,
            "Bronze": 1.95,
            "Aço Carbono": 2.1,
            "Concreto Pesado (Magnetita)": 4.5,
            "Terra Seca": 9.5,
            "Areia Compactada": 8.8,
            "Estanho (Sn)": 0.95,
            "Cádmio": 0.85,
            "Lítio": 12.0,
            "Bário": 1.1
        }
    },
    "Césio-137 (Cs-137)": {
        "gama_const": 3.3,
        "energia_desc": "Média Energia (0.662 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.65,
            "Tungstênio (W)": 0.50,
            "Urânio Depletado (DU)": 0.45,
            "Bismuto (Bi)": 0.60,
            "Aço / Ferro": 1.6,
            "Aço Inoxidável": 1.7,
            "Concreto": 4.8,
            "Concreto com Bário": 4.2,
            "Gesso": 6.0,
            "Tijolo": 6.2,
            "Água / Corpo Humano": 10.0,
            "Terra Compactada": 7.5,
            "Terra Úmida": 7.0,
            "Alumínio": 3.5,
            "Grafite": 4.0,
            "Madeira (Pinho)": 15.0,
            "Vidro Chumbo": 0.68,
            "Ferro Fundido": 1.5,
            "Cobre": 1.3,
            "Latão": 1.4,
            "Bronze": 1.45,
            "Aço Carbono": 1.55,
            "Concreto Pesado (Magnetita)": 3.8,
            "Terra Seca": 8.0,
            "Areia Compactada": 7.5,
            "Estanho (Sn)": 0.50,
            "Cádmio": 0.45,
            "Lítio": 10.0,
            "Bário": 0.55
        }
    },
    "Irídio-192 (Ir-192)": {
        "gama_const": 4.8,
        "energia_desc": "Média Energia (Espectro complexo ~0.38 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.55,
            "Tungstênio (W)": 0.42,
            "Urânio Depletado (DU)": 0.38,
            "Bismuto (Bi)": 0.52,
            "Aço / Ferro": 1.3,
            "Aço Inoxidável": 1.4,
            "Concreto": 4.3,
            "Concreto com Bário": 3.8,
            "Gesso": 5.5,
            "Tijolo": 5.7,
            "Água / Corpo Humano": 9.0,
            "Terra Compactada": 7.0,
            "Terra Úmida": 6.5,
            "Alumínio": 3.0,
            "Grafite": 3.5,
            "Madeira (Pinho)": 14.0,
            "Vidro Chumbo": 0.58,
            "Ferro Fundido": 1.2,
            "Cobre": 1.1,
            "Latão": 1.15,
            "Bronze": 1.18,
            "Aço Carbono": 1.25,
            "Concreto Pesado (Magnetita)": 3.2,
            "Terra Seca": 7.2,
            "Areia Compactada": 6.8,
            "Estanho (Sn)": 0.42,
            "Cádmio": 0.38,
            "Lítio": 9.0,
            "Bário": 0.48
        }
    },
    "Iodo-131 (I-131)": {
        "gama_const": 2.2,
        "energia_desc": "Média-Baixa Energia (0.364 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.30,
            "Tungstênio (W)": 0.23,
            "Urânio Depletado (DU)": 0.21,
            "Bismuto (Bi)": 0.28,
            "Aço / Ferro": 1.1,
            "Aço Inoxidável": 1.2,
            "Concreto": 3.5,
            "Concreto com Bário": 3.0,
            "Gesso": 4.5,
            "Tijolo": 4.7,
            "Água / Corpo Humano": 7.0,
            "Terra Compactada": 5.5,
            "Terra Úmida": 5.0,
            "Alumínio": 2.5,
            "Grafite": 2.8,
            "Madeira (Pinho)": 12.0,
            "Vidro Chumbo": 0.32,
            "Ferro Fundido": 1.0,
            "Cobre": 0.9,
            "Latão": 0.95,
            "Bronze": 0.98,
            "Aço Carbono": 1.05,
            "Concreto Pesado (Magnetita)": 2.5,
            "Terra Seca": 6.0,
            "Areia Compactada": 5.5,
            "Estanho (Sn)": 0.28,
            "Cádmio": 0.25,
            "Lítio": 7.5,
            "Bário": 0.30
        }
    },
    "Tecnécio-99m (Tc-99m)": {
        "gama_const": 0.78,
        "energia_desc": "Baixa Energia (0.140 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.03,
            "Tungstênio (W)": 0.025,
            "Urânio Depletado (DU)": 0.022,
            "Bismuto (Bi)": 0.028,
            "Aço / Ferro": 0.1,
            "Aço Inoxidável": 0.11,
            "Concreto": 2.0,
            "Concreto com Bário": 1.7,
            "Gesso": 2.5,
            "Tijolo": 2.6,
            "Água / Corpo Humano": 4.0,
            "Terra Compactada": 3.0,
            "Terra Úmida": 2.8,
            "Alumínio": 1.5,
            "Grafite": 1.8,
            "Madeira (Pinho)": 8.0,
            "Vidro Chumbo": 0.032,
            "Ferro Fundido": 0.08,
            "Cobre": 0.07,
            "Latão": 0.075,
            "Bronze": 0.078,
            "Aço Carbono": 0.085,
            "Concreto Pesado (Magnetita)": 1.5,
            "Terra Seca": 2.8,
            "Areia Compactada": 2.6,
            "Estanho (Sn)": 0.025,
            "Cádmio": 0.022,
            "Lítio": 4.5,
            "Bário": 0.028
        }
    },
    "Amerício-241 (Am-241)": {
        "gama_const": 0.1,
        "energia_desc": "Baixíssima Energia (0.060 MeV)",
        "HVL": {
            "Chumbo (Pb)": 0.01,
            "Tungstênio (W)": 0.008,
            "Urânio Depletado (DU)": 0.007,
            "Bismuto (Bi)": 0.009,
            "Aço / Ferro": 0.05,
            "Aço Inoxidável": 0.055,
            "Concreto": 1.0,
            "Concreto com Bário": 0.85,
            "Gesso": 1.3,
            "Tijolo": 1.4,
            "Água / Corpo Humano": 2.5,
            "Terra Compactada": 2.0,
            "Terra Úmida": 1.8,
            "Alumínio": 0.7,
            "Grafite": 0.8,
            "Madeira (Pinho)": 5.0,
            "Vidro Chumbo": 0.011,
            "Ferro Fundido": 0.04,
            "Cobre": 0.035,
            "Latão": 0.038,
            "Bronze": 0.040,
            "Aço Carbono": 0.045,
            "Concreto Pesado (Magnetita)": 0.75,
            "Terra Seca": 1.8,
            "Areia Compactada": 1.6,
            "Estanho (Sn)": 0.009,
            "Cádmio": 0.008,
            "Lítio": 3.0,
            "Bário": 0.010
        }
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================
def calcular_dose_inicial(atividade_ci, distancia_m, gama):
    """
    Calcula a taxa de dose inicial usando a Lei do Inverso do Quadrado.
    
    Parâmetros:
        atividade_ci: Atividade da fonte em Curie (Ci)
        distancia_m: Distância da fonte ao ponto de interesse (m)
        gama: Constante gama do isótopo (mSv/h a 1m por Ci)
    
    Retorna:
        Taxa de dose em mSv/h sem blindagem
    """
    if distancia_m <= 0:
        return 0.0
    # Lei do Inverso do Quadrado: Dose = (Gamma × Atividade) / Distância²
    dose_mSv_h = (gama * atividade_ci) / (distancia_m ** 2)
    return dose_mSv_h

def calcular_atenuacao(dose_inicial, espessura_cm, hvl_cm):
    """
    Calcula a atenuação da radiação gama através de uma barreira usando a lei exponencial.
    
    Fórmula: I = I₀ × (1/2)^(x / HVL)
    Onde:
        I = dose final após blindagem
        I₀ = dose inicial sem blindagem
        x = espessura da blindagem
        HVL = Half-Value Layer (camada semirredutora)
    
    Parâmetros:
        dose_inicial: Taxa de dose inicial em mSv/h
        espessura_cm: Espessura da blindagem em centímetros
        hvl_cm: Half-Value Layer do material em centímetros
    
    Retorna:
        Tupla: (dose_final, num_hvls, fator_reducao)
        - dose_final: Taxa de dose após blindagem (mSv/h)
        - num_hvls: Número de camadas semirredutoras
        - fator_reducao: Fator pelo qual a dose foi reduzida
    """
    if hvl_cm <= 0:
        return dose_inicial, 0, 1.0
    
    num_hvls = espessura_cm / hvl_cm
    fator_reducao = 2 ** num_hvls
    dose_final = dose_inicial / fator_reducao
    
    return dose_final, num_hvls, fator_reducao

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Barreiras de Proteção")
    st.markdown("**Calculadora de Blindagem Radiológica: Dimensionamento de Barreiras Físicas**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Blindagem Radiológica", expanded=True):
        st.markdown("""
        **O Conceito de HVL (Half-Value Layer - Camada Semirredutora):**
        
        A radiação gama não é completamente bloqueada por uma barreira, mas sim atenuada exponencialmente 
        à medida que atravessa o material. A HVL é a espessura de material necessária para reduzir a 
        intensidade da radiação pela metade.
        
        **Princípio de Atenuação:**
        
        - **1 HVL:** Reduz a dose para 50% do valor inicial
        - **2 HVLs:** Reduz a dose para 25% (50% de 50%)
        - **3 HVLs:** Reduz a dose para 12.5%
        - **4 HVLs:** Reduz a dose para 6.25%
        - **7 HVLs:** Reduz para menos de 1% (0.78%)
        - **10 HVLs:** Reduz para aproximadamente 0.1%
        
        **Fórmula Matemática:**
        
        A atenuação segue uma lei exponencial: **I = I₀ × (1/2)^(x / HVL)**
        
        Onde:
        - I = intensidade final após blindagem
        - I₀ = intensidade inicial sem blindagem
        - x = espessura da blindagem
        - HVL = Half-Value Layer do material
        
        **Exemplo Prático:**
        
        Para o Cobalto-60 (alta energia), são necessários:
        - **1.25 cm de Chumbo** OU
        - **6.0 cm de Concreto** OU
        - **11.0 cm de Água**
        
        para reduzir a dose pela metade (1 HVL). Cada material tem uma eficiência diferente baseada em 
        sua densidade e número atômico.
        
        **Fatores que Influenciam a Eficiência da Blindagem:**
        
        1. **Densidade:** Materiais mais densos (chumbo, tungstênio) são mais eficientes
        2. **Número Atômico (Z):** Elementos com Z alto absorvem melhor radiação gama
        3. **Energia da Radiação:** Radiação de alta energia requer blindagem mais espessa
        4. **Espessura:** A atenuação é exponencial - cada HVL adicional dobra a proteção
        
        **Limitações do Modelo:**
        
        Este modelo assume atenuação exponencial simples e não considera:
        - Efeitos de build-up (acúmulo de radiação espalhada)
        - Geometria complexa da fonte e blindagem
        - Múltiplas camadas de materiais diferentes
        - Radiação secundária (bremsstrahlung, raios X característicos)
        """)

    # 1. DEFINIÇÃO DA FONTE
    st.subheader("Parâmetros da Fonte Radioativa")
    col1, col2 = st.columns(2)
    
    with col1:
        isotopo = st.selectbox("Isótopo Radioativo", list(DADOS_BLINDAGEM.keys()))
        dados = DADOS_BLINDAGEM[isotopo]
        st.info(f"**{isotopo}**\n\n**Energia:** {dados['energia_desc']}\n\n"
               f"**Constante Gama:** {dados['gama_const']} mSv/h a 1m por Ci")
    
    with col2:
        atividade = st.number_input("Atividade da Fonte (Ci)", value=10.0, min_value=0.001, step=1.0, 
                                   help="Atividade da fonte radioativa em Curie (Ci). 1 Ci = 3.7×10¹⁰ Bq.")
        distancia = st.number_input("Distância da Fonte ao Alvo (m)", value=2.0, min_value=0.1, step=0.1, 
                                   help="Distância entre a fonte radioativa e o ponto onde se deseja calcular a dose.")

    # Cálculo da Dose Inicial
    dose_sem_blindagem = calcular_dose_inicial(atividade, distancia, dados['gama_const'])
    
    # Exibição da dose inicial
    st.markdown("### Taxa de Dose Sem Blindagem")
    if dose_sem_blindagem > 1.0:
        cor_alerta = "#e74c3c"  # Vermelho
        nivel = "MUITO ALTA"
    elif dose_sem_blindagem > 0.02:
        cor_alerta = "#f39c12"  # Laranja
        nivel = "ALTA"
    else:
        cor_alerta = "#2ecc71"  # Verde
        nivel = "MODERADA"
    
    st.markdown(f"<h3 style='color:{cor_alerta}'>{dose_sem_blindagem:.4f} mSv/h ({nivel})</h3>", unsafe_allow_html=True)
    st.caption(f"Calculada usando a Lei do Inverso do Quadrado: Dose = (Γ × Atividade) / Distância²")
    st.markdown("---")

    # 2. DEFINIÇÃO DA BLINDAGEM
    st.subheader("Configuração da Barreira de Proteção")
    
    c_mat, c_esp = st.columns(2)
    with c_mat:
        material = st.selectbox("Material da Barreira", list(dados['HVL'].keys()))
        hvl_atual = dados['HVL'][material]
        st.info(f"**{material}**\n\n**Half-Value Layer (HVL):** {hvl_atual} cm\n\n"
               f"Esta é a espessura necessária para reduzir a radiação pela metade.")
        
    with c_esp:
        espessura = st.slider("Espessura da Barreira (cm)", 0.0, 200.0, 5.0, step=0.1,
                             help="Espessura total da barreira de proteção em centímetros.")
        
        # Calcular número de HVLs para a espessura selecionada
        if hvl_atual > 0:
            num_hvls_estimado = espessura / hvl_atual
            st.caption(f"Espessura equivalente a {num_hvls_estimado:.2f} camadas semirredutoras (HVL)")

    # CÁLCULO FINAL
    dose_final, num_hvls, fator = calcular_atenuacao(dose_sem_blindagem, espessura, hvl_atual)
    
    # 3. RESULTADOS E ANÁLISE
    st.markdown("---")
    st.markdown("### Resultados da Análise de Blindagem")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    reducao_percentual = ((1 - 1/fator) * 100) if fator > 0 else 0
    col_res1.metric("Dose Final (Com Barreira)", f"{dose_final:.6f} mSv/h", 
                   f"Redução de {reducao_percentual:.1f}%", delta_color="inverse")
    col_res2.metric("Camadas HVL", f"{num_hvls:.2f}", 
                   "Número de camadas semirredutoras", help="Quantas vezes a dose foi dividida por 2")
    if fator < 1000000:
        col_res3.metric("Fator de Atenuação", f"1 / {int(fator):,}", 
                       f"{fator:.2e} vezes menor")
    else:
        col_res3.metric("Fator de Atenuação", f"1 / {fator:.2e}", 
                       "Redução extremamente alta")

    # Diagnóstico de Segurança
    limite_publico = 0.0005  # 0.5 µSv/h (aproximadamente fundo natural + margem de segurança)
    limite_trabalhador = 0.02  # 20 µSv/h (limite para zona controlada - trabalhadores monitorados)
    
    st.markdown("---")
    st.markdown("#### Classificação de Segurança")
    
    if dose_final < limite_publico:
        st.success("**SEGURO PARA PÚBLICO GERAL:** A taxa de dose está abaixo de 0.5 µSv/h, "
                  "indistinguível do fundo natural de radiação. Não há necessidade de restrições de acesso.")
    elif dose_final < limite_trabalhador:
        st.warning("**ZONA CONTROLADA:** A taxa de dose está entre 0.5 µSv/h e 20 µSv/h. "
                  "Esta área requer controle de acesso e monitoramento de trabalhadores. "
                  "Apenas pessoal autorizado e monitorado pode permanecer nesta área.")
    else:
        st.error("**PERIGO - BLINDAGEM INSUFICIENTE:** A taxa de dose ainda é alta (acima de 20 µSv/h). "
                "A blindagem atual não é adequada para permanência prolongada. "
                "Aumente a espessura da barreira ou use material mais eficiente.")

    # 4. GRÁFICO INTERATIVO
    st.markdown("---")
    st.markdown("#### Curva de Atenuação")
    st.caption("Gráfico mostrando como a taxa de dose diminui exponencialmente com o aumento da espessura da blindagem.")
    
    # Gerar dados para o gráfico (de 0 até 2x a espessura selecionada ou pelo menos 50cm)
    range_max = max(espessura * 2.0, 50.0)
    x_cm = np.linspace(0, range_max, 100)
    y_dose = [calcular_atenuacao(dose_sem_blindagem, x, hvl_atual)[0] for x in x_cm]
    
    df_chart = pd.DataFrame({'Espessura (cm)': x_cm, 'Dose (mSv/h)': y_dose})
    
    # Gráfico principal
    chart = alt.Chart(df_chart).mark_line(color='#2ecc71', size=2).encode(
        x=alt.X('Espessura (cm)', title='Espessura da Blindagem (cm)'),
        y=alt.Y('Dose (mSv/h)', title='Taxa de Dose (mSv/h)', scale=alt.Scale(type='log')),
        tooltip=[alt.Tooltip('Espessura (cm)', format='.2f'),
                 alt.Tooltip('Dose (mSv/h)', format='.6f')]
    ).properties(height=400, title='Atenuação da Radiação em Função da Espessura da Blindagem')
    
    # Linha vertical marcando a escolha do usuário
    rule = alt.Chart(pd.DataFrame({'x': [espessura]})).mark_rule(
        color='#e74c3c', strokeDash=[5, 5], strokeWidth=2
    ).encode(x='x')
    
    # Ponto marcando a dose final
    point = alt.Chart(pd.DataFrame({'x': [espessura], 'y': [dose_final]})).mark_circle(
        color='#e74c3c', size=100
    ).encode(x='x', y='y')
    
    # Texto na linha
    text = alt.Chart(pd.DataFrame({
        'x': [espessura], 
        'y': [dose_final], 
        't': [f'Blindagem Selecionada: {espessura:.1f} cm\nDose: {dose_final:.6f} mSv/h']
    })).mark_text(
        align='left', dx=10, dy=-10, color='#e74c3c', fontSize=12, fontWeight='bold'
    ).encode(x='x', y='y', text='t')
    
    # Linhas de referência para limites de segurança
    limite_publico_line = alt.Chart(pd.DataFrame({'y': [limite_publico]})).mark_rule(
        color='#2ecc71', strokeDash=[3, 3], strokeWidth=1, opacity=0.7
    ).encode(y='y')
    
    limite_trabalhador_line = alt.Chart(pd.DataFrame({'y': [limite_trabalhador]})).mark_rule(
        color='#f39c12', strokeDash=[3, 3], strokeWidth=1, opacity=0.7
    ).encode(y='y')
    
    st.altair_chart(chart + limite_publico_line + limite_trabalhador_line + rule + point + text, use_container_width=True)
    
    # Legenda
    st.caption("**Legenda:** Linha verde tracejada = Limite para público geral (0.5 µSv/h). "
              "Linha laranja tracejada = Limite para zona controlada (20 µSv/h). "
              "Escala logarítmica no eixo Y para melhor visualização da atenuação exponencial.")
    
    # Tabela de referência rápida
    with st.expander("Tabela de Referência: Espessuras para Diferentes Níveis de Proteção", expanded=False):
        st.markdown(f"""
        **Para {isotopo} usando {material} (HVL = {hvl_atual} cm):**
        
        | Nível de Proteção | Camadas HVL | Espessura (cm) | Fator de Redução |
        |-------------------|-------------|----------------|------------------|
        | 50% (1 HVL) | 1.0 | {hvl_atual:.2f} | 2× |
        | 75% (2 HVL) | 2.0 | {hvl_atual*2:.2f} | 4× |
        | 87.5% (3 HVL) | 3.0 | {hvl_atual*3:.2f} | 8× |
        | 93.75% (4 HVL) | 4.0 | {hvl_atual*4:.2f} | 16× |
        | 96.875% (5 HVL) | 5.0 | {hvl_atual*5:.2f} | 32× |
        | 99.9% (10 HVL) | 10.0 | {hvl_atual*10:.2f} | 1024× |
        
        **Nota:** Para reduzir a dose para menos de 0.5 µSv/h (limite público), geralmente são necessárias 
        entre 7-10 camadas HVL, dependendo da dose inicial.
        """)
    
    # Recomendações operacionais
    st.markdown("---")
    with st.expander("Recomendações Operacionais e Considerações de Projeto", expanded=False):
        st.markdown(f"""
        **Cenário Analisado:**
        - **Isótopo:** {isotopo}
        - **Atividade:** {atividade:.1f} Ci
        - **Distância:** {distancia:.1f} m
        - **Material de Blindagem:** {material}
        - **Espessura:** {espessura:.1f} cm
        - **Dose Sem Blindagem:** {dose_sem_blindagem:.6f} mSv/h
        - **Dose Com Blindagem:** {dose_final:.6f} mSv/h
        - **Redução:** {reducao_percentual:.1f}%
        
        **Recomendações de Projeto:**
        
        1. **Seleção de Material:**
           - Materiais de alta densidade (chumbo, tungstênio, urânio depletado) oferecem melhor proteção 
             por unidade de espessura, mas são mais caros e pesados.
           - Concreto é uma opção econômica para blindagem permanente, mas requer maior espessura.
           - Para blindagem temporária ou portátil, chumbo ou tungstênio são preferíveis.
        
        2. **Espessura Mínima Recomendada:**
           - Para zona controlada (trabalhadores): A dose deve estar abaixo de 20 µSv/h (0.02 mSv/h)
           - Para público geral: A dose deve estar abaixo de 0.5 µSv/h (0.0005 mSv/h)
           - A espessura atual de {espessura:.1f} cm fornece {num_hvls:.2f} camadas HVL
        
        3. **Considerações Práticas:**
           - **Peso:** Materiais densos podem ser muito pesados. Considere a capacidade estrutural do suporte.
           - **Custo:** Chumbo é relativamente barato, tungstênio é muito caro, concreto é econômico.
           - **Disponibilidade:** Em emergências, concreto ou terra podem ser mais facilmente disponíveis.
           - **Mobilidade:** Para blindagem portátil, chumbo ou tungstênio são preferíveis.
        
        4. **Blindagem Composta:**
           - Em alguns casos, combinar materiais pode ser mais eficaz (ex: chumbo + concreto para reduzir 
             custo e peso mantendo proteção adequada).
           - Materiais de baixo número atômico (polietileno, água) são eficazes para nêutrons, mas 
             requerem camada externa de material pesado para gama.
        
        5. **Verificação e Validação:**
           - Sempre valide o dimensionamento com medições de campo usando detectores apropriados.
           - Considere margem de segurança de 10-20% na espessura calculada.
           - Verifique se não há frestas, juntas ou aberturas que comprometam a blindagem.
        
        6. **Manutenção:**
           - Verifique periodicamente a integridade da blindagem.
           - Materiais podem sofrer degradação (concreto pode rachar, chumbo pode se deformar).
           - Mantenha registros de inspeção e medições de dose.
        
        **Limitações Importantes:**
        
        Este modelo assume atenuação exponencial simples e não considera:
        - Efeitos de build-up (acúmulo de radiação espalhada) que podem aumentar a dose em até 2-3 vezes
        - Geometria complexa da fonte e blindagem
        - Múltiplas camadas de materiais diferentes
        - Radiação secundária (bremsstrahlung de elétrons, raios X característicos)
        - Radiação de nêutrons (requer blindagem diferente)
        
        Para projetos críticos, consulte um físico de radioproteção qualificado e utilize software 
        especializado (ex: MicroShield, MCNP) para cálculos mais precisos.
        """)