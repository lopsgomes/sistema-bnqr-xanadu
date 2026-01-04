import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS: GASES DENSOS (PESADOS QUE O AR)
# =============================================================================
# Gases e vapores com densidade relativa ao ar > 1.0
# Fonte: EPA AEGL Program, NIOSH Pocket Guide, CCPS Guidelines
# Densidade Relativa: > 1.0 (Pesado, rasteja) | > 1.5 (Muito Pesado, crítico)
# Lv = Calor Latente de Vaporização (kJ/kg) - para líquidos/criogênicos
# T_ebulicao = Temperatura de Ebulição (°C) - para identificar criogênicos
GASES_DENSOS = {
    "Cloro (Cl₂)": {
        "mw": 70.90,
        "densidade_rel": 2.5,
        "aegl1": 0.5,
        "aegl2": 2.0,
        "aegl3": 20.0,
        "idlh": 10,
        "tipo": "gas",
        "desc": "Gás verde-amarelado, muito pesado. Rasteja pelo chão, entra em porões e metrôs. Extremamente tóxico."
    },
    "Dióxido de Carbono (CO₂)": {
        "mw": 44.01,
        "densidade_rel": 1.52,
        "aegl1": 40000,
        "aegl2": 40000,
        "aegl3": 40000,
        "idlh": 40000,
        "tipo": "gas",
        "desc": "Gás asfixiante. Desloca oxigênio. Em altas concentrações causa perda de consciência rápida."
    },
    "Amônia Liquefeita (LNH₃)": {
        "mw": 17.03,
        "densidade_rel": 0.6,  # Gás é leve, mas líquido cria névoa fria densa
        "aegl1": 30,
        "aegl2": 160,
        "aegl3": 1100,
        "idlh": 300,
        "tipo": "liquido_criogenico",
        "lv": 1370,  # kJ/kg
        "t_ebulicao": -33.3,
        "desc": "Líquido criogênico. Ao evaporar, forma névoa fria densa que rasteja pelo chão."
    },
    "Bromo (Vapor)": {
        "mw": 159.80,
        "densidade_rel": 5.5,
        "aegl1": 0.33,
        "aegl2": 2.2,
        "aegl3": 8.5,
        "idlh": 3,
        "tipo": "liquido",
        "lv": 193,
        "t_ebulicao": 58.8,
        "desc": "Vapores vermelhos muito pesados. Destrói tecidos por oxidação. Viaja muito rente ao chão."
    },
    "Ácido Clorídrico (HCl - Gás)": {
        "mw": 36.46,
        "densidade_rel": 1.3,
        "aegl1": 1.8,
        "aegl2": 22,
        "aegl3": 100,
        "idlh": 50,
        "tipo": "gas",
        "desc": "Névoa ácida branca. Irritante severo. Comum em acidentes rodoviários."
    },
    "Dióxido de Enxofre (SO₂)": {
        "mw": 64.06,
        "densidade_rel": 2.2,
        "aegl1": 0.2,
        "aegl2": 0.75,
        "aegl3": 30,
        "idlh": 100,
        "tipo": "gas",
        "desc": "Subproduto industrial. Pesado e invisível. Causa espasmo de glote imediato."
    },
    "Arsina (SA)": {
        "mw": 77.95,
        "densidade_rel": 2.7,
        "aegl1": 0.0,
        "aegl2": 0.12,
        "aegl3": 0.86,
        "idlh": 3,
        "tipo": "gas",
        "desc": "Gás incolor (cheiro de alho). Usado em semicondutores. Destrói hemácias rapidamente."
    },
    "Nitrogênio Líquido (LN₂)": {
        "mw": 28.01,
        "densidade_rel": 0.97,  # Gás é leve, mas vapor frio é denso
        "aegl1": 0,
        "aegl2": 0,
        "aegl3": 0,
        "idlh": 0,
        "tipo": "liquido_criogenico",
        "lv": 199,
        "t_ebulicao": -195.8,
        "desc": "Criogênico. Vapor frio desloca oxigênio. Risco de asfixia pura."
    },
    "Propano (Líquido)": {
        "mw": 44.10,
        "densidade_rel": 1.52,
        "aegl1": 0,
        "aegl2": 0,
        "aegl3": 0,
        "idlh": 2100,
        "tipo": "liquido",
        "lv": 426,
        "t_ebulicao": -42.1,
        "desc": "GLP. Ao evaporar, forma nuvem pesada e inflamável que rasteja."
    },
    "Cloreto de Vinila": {
        "mw": 62.50,
        "densidade_rel": 2.15,
        "aegl1": 250,
        "aegl2": 1200,
        "aegl3": 4800,
        "idlh": 0,
        "tipo": "gas",
        "desc": "Gás inflamável e carcinogênico. Risco de explosão é maior que o tóxico agudo."
    },
    "Dissulfeto de Carbono": {
        "mw": 76.14,
        "densidade_rel": 2.6,
        "aegl1": 13,
        "aegl2": 160,
        "aegl3": 480,
        "idlh": 500,
        "tipo": "liquido",
        "lv": 352,
        "t_ebulicao": 46.2,
        "desc": "Líquido que vira vapor muito inflamável e neurotóxico. Vapores pesados."
    },
    "Fosgênio (COCl₂)": {
        "mw": 98.92,
        "densidade_rel": 3.4,
        "aegl1": 0.0,
        "aegl2": 0.1,
        "aegl3": 1.5,
        "idlh": 2,
        "tipo": "gas",
        "desc": "Agente de guerra química. Gás muito pesado. Efeitos letais tardios (edema pulmonar 6-24h após exposição)."
    },
    "Fluoreto de Hidrogênio (HF)": {
        "mw": 20.01,
        "densidade_rel": 0.92,  # Gás leve, mas forma névoa densa
        "aegl1": 1.0,
        "aegl2": 24,
        "aegl3": 44,
        "idlh": 30,
        "tipo": "liquido",
        "lv": 245,
        "t_ebulicao": 19.5,
        "desc": "EXTREMO. Corrói vidro e ossos. Forma nuvem branca densa que viaja baixo apesar do MW leve."
    },
    "Metil Brometo": {
        "mw": 94.94,
        "densidade_rel": 3.3,
        "aegl1": 0.0,
        "aegl2": 210,
        "aegl3": 850,
        "idlh": 250,
        "tipo": "liquido",
        "lv": 252,
        "t_ebulicao": 3.6,
        "desc": "Fumigante pesado. Neurotóxico cumulativo. Vapores muito pesados que rastejam pelo chão."
    },
    "Metil Mercaptana": {
        "mw": 48.11,
        "densidade_rel": 1.66,
        "aegl1": 0.005,
        "aegl2": 37,
        "aegl3": 120,
        "idlh": 150,
        "tipo": "gas",
        "desc": "Gás com cheiro de repolho podre. Depressor do sistema nervoso central. Inflamável."
    },
    "Peróxido de Hidrogênio (Vapor)": {
        "mw": 34.01,
        "densidade_rel": 1.2,
        "aegl1": 10,
        "aegl2": 50,
        "aegl3": 100,
        "idlh": 75,
        "tipo": "liquido",
        "lv": 1200,
        "t_ebulicao": 150.2,
        "desc": "Vapores de peróxido concentrado. Oxidante forte. Pode causar queimaduras químicas e irritação severa."
    },
    "Sarin (GB)": {
        "mw": 140.10,
        "densidade_rel": 4.9,
        "aegl1": 0.0,
        "aegl2": 0.0003,
        "aegl3": 0.001,
        "idlh": 0.1,
        "tipo": "liquido",
        "lv": 350,
        "t_ebulicao": 147,
        "desc": "Agente neurotóxico de guerra química. Extremamente letal em doses mínimas. Vapores muito pesados."
    },
    "Tetracloroetileno (PCE)": {
        "mw": 165.83,
        "densidade_rel": 5.7,
        "aegl1": 0,
        "aegl2": 0,
        "aegl3": 0,
        "idlh": 150,
        "tipo": "liquido",
        "lv": 210,
        "t_ebulicao": 121.1,
        "desc": "Lavagem a seco. Vapores extremamente pesados. Carcinogênico provável. Neurotóxico e hepatotóxico."
    },
    "Tolueno 2,4-Diisocianato (TDI)": {
        "mw": 174.16,
        "densidade_rel": 6.0,
        "aegl1": 0.02,
        "aegl2": 0.17,
        "aegl3": 0.55,
        "idlh": 2.5,
        "tipo": "liquido",
        "lv": 280,
        "t_ebulicao": 251,
        "desc": "Vapores de espumas industriais. Extremamente pesado. Asma severa e danos pulmonares imediatos."
    },
    "Trimetilamina": {
        "mw": 59.11,
        "densidade_rel": 2.1,
        "aegl1": 0,
        "aegl2": 0,
        "aegl3": 0,
        "idlh": 200,
        "tipo": "gas",
        "desc": "Gás com cheiro de peixe podre. Irritante severo para olhos e vias respiratórias. Inflamável."
    },
    "Óxido de Etileno": {
        "mw": 44.05,
        "densidade_rel": 1.5,
        "aegl1": 0.0,
        "aegl2": 45,
        "aegl3": 200,
        "idlh": 800,
        "tipo": "gas",
        "desc": "Gás esterilizante. Carcinogênico, mutagênico e explosivo. Vapores pesados."
    },
    "OUTRAS (Entrada Manual)": {
        "mw": 0,
        "densidade_rel": 1.0,
        "aegl1": 0,
        "aegl2": 0,
        "aegl3": 0,
        "idlh": 0,
        "tipo": "gas",
        "desc": "Configure manualmente os parâmetros da substância."
    }
}

