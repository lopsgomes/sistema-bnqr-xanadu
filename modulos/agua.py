import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================================================================
# 1. BANCO DE DADOS: AGENTES DE CONTAMINAÇÃO HÍDRICA
# =============================================================================
# LD50 (Lethal Dose 50%): Dose que mata 50% da população (mg/kg de peso corporal).
# Limite Potável: Baseado em CONAMA / OMS (mg/L).
CONTAMINANTES_AGUA = {
    "Aldicarb (Chumbinho)": {
        "tipo": "Químico (Pesticida)",
        "LD50": 0.9, 
        "limite_potavel": 0.01,
        "desc": "Carbamato ilegal muito comum no Brasil. Bloqueia a colinesterase. Extremamente letal."
    },
    "Arsênio (Trióxido)": {
        "tipo": "Químico",
        "LD50": 14.0, 
        "limite_potavel": 0.01,
        "desc": "Veneno insípido e inodoro. Usado historicamente para envenenamento em massa."
    },
    "Bário (Cloreto Solúvel)": {
        "tipo": "Químico",
        "LD50": 118.0, 
        "limite_potavel": 0.7,
        "desc": "Afeta o coração (arritmias) e músculos. Sais de bário são muito solúveis."
    },
    "Cádmio": {
        "tipo": "Químico (Metal Pesado)",
        "LD50": 225.0, 
        "limite_potavel": 0.005,
        "desc": "Altamente tóxico para os rins. Intoxicação aguda causa vômitos severos e choque."
    },
    "Césio-137 (Solúvel - Cloreto)": {
        "tipo": "Radiológico",
        "LD50": 1000.0, # (Risco radiológico preponderante sobre o químico)
        "limite_potavel": 0.0, 
        "desc": "Se dissolvido, quem bebe se torna radioativo internamente. Danos celulares massivos."
    },
    "Cianeto de Potássio": {
        "tipo": "Químico",
        "LD50": 2.5, 
        "limite_potavel": 0.07,
        "desc": "O veneno clássico. Bloqueia a respiração celular. Solúvel e invisível na água."
    },
    "Cloro (Superdosagem)": {
        "tipo": "Químico",
        "LD50": 850.0, # (Hipoclorito concentrado)
        "limite_potavel": 5.0,
        "desc": "Sabotagem operacional (despejar o tanque de tratamento puro). Queimaduras internas severas."
    },
    "Dioxina (TCDD)": {
        "tipo": "Químico",
        "LD50": 0.02, # Extremamente potente
        "limite_potavel": 0.00000003,
        "desc": "O veneno do Agente Laranja. Causa cloracne e falência hepática aguda em altas doses."
    },
    "Estricnina": {
        "tipo": "Químico",
        "LD50": 2.0, 
        "limite_potavel": 0.0,
        "desc": "Pesticida antigo. Causa convulsões violentas (tetania). Gosto muito amargo."
    },
    "Fentanil": {
        "tipo": "Opioide Sintético",
        "LD50": 0.03, 
        "limite_potavel": 0.0,
        "desc": "Ameaça moderna. 50x mais forte que heroína. Parada respiratória imediata."
    },
    "Fluoroacetato de Sódio (1080)": {
        "tipo": "Químico",
        "LD50": 2.0, 
        "limite_potavel": 0.0,
        "desc": "Rodenticida inodoro e insípido. Bloqueia o ciclo de Krebs. Sem antídoto eficaz."
    },
    "Flúor (Excesso)": {
        "tipo": "Químico",
        "LD50": 50.0, 
        "limite_potavel": 1.5,
        "desc": "Sabotagem em estações de tratamento. Ocorre se o sistema de fluoretação for manipulado."
    },
    "LSD (Alucinógeno)": {
        "tipo": "Psicotrópico",
        "LD50": 100.0, 
        "limite_potavel": 0.0,
        "desc": "Cenário de desorganização social. Não mata, mas incapacita a população com alucinações."
    },
    "Mercúrio (Orgânico/Metil)": {
        "tipo": "Químico",
        "LD50": 25.0, 
        "limite_potavel": 0.001,
        "desc": "Dano neurológico severo. Bioacumulativo, mas em ataque agudo causa falência renal."
    },
    "Nicotina (Pura)": {
        "tipo": "Químico",
        "LD50": 6.5, 
        "limite_potavel": 0.0,
        "desc": "Extraída de tabaco. Paralisia respiratória rápida. Gosto amargo e picante."
    },
    "Paraquat": {
        "tipo": "Herbicida",
        "LD50": 35.0, 
        "limite_potavel": 0.01,
        "desc": "Causa fibrose pulmonar irreversível dias após a ingestão. Morte lenta e dolorosa."
    },
    "Polônio-210": {
        "tipo": "Radiológico",
        "LD50": 0.00005, # 50 nanogramas (Estimativa)
        "limite_potavel": 0.0,
        "desc": "O veneno do espião (Litvinenko). Emissor Alfa massivo. Destrói o corpo por dentro."
    },
    "Ricina (Toxina)": {
        "tipo": "Biotoxina",
        "LD50": 0.02, # Ingestão
        "limite_potavel": 0.0001,
        "desc": "Toxina da mamona. Causa falência de órgãos e hemorragia gástrica severa."
    },
    "Saxitoxina": {
        "tipo": "Biotoxina (Marinha)",
        "LD50": 0.01, 
        "limite_potavel": 0.000003,
        "desc": "Veneno da maré vermelha. Paralisia muscular imediata. Resistente à fervura."
    },
    "Tálio (Sulfato)": {
        "tipo": "Químico",
        "LD50": 12.0, 
        "limite_potavel": 0.002,
        "desc": "O 'Veneno dos Envenenadores'. Insípido. Causa queda de cabelo e dor excruciante."
    },
    "Tetrodotoxina (TTX)": {
        "tipo": "Biotoxina (Baiacu)",
        "LD50": 0.33, 
        "limite_potavel": 0.0,
        "desc": "Bloqueador de canal de sódio. A vítima fica paralisada consciente até morrer."
    },
    "Toxina Botulínica A": {
        "tipo": "Biotoxina",
        "LD50": 0.000001, 
        "limite_potavel": 0.0000001,
        "desc": "A substância mais tóxica conhecida. Uma grama poderia contaminar um reservatório inteiro."
    },
    "Varfarina (Superdosagem)": {
        "tipo": "Químico",
        "LD50": 180.0, 
        "limite_potavel": 0.03,
        "desc": "Anticoagulante (Veneno de rato). Doses massivas causam hemorragia interna espontânea."
    },
    "VX (Agente de Guerra)": {
        "tipo": "Químico (Neurotóxico)",
        "LD50": 0.005, 
        "limite_potavel": 0.0,
        "desc": "Persistente em água fria e pH neutro. Letalidade extrema em doses minúsculas."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (DILUIÇÃO E TOXICOLOGIA)
# =============================================================================
def calcular_impacto_agua(volume_litros, massa_agente_kg, dados_agente):
    """
    Calcula a concentração final e compara com doses letais.
    """
    # 1. Conversão de Massa (kg -> mg)
    massa_mg = massa_agente_kg * 1_000_000
    
    # 2. Concentração (mg/L ou ppm)
    concentracao_mg_L = massa_mg / volume_litros
    
    # 3. Toxicologia Humana (Padrão: Adulto 70kg)
    peso_medio = 70.0
    dose_letal_total_mg = dados_agente['LD50'] * peso_medio
    
    # Quantos mg tem em um copo d'água (250ml)?
    mg_no_copo = concentracao_mg_L * 0.25
    
    # O copo mata?
    copos_para_morte = dose_letal_total_mg / mg_no_copo if mg_no_copo > 0 else 999999
    
    # 4. Potabilidade
    fator_excesso = concentracao_mg_L / dados_agente['limite_potavel'] if dados_agente['limite_potavel'] > 0 else float('inf')
    
    # 5. Classificação
    if copos_para_morte <= 1.0:
        status = "LETAL IMEDIATO (1 Copo)"
        cor = "red"
    elif copos_para_morte <= 10.0:
        status = "PERIGO AGUDO (Alguns Copos)"
        cor = "orange"
    elif fator_excesso > 1:
        status = "IMPRÓPRIA (Intoxicação Lenta)"
        cor = "yellow"
    else:
        status = "SEGURA (Diluição Eficaz)"
        cor = "green"
        
    return {
        "concentracao": concentracao_mg_L,
        "mg_copo": mg_no_copo,
        "dose_letal_pessoa": dose_letal_total_mg,
        "copos_letais": copos_para_morte,
        "fator_limite": fator_excesso,
        "status": status,
        "cor": cor
    }

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 💧 Contaminação de Água")
    st.markdown("Modelagem de sabotagem hídrica: Diluição, Toxicidade e Potabilidade.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 A Matemática do Veneno (Diluição)", expanded=True):
        st.markdown("""
        **O Cenário:** Um terrorista joga um saco de veneno em uma caixa d'água ou reservatório.
        
        **A Regra de Ouro:** *'A dose faz o veneno'.*
        * Jogar 1kg de Cianeto em uma piscina olímpica pode matar quem beber.
        * Jogar 1kg de Cianeto em uma represa gigante apenas dilui o veneno a níveis indetectáveis.
        
        **O Cálculo:**
        O sistema divide a Massa (Veneno) pelo Volume (Água) para achar a Concentração. Depois, calcula se um **copo de 250ml** contém veneno suficiente para matar um adulto de 70kg (Baseado na LD50).
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. O Alvo (Reservatório)")
        
        # Presets de Volume para facilitar
        tipo_reservatorio = st.selectbox(
            "Tipo de Reservatório",
            ["Caixa d'Água Residencial (1.000 L)", 
             "Caminhão Pipa (10.000 L)", 
             "Torre de Condomínio (50.000 L)",
             "Piscina Olímpica (2.500.000 L)",
             "Pequena Represa/ETA (100.000.000 L)"],
            index=2
        )
        
        # Extrair volume do texto ou permitir customizado
        mapa_vol = {
            "Caixa d'Água Residencial (1.000 L)": 1000,
            "Caminhão Pipa (10.000 L)": 10000,
            "Torre de Condomínio (50.000 L)": 50000,
            "Piscina Olímpica (2.500.000 L)": 2500000,
            "Pequena Represa/ETA (100.000.000 L)": 100000000
        }
        
        volume = st.number_input("Volume Real (Litros)", value=mapa_vol[tipo_reservatorio], min_value=100)
        st.caption(f"ℹ️ {volume/1000:.0f} metros cúbicos de água.")

    with col2:
        st.subheader("2. O Agente (Ataque)")
        agente = st.selectbox("Substância Utilizada", list(CONTAMINANTES_AGUA.keys()))
        dados_agente = CONTAMINANTES_AGUA[agente]
        
        st.info(f"☠️ **{agente}**\n\n{dados_agente['desc']}\n\n*LD50: {dados_agente['LD50']} mg/kg*")
        
        massa = st.number_input("Quantidade Jogada na Água (kg)", value=1.0, step=0.5, min_value=0.001)

    # Botão de Cálculo
    if 'agua_calc' not in st.session_state: st.session_state['agua_calc'] = False
    
    if st.button("🧪 Analisar Potabilidade", type="primary", use_container_width=True):
        st.session_state['agua_calc'] = True

    if st.session_state['agua_calc']:
        res = calcular_impacto_agua(volume, massa, dados_agente)
        
        st.write("---")
        st.markdown(f"### 🛡️ Diagnóstico: <span style='color:{res['cor']}'>{res['status']}</span>", unsafe_allow_html=True)

        # Métricas Principais
        m1, m2, m3 = st.columns(3)
        m1.metric("Concentração Final", f"{res['concentracao']:.4f} mg/L", f"Limite: {dados_agente['limite_potavel']} mg/L", delta_color="inverse")
        m2.metric("Veneno por Copo (250ml)", f"{res['mg_copo']:.2f} mg", "Ingestão Típica")
        m3.metric("Dose Letal (70kg)", f"{res['dose_letal_pessoa']:.2f} mg", "Para matar 1 pessoa")

        # Análise do Copo d'Água (Visual)
        st.markdown("#### 🥤 Teste do Copo d'Água")
        if res['copos_letais'] < 1:
            st.error(f"💀 **MORTE CERTA:** Um único gole contém {res['mg_copo']:.1f} mg (a dose letal é {res['dose_letal_pessoa']:.1f} mg). Sobrevivência improvável.")
        elif res['copos_letais'] < 5:
            st.warning(f"⚠️ **PERIGO EXTREMO:** Beber {int(res['copos_letais'])+1} copos seria fatal. Sintomas graves no primeiro copo.")
        elif res['fator_limite'] > 1:
            st.warning(f"🚫 **ÁGUA IMPRÓPRIA:** Não mata imediatamente (precisaria de {int(res['copos_letais'])} copos), mas excede o limite legal em {res['fator_limite']:.0f}x. Causa danos crônicos.")
        else:
            st.success("✅ **DILUIÇÃO EFICAZ:** O volume de água foi suficiente para anular o veneno. A concentração está abaixo do limite legal.")

        # Calculadora de Remediação
        if res['fator_limite'] > 1:
            with st.expander("🚒 Como salvar essa água? (Cálculo de Diluição)", expanded=False):
                agua_necessaria = (res['concentracao'] / dados_agente['limite_potavel']) * volume
                st.write(f"Para diluir essa contaminação até o nível potável, você precisaria adicionar mais **{agua_necessaria/1000000:.1f} milhões de litros** de água limpa.")
                st.write("Isso geralmente é inviável. A solução tática é **drenar o reservatório e descontaminar** ou usar osmose reversa (se químico) / ultrafiltração (se biológico).")

        # Gráfico Comparativo (Escala Logarítmica para caber tudo)
        st.markdown("#### 📊 Comparação de Escala (mg/L)")
        
        df_chart = pd.DataFrame({
            'Referência': ['Limite Potável', 'Concentração Atual', 'Concentração Letal (1 Copo)'],
            'Valor (mg/L)': [
                dados_agente['limite_potavel'] if dados_agente['limite_potavel'] > 0 else 0.0001, 
                res['concentracao'], 
                res['dose_letal_pessoa'] * 4 # Se 250ml mata, então 1L tem 4x a dose
            ],
            'Cor': ['green', res['cor'], 'black']
        })
        
        chart = alt.Chart(df_chart).mark_bar().encode(
            x=alt.X('Valor (mg/L)', scale=alt.Scale(type='log')), # Escala Log vital aqui
            y=alt.Y('Referência', sort=['Concentração Letal (1 Copo)', 'Concentração Atual', 'Limite Potável']),
            color=alt.Color('Cor', scale=None),
            tooltip=['Referência', 'Valor (mg/L)']
        ).properties(title="Escala Logarítmica de Toxicidade")
        
        st.altair_chart(chart, use_container_width=True)