# Limites de Asfixia (para gases não tóxicos que deslocam O₂)
LIMITES_ASFIXIA = {
    "O₂ Normal": 21.0,  # % vol
    "Limite Seguro": 19.5,  # % vol
    "Sintomas Leves": 17.0,  # % vol
    "Perda de Consciência": 12.0,  # % vol
    "Morte": 6.0  # % vol
}

# =============================================================================
# 2. MOTOR DE CÁLCULO: MODELO DE GÁS DENSO
# =============================================================================
def verificar_gas_denso(densidade_rel):
    """
    Verifica se o gás é considerado denso.
    Critério: densidade_rel > 1.5 (conservador) ou > 1.0 (menos conservador)
    """
    return densidade_rel > 1.5

def calcular_evaporacao_liquido(q_calor_kw, lv_kj_kg):
    """
    Calcula taxa de evaporação para líquidos/criogênicos.
    
    m_evap = Q_calor / Lv
    
    Onde:
    - Q_calor = fluxo térmico do ambiente (kW)
    - Lv = calor latente de vaporização (kJ/kg)
    """
    if lv_kj_kg <= 0:
        return 0.0
    
    # Fluxo térmico típico do ambiente (aproximação)
    # Para criogênicos, o fluxo é maior devido à diferença de temperatura
    if q_calor_kw <= 0:
        # Estimativa baseada em área de contato (simplificada)
        q_calor_kw = 10.0  # kW (valor típico)
    
    m_evap_kg_s = q_calor_kw / lv_kj_kg
    
    return m_evap_kg_s

def calcular_velocidade_frontal(h_m, densidade_gas, densidade_ar=1.2):
    """
    Calcula velocidade frontal do espalhamento gravitacional (slumping).
    
    Uf = sqrt(g * h * (ρ_gas - ρ_ar) / ρ_ar)
    
    Onde:
    - g = gravidade (9.81 m/s²)
    - h = altura média da nuvem (m)
    - ρ_gas = densidade do gás (kg/m³)
    - ρ_ar = densidade do ar (kg/m³)
    """
    g = 9.81  # m/s²
    
    if densidade_gas <= densidade_ar:
        return 0.0
    
    uf = math.sqrt(g * h_m * (densidade_gas - densidade_ar) / densidade_ar)
    
    return uf

def calcular_box_model(massa_kg, q_kg_s, tempo_s, densidade_gas, u_vento_m_s, rugosidade="rural"):
    """
    Modelo de Caixa (Box Model) para gases densos.
    
    A nuvem é tratada como uma caixa móvel que:
    1. Se espalha gravitacionalmente
    2. É arrastada pelo vento
    3. Dilui por entrainment de ar
    
    Retorna: comprimento, largura, altura, concentração média
    """
    # Densidade do ar padrão
    densidade_ar = 1.2  # kg/m³
    
    # Altura inicial da nuvem (estimativa)
    h_inicial = 2.0  # metros (típico para vazamento no solo)
    
    # Velocidade frontal de espalhamento
    uf = calcular_velocidade_frontal(h_inicial, densidade_gas, densidade_ar)
    
    # Comprimento (direção do vento)
    # L = u_vento * t + uf * t (arrastamento + espalhamento)
    comprimento = (u_vento_m_s + uf) * tempo_s
    
    # Largura (perpendicular ao vento)
    # W = 2 * uf * t (espalhamento lateral)
    largura = 2 * uf * tempo_s
    
    # Altura (dilui com o tempo)
    # Coeficiente de diluição turbulenta
    k_dil = 0.01  # 1/s (empírico)
    altura = h_inicial * math.exp(-k_dil * tempo_s)
    altura = max(0.5, altura)  # Altura mínima de 0.5m
    
    # Volume da caixa
    volume = comprimento * largura * altura
    
    # Massa total (vazamento contínuo acumulado)
    if q_kg_s > 0:
        massa_total = q_kg_s * tempo_s
    else:
        massa_total = massa_kg
    
    # Concentração média (kg/m³)
    if volume > 0:
        concentracao_kg_m3 = massa_total / volume
    else:
        concentracao_kg_m3 = 0.0
    
    # Converter para % vol (aproximação)
    # % vol ≈ (concentracao_kg/m³ / densidade_gas) * 100
    # Mas precisamos converter para ppm primeiro
    # Assumindo comportamento de gás ideal
    concentracao_percent = (concentracao_kg_m3 / densidade_gas) * 100
    
    return {
        "comprimento": comprimento,
        "largura": largura,
        "altura": altura,
        "concentracao_percent": concentracao_percent,
        "concentracao_kg_m3": concentracao_kg_m3,
        "massa_total": massa_total,
        "velocidade_frontal": uf
    }

def calcular_diluicao_temporal(concentracao_inicial, tempo_s, k_dil=0.01):
    """
    Calcula diluição por entrainment de ar ao longo do tempo.
    
    C(t) = C₀ * exp(-k * t)
    """
    concentracao_final = concentracao_inicial * math.exp(-k_dil * tempo_s)
    return concentracao_final

def avaliar_toxicidade_asfixia(concentracao_percent, substancia_dados):
    """
    Avalia risco de toxicidade e asfixia baseado em concentração.
    
    Parâmetros:
    - concentracao_percent: Concentração do gás em % em volume
    - substancia_dados: Dicionário com propriedades da substância (AEGL, IDLH)
    
    Retorna:
    - Dicionário com avaliação de risco (toxicidade, asfixia, risco_total, cor, mensagem)
    """
    resultados = {
        "toxicidade": None,
        "asfixia": None,
        "risco_total": None,
        "cor": "green",
        "mensagem": ""
    }
    
    # Verificar toxicidade (AEGL-2 como limite de incapacitação)
    aegl2 = substancia_dados.get("aegl2", 0)
    idlh = substancia_dados.get("idlh", 0)
    
    # Converter concentração para ppm (assumindo % vol)
    concentracao_ppm = concentracao_percent * 10000
    
    risco_toxico = False
    nivel_toxico = ""
    
    if aegl2 > 0 and concentracao_ppm >= aegl2:
        risco_toxico = True
        if concentracao_ppm >= substancia_dados.get("aegl3", float('inf')):
            nivel_toxico = "Letal"
            resultados["cor"] = "red"
        elif concentracao_ppm >= idlh:
            nivel_toxico = "IDLH - Perigoso"
            resultados["cor"] = "red"
        else:
            nivel_toxico = "Incapacitante"
            resultados["cor"] = "orange"
    
    # Verificar asfixia (deslocamento de O₂)
    # O₂ restante = 21% - concentração do gás (se não tóxico)
    if substancia_dados.get("tipo") == "gas" and not risco_toxico:
        o2_restante = 21.0 - concentracao_percent
        
        if o2_restante < LIMITES_ASFIXIA["Morte"]:
            resultados["asfixia"] = "Morte"
            resultados["cor"] = "red"
            resultados["mensagem"] = f"ASFIXIA LETAL: O₂ restante ({o2_restante:.1f}%) abaixo de 6%. Morte em minutos."
        elif o2_restante < LIMITES_ASFIXIA["Perda de Consciência"]:
            resultados["asfixia"] = "Perda de Consciência"
            resultados["cor"] = "red"
            resultados["mensagem"] = f"ASFIXIA CRÍTICA: O₂ restante ({o2_restante:.1f}%) abaixo de 12%. Perda de consciência iminente."
        elif o2_restante < LIMITES_ASFIXIA["Sintomas Leves"]:
            resultados["asfixia"] = "Sintomas Leves"
            resultados["cor"] = "orange"
            resultados["mensagem"] = f"ASFIXIA MODERADA: O₂ restante ({o2_restante:.1f}%) abaixo de 17%. Sintomas respiratórios."
        elif o2_restante < LIMITES_ASFIXIA["Limite Seguro"]:
            resultados["asfixia"] = "Atenção"
            resultados["cor"] = "yellow"
            resultados["mensagem"] = f"O₂ próximo do limite ({o2_restante:.1f}%). Monitore continuamente."
    
    if risco_toxico:
        resultados["toxicidade"] = nivel_toxico
        if not resultados["mensagem"]:
            resultados["mensagem"] = f"TOXICIDADE: Concentração ({concentracao_ppm:.1f} ppm) excede limites seguros. {nivel_toxico}."
    
    if not resultados["mensagem"]:
        resultados["mensagem"] = "Concentração abaixo dos limites de toxicidade e asfixia."
        resultados["risco_total"] = "Baixo"
    else:
        resultados["risco_total"] = "Alto" if resultados["cor"] in ["red", "orange"] else "Moderado"
    
    return resultados

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Dispersão de Gases Densos e Asfixiantes")
    st.markdown("**Simulação de nuvens de gases mais pesados que o ar, que rastejam pelo solo e representam risco crítico de asfixia e toxicidade**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos Teóricos e Conceitos Operacionais", expanded=True):
        st.markdown("""
        #### O que são Gases Densos?
        
        Nem todos os gases se comportam da mesma forma na atmosfera. Gases **mais pesados que o ar** (densidade relativa > 1.0) não seguem o modelo de dispersão Gaussiano clássico usado para gases leves. Eles apresentam comportamento único:
        
        1. **Afundam por diferença de densidade:** A força gravitacional domina sobre a turbulência atmosférica
        2. **Rastejam pelo chão como um fluido:** Formam uma camada densa que se espalha horizontalmente
        3. **Se acumulam em áreas baixas:** Valas, túneis, subsolos, porões, bueiros
        4. **Transição para regime turbulento:** Só depois de se diluir significativamente entram em regime de dispersão atmosférica normal
        
        #### Por que são Perigosos?
        
        O comportamento de gases densos cria riscos únicos:
        - **A nuvem não sobe:** Diferente de gases leves, permanece próxima ao solo
        - **Entra em edifícios:** Pode penetrar por portas, janelas baixas, sistemas de ventilação
        - **Risco de asfixia:** Gases não tóxicos (como CO₂, N₂) podem deslocar oxigênio, causando asfixia
        - **Toxicidade aguda no solo:** Concentrações perigosas se mantêm no nível do solo por longos períodos
        - **Dificuldade de detecção:** Muitos gases densos são invisíveis e inodoros
        
        #### Exemplos Críticos
        
        - **Cloro (Cl₂):** Gás verde-amarelado, densidade 2.5x o ar. Rasteja pelo chão e é extremamente tóxico. Entra em porões e metrôs.
        - **Dióxido de Carbono (CO₂):** Gás asfixiante invisível. Em altas concentrações, desloca oxigênio causando perda de consciência rápida.
        - **Amônia Liquefeita:** Ao evaporar, forma névoa fria densa que rasteja pelo chão.
        - **Bromo:** Vapores vermelhos muito pesados (5.5x o ar). Viaja muito rente ao chão.
        
        #### Como Funciona o Modelo?
        
        **1. Critério de Gás Denso:**
        - Se densidade relativa > 1.5 → Ativa modelo de gás pesado (Box Model)
        - Se densidade relativa < 1.5 → Pode usar modelo Gaussiano padrão ou modelo híbrido
        
        **2. Modelo de Caixa (Box Model):**
        A nuvem é tratada como uma "caixa" móvel que:
        - Se espalha gravitacionalmente (slumping) - movimento horizontal devido à diferença de densidade
        - É arrastada pelo vento - movimento na direção do vento
        - Dilui por mistura turbulenta com o ar - entrainment de ar ambiente
        
        **3. Espalhamento Gravitacional (Slumping):**
        Velocidade frontal: **Uf = √(g × h × (ρ_gás - ρ_ar) / ρ_ar)**
        - g = aceleração da gravidade (9.81 m/s²)
        - h = altura média da nuvem (m)
        - ρ_gás = densidade do gás (kg/m³)
        - ρ_ar = densidade do ar (kg/m³)
        
        **4. Diluição Temporal:**
        **C(t) = C₀ × exp(-k × t)**
        Onde k é o coeficiente de mistura turbulenta (empírico, ~0.01 s⁻¹)
        
        **5. Transição para Dispersão Atmosférica:**
        Quando a densidade da mistura (gás + ar entrainado) se aproxima da densidade do ar, o modelo muda para dispersão Gaussiana padrão.
        
        #### Limitações do Modelo
        
        Este modelo utiliza simplificações para fins didáticos e operacionais:
        - Assume terreno plano e sem obstáculos significativos
        - Não considera topografia complexa (montanhas, vales, edifícios)
        - Assume condições meteorológicas estáveis
        - Não modela reações químicas ou decomposição
        - Simplifica o processo de entrainment de ar
        
        Para análises detalhadas, utilize modelos CFD (Computational Fluid Dynamics) ou software especializado (ALOHA, PHAST).
        """)

    st.markdown("---")

    # --- SEÇÃO 1: SUBSTÂNCIA ---
    st.subheader("Substância Química")
    
    substancia_nome = st.selectbox(
        "Selecione a substância:",
        list(GASES_DENSOS.keys()),
        help="Escolha o gás ou líquido envolvido no vazamento. Consulte a FISPQ ou utilize detectores de gás para identificação."
    )
    
    substancia_dados = GASES_DENSOS[substancia_nome]
    
    if substancia_nome == "OUTRAS (Entrada Manual)":
        st.markdown("**Configuração Manual:**")
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            mw_manual = st.number_input("Massa Molecular (g/mol)", min_value=0.0, value=50.0, step=0.1, key="mw_man")
            dens_manual = st.number_input("Densidade Relativa ao Ar", min_value=0.0, value=2.0, step=0.1, key="dens_man")
            tipo_manual = st.selectbox("Tipo", ["gas", "liquido", "liquido_criogenico"], key="tipo_man")
        
        with col_man2:
            aegl2_manual = st.number_input("AEGL-2 (ppm)", min_value=0.0, value=100.0, step=1.0, key="aegl2_man")
            idlh_manual = st.number_input("IDLH (ppm)", min_value=0.0, value=50.0, step=1.0, key="idlh_man")
            if tipo_manual != "gas":
                lv_manual = st.number_input("Calor Latente (kJ/kg)", min_value=0.0, value=400.0, step=10.0, key="lv_man")
            else:
                lv_manual = 0
        
        substancia_dados = {
            "mw": mw_manual,
            "densidade_rel": dens_manual,
            "aegl2": aegl2_manual,
            "idlh": idlh_manual,
            "tipo": tipo_manual,
            "lv": lv_manual if tipo_manual != "gas" else 0,
            "desc": "Substância configurada manualmente."
        }
    else:
        st.info(f"**{substancia_nome}**\n\n{substancia_dados['desc']}")
        
        col_prop1, col_prop2, col_prop3, col_prop4 = st.columns(4)
        col_prop1.metric("Densidade Relativa", f"{substancia_dados['densidade_rel']:.2f}x", "vs Ar",
                        help="Densidade do gás em relação ao ar (1.0 = mesmo peso do ar)")
        col_prop2.metric("AEGL-2", f"{substancia_dados['aegl2']:.1f} ppm", "Incapacitante",
                        help="Nível de exposição aguda que causa incapacitação")
        col_prop3.metric("IDLH", f"{substancia_dados['idlh']:.0f} ppm", "Perigoso",
                        help="Concentração imediatamente perigosa à vida ou saúde")
        col_prop4.metric("Tipo", substancia_dados['tipo'].upper(), 
                        help="Tipo de substância: gás, líquido ou líquido criogênico")
        
        # Verificar se é gás denso
        if verificar_gas_denso(substancia_dados['densidade_rel']):
            st.success(f"**GÁS DENSO DETECTADO:** Densidade relativa ({substancia_dados['densidade_rel']:.2f}) > 1.5. "
                      f"Este gás rasteja pelo chão e se acumula em áreas baixas (valas, túneis, subsolos).")
        else:
            st.warning(f"**ATENÇÃO:** Densidade relativa ({substancia_dados['densidade_rel']:.2f}) < 1.5. "
                      f"Este gás pode não seguir comportamento de gás denso puro. Considere usar o módulo de Nuvem Tóxica Outdoor.")

    st.markdown("---")

    # --- SEÇÃO 2: CENÁRIO DE VAZAMENTO ---
    st.subheader("Cenário de Vazamento")
    
    col_cen1, col_cen2 = st.columns(2)
    
    with col_cen1:
        tipo_liberacao = st.radio(
            "Tipo de Liberação:",
            ["Contínua", "Instantânea"],
            help="Contínua = vazamento constante | Instantânea = liberação única"
        )
        
        if tipo_liberacao == "Contínua":
            q_kg_s = st.number_input(
                "Taxa de Vazamento (kg/s)",
                min_value=0.01,
                value=1.0,
                step=0.1,
                help="Quantidade de substância liberada por segundo"
            )
            massa_kg = 0  # Não usado em contínuo
        else:
            massa_kg = st.number_input(
                "Massa Total Liberada (kg)",
                min_value=0.1,
                value=100.0,
                step=10.0
            )
            q_kg_s = 0  # Não usado em instantâneo
        
        altura_liberacao = st.number_input(
            "Altura da Liberação (m)",
            min_value=0.0,
            value=0.0,
            step=0.5,
            help="Altura do ponto de vazamento acima do solo (0 = no chão)"
        )
        
        # Para líquidos/criogênicos, calcular evaporação
        if substancia_dados.get("tipo") in ["liquido", "liquido_criogenico"]:
            st.markdown("**Evaporação (Líquido/Criogênico):**")
            st.caption("Líquidos e criogênicos evaporam continuamente, gerando vapores densos.")
            q_calor = st.number_input(
                "Fluxo Térmico do Ambiente (kW)",
                min_value=0.1,
                value=10.0,
                step=1.0,
                help="Calor recebido do ambiente para vaporização. Valores típicos: 5-15 kW para líquidos normais, 20-50 kW para criogênicos."
            )
            m_evap = calcular_evaporacao_liquido(q_calor, substancia_dados.get("lv", 0))
            if m_evap > 0:
                st.info(f"**Taxa de Evaporação:** {m_evap:.3f} kg/s")
                # Adicionar à taxa de vazamento
                if tipo_liberacao == "Contínua":
                    q_kg_s += m_evap
                else:
                    # Para instantâneo, assumir evaporação contínua
                    q_kg_s = m_evap

    with col_cen2:
        st.markdown("**Condições Atmosféricas:**")
        
        velocidade_vento = st.number_input(
            "Velocidade do Vento (m/s)",
            min_value=0.1,
            value=3.0,
            step=0.5,
            help="Velocidade do vento a 10m de altura"
        )
        
        classe_estabilidade = st.selectbox(
            "Classe de Estabilidade (Pasquill):",
            ["A", "B", "C", "D", "E", "F"],
            index=3,
            help="A = Muito instável | D = Neutra | F = Muito estável"
        )
        
        temperatura = st.number_input(
            "Temperatura Ambiente (°C)",
            min_value=-50.0,
            max_value=50.0,
            value=25.0,
            step=1.0
        )
        
        rugosidade = st.selectbox(
            "Rugosidade do Terreno:",
            ["Rural", "Urbano"],
            help="Rural = menos obstáculos | Urbano = mais obstáculos, mais turbulência"
        )

    st.markdown("---")

    # --- SEÇÃO 3: GEORREFERENCIAMENTO ---
    st.subheader("Localização do Incidente")
    
    col_geo1, col_geo2 = st.columns(2)
    
    with col_geo1:
        lat = st.number_input("Latitude (graus decimais)", value=-22.8625, format="%.6f",
                             help="Coordenada geográfica do local do vazamento. Use o Google Maps para obter coordenadas precisas.")
    
    with col_geo2:
        lon = st.number_input("Longitude (graus decimais)", value=-43.2245, format="%.6f",
                             help="Coordenada geográfica do local do vazamento.")

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("CALCULAR DISPERSÃO DE GÁS DENSO", type="primary", use_container_width=True):
        st.session_state['gases_densos_calc'] = True

    if st.session_state.get('gases_densos_calc', False):
        # Verificar se é gás denso
        if not verificar_gas_denso(substancia_dados['densidade_rel']):
            st.warning("**ATENÇÃO:** Esta substância pode não seguir comportamento de gás denso puro. "
                      "Considere usar o módulo de Nuvem Tóxica Outdoor para análise mais precisa.")
        
        # Calcular densidade do gás (kg/m³)
        densidade_ar = 1.2  # kg/m³ (a 25°C, 1 atm)
        densidade_gas = densidade_ar * substancia_dados['densidade_rel']
        
        # Tempo de análise (variar de 0 a 30 minutos)
        tempos_analise = np.arange(0, 1800, 60)  # 0 a 30 min, passo de 1 min
        
        resultados_tempo = []
        
        for t in tempos_analise:
            resultado = calcular_box_model(massa_kg, q_kg_s, t, densidade_gas, velocidade_vento, rugosidade)
            resultado["tempo_s"] = t
            resultado["tempo_min"] = t / 60.0
            resultados_tempo.append(resultado)
        
        # Resultado no tempo de 10 minutos (padrão para análise)
        tempo_analise = 600  # 10 minutos
        resultado_principal = calcular_box_model(massa_kg, q_kg_s, tempo_analise, densidade_gas, velocidade_vento, rugosidade)
        
        # Avaliar toxicidade e asfixia
        avaliacao = avaliar_toxicidade_asfixia(resultado_principal["concentracao_percent"], substancia_dados)
        
        st.markdown("---")
        st.markdown("### Resultados da Simulação")
        
        # Métricas principais
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        col_res1.metric(
            "Comprimento da Nuvem",
            f"{resultado_principal['comprimento']:.0f} m",
            f"{resultado_principal['comprimento']/1000:.2f} km"
        )
        col_res2.metric(
            "Largura da Nuvem",
            f"{resultado_principal['largura']:.0f} m",
            "Lateral"
        )
        col_res3.metric(
            "Altura da Nuvem",
            f"{resultado_principal['altura']:.1f} m",
            "Espessura"
        )
        col_res4.metric(
            "Concentração Média",
            f"{resultado_principal['concentracao_percent']:.3f}% vol",
            f"{resultado_principal['concentracao_percent']*10000:.0f} ppm"
        )
        
        # Diagnóstico de risco
        st.markdown("---")
        st.markdown("### Avaliação de Risco")
        st.markdown(f"**Nível de Risco:** <span style='color:{avaliacao['cor']}; font-size:20px; font-weight:bold'>{avaliacao['risco_total']}</span>", unsafe_allow_html=True)
        
        if avaliacao['cor'] == 'red':
            st.error(avaliacao['mensagem'])
        elif avaliacao['cor'] == 'orange':
            st.warning(avaliacao['mensagem'])
        elif avaliacao['cor'] == 'yellow':
            st.warning(avaliacao['mensagem'])
        else:
            st.success(avaliacao['mensagem'])
        
        # Tempo máximo de permanência
        st.markdown("---")
        st.markdown("### Tempo Máximo de Permanência")
        
        # Calcular em que tempo a concentração cai abaixo dos limites
        tempo_seguro = None
        for resultado in resultados_tempo:
            avaliacao_temp = avaliar_toxicidade_asfixia(resultado["concentracao_percent"], substancia_dados)
            if avaliacao_temp['risco_total'] == 'Baixo':
                tempo_seguro = resultado["tempo_min"]
                break
        
        if tempo_seguro:
            st.success(f"**Tempo até Segurança:** Após {tempo_seguro:.1f} minutos, a concentração cai abaixo dos limites perigosos.")
        else:
            st.error("**RISCO PERSISTENTE:** A concentração permanece perigosa por mais de 30 minutos. Evacuação obrigatória!")
        
        # Informações técnicas
        st.markdown("---")
        st.markdown("### Informações Técnicas")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"""
            **Substância:** {substancia_nome}  
            **Densidade do Gás:** {densidade_gas:.2f} kg/m³  
            **Velocidade Frontal:** {resultado_principal['velocidade_frontal']:.2f} m/s  
            **Massa Total na Nuvem:** {resultado_principal['massa_total']:.2f} kg
            """)
        with col_info2:
            st.markdown(f"""
            **Velocidade do Vento:** {velocidade_vento:.1f} m/s  
            **Classe de Estabilidade:** {classe_estabilidade}  
            **Temperatura:** {temperatura:.1f} °C  
            **Rugosidade:** {rugosidade}
            """)
        
        # Mapa
        st.markdown("---")
        st.markdown("### Visualização da Nuvem de Gás Denso")
        
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
        
        # Marcador do ponto de vazamento
        folium.Marker(
            [lat, lon],
            tooltip="Ponto de Vazamento",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)
        
        # Desenhar zona da nuvem (elipse representativa)
        # Converter dimensões para graus
        comprimento_graus = resultado_principal['comprimento'] / 111000
        largura_graus = resultado_principal['largura'] / (111000 * math.cos(math.radians(lat)))
        
        # Zona de risco (elipse simplificada)
        # Assumindo vento na direção leste
        pontos_elipse = []
        num_pontos = 20
        for i in range(num_pontos):
            angulo = 2 * math.pi * i / num_pontos
            x = comprimento_graus * math.cos(angulo) / 2
            y = largura_graus * math.sin(angulo) / 2
            pontos_elipse.append([lat + y, lon + x])
        
        # Adicionar elipse
        folium.Polygon(
            pontos_elipse,
            color=avaliacao['cor'],
            fill=True,
            fill_opacity=0.3,
            tooltip=f"Zona de Gás Denso: {resultado_principal['concentracao_percent']*10000:.0f} ppm"
        ).add_to(m)
        
        st_folium(m, width=None, height=600)
        
        st.caption("A elipse representa a área aproximada onde o gás denso se espalhou. "
                  "O risco é MAIOR em áreas baixas dentro desta zona (valas, túneis, subsolos, porões).")
        
        # Recomendações
        st.markdown("---")
        st.markdown("### Recomendações Operacionais")
        
        if avaliacao['risco_total'] == 'Alto':
            st.error("**EVACUAÇÃO IMEDIATA:**")
            st.markdown("""
            1. Evacuar imediatamente todas as pessoas dentro da zona de risco
            2. **EVITAR áreas baixas** (valas, túneis, subsolos, porões, bueiros)
            3. **Subir para terreno elevado** (gás denso rasteja pelo chão)
            4. Usar **SCBA (Self-Contained Breathing Apparatus)** ou **Respirador de Linha de Ar**
            5. **Filtros não protegem contra asfixia** - apenas SCBA ou linha de ar
            6. Estabelecer perímetro de segurança baseado na zona de risco
            7. Coordenar com equipes de emergência química
            """)
        elif avaliacao['risco_total'] == 'Moderado':
            st.warning("**ATENÇÃO:**")
            st.markdown("""
            1. Limitar tempo de permanência na zona
            2. Monitorar concentração continuamente com detectores de gás
            3. Evitar áreas baixas (valas, túneis, subsolos)
            4. Usar proteção respiratória adequada
            5. Estabelecer pontos de controle de acesso
            """)
        else:
            st.info("**SITUAÇÃO CONTROLADA:**")
            st.markdown("""
            1. Monitore a evolução da nuvem continuamente
            2. Mantenha distância segura
            3. Evite áreas baixas se possível
            4. Esteja preparado para evacuação se condições piorarem
            """)
        
        st.info("""
        **CONSIDERAÇÕES TÉCNICAS:**
        - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
        - Gases densos podem se acumular em áreas baixas mesmo além das zonas calculadas.
        - Topografia complexa (montanhas, valas, edifícios) pode criar zonas de concentração não previstas.
        - Mudanças nas condições meteorológicas alteram drasticamente o comportamento da nuvem.
        - Consulte modelos CFD ou software especializado (ALOHA, PHAST) para análises detalhadas.
        - Utilize detectores de gás para monitoramento em tempo real das concentrações reais.
        """)
