import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS: SUBSTÂNCIAS INFLAMÁVEIS
# =============================================================================
# LFL = Lower Flammability Limit (% vol)
# UFL = Upper Flammability Limit (% vol)
# Hc = Calor de Combustão (kJ/kg)
# MW = Massa Molecular (g/mol)
# densidade_rel = Densidade relativa ao ar (adimensional)
SUBSTANCIAS_FLASH = {
    "Acetaldeído": {
        "lfl": 4.0, "ufl": 57.0, "hc": 25000, "mw": 44.05, "densidade_rel": 1.52,
        "desc": "Líquido extremamente inflamável. Queima rápida e volátil. Risco de reignição."
    },
    "Acetona": {
        "lfl": 2.5, "ufl": 12.8, "hc": 25800, "mw": 58.08, "densidade_rel": 2.00,
        "desc": "Solvente industrial. Queima limpa e rápida."
    },
    "Acetileno": {
        "lfl": 2.5, "ufl": 100.0, "hc": 48200, "mw": 26.04, "densidade_rel": 0.90,
        "desc": "Gás de solda. Extremamente reativo. Pode detonar mesmo sem oxigênio."
    },
    "Amônia (Anidra)": {
        "lfl": 15.0, "ufl": 28.0, "hc": 18600, "mw": 17.03, "densidade_rel": 0.59,
        "desc": "Gás leve (sobe). Difícil de acender, mas queima se houver fonte forte."
    },
    "Benzeno": {
        "lfl": 1.2, "ufl": 7.8, "hc": 40100, "mw": 78.11, "densidade_rel": 2.70,
        "desc": "Chama muito fuliginosa (fumaça preta densa). Alta radiação térmica."
    },
    "Butano": {
        "lfl": 1.8, "ufl": 8.4, "hc": 45750, "mw": 58.12, "densidade_rel": 2.01,
        "desc": "GLP doméstico. Gás pesado (rasteja). Acumula em baixadas."
    },
    "Ciclohexano": {
        "lfl": 1.2, "ufl": 8.0, "hc": 43400, "mw": 84.16, "densidade_rel": 2.90,
        "desc": "Queima similar à gasolina. Chama intensa e quente."
    },
    "Dióxido de Carbono (CO2)": {
        "lfl": 0.0, "ufl": 0.0, "hc": 0, "mw": 44.01, "densidade_rel": 1.52,
        "desc": "NÃO INFLAMÁVEL - Gás asfixiante. Desloca oxigênio."
    },
    "Dissulfeto de Carbono": {
        "lfl": 1.3, "ufl": 50.0, "hc": 13000, "mw": 76.14, "densidade_rel": 2.64,
        "desc": "EXTREMO. Chama azulada quase invisível. Gases tóxicos (SO2)."
    },
    "Etanol (Álcool)": {
        "lfl": 3.3, "ufl": 19.0, "hc": 26800, "mw": 46.07, "densidade_rel": 1.59,
        "desc": "Chama quase invisível (azulada) de dia. Menor radiação térmica."
    },
    "Etileno": {
        "lfl": 2.7, "ufl": 36.0, "hc": 47100, "mw": 28.05, "densidade_rel": 0.97,
        "desc": "Muito reativo. Queima rápida e violenta."
    },
    "Gasolina (Vapores)": {
        "lfl": 1.4, "ufl": 7.6, "hc": 43700, "mw": 100.0, "densidade_rel": 3.45,
        "desc": "Referência de incêndio. Queima muito rápida com chama alta."
    },
    "Gás Natural (Metano)": {
        "lfl": 5.0, "ufl": 15.0, "hc": 50000, "mw": 16.04, "densidade_rel": 0.55,
        "desc": "GNV/Gás encanado. Muito leve (sobe rápido). Difícil confinar."
    },
    "Hidrogênio": {
        "lfl": 4.0, "ufl": 75.0, "hc": 120000, "mw": 2.02, "densidade_rel": 0.07,
        "desc": "PERIGO INVISÍVEL: Chama transparente de dia. Energia altíssima."
    },
    "Hexano": {
        "lfl": 1.1, "ufl": 7.5, "hc": 44700, "mw": 86.18, "densidade_rel": 2.97,
        "desc": "Alta taxa de queima. Solvente comum."
    },
    "Isopropanol (IPA)": {
        "lfl": 2.0, "ufl": 12.0, "hc": 30500, "mw": 60.10, "densidade_rel": 2.07,
        "desc": "Álcool isopropílico. Queima um pouco mais 'sujo' que o etanol."
    },
    "Metano": {
        "lfl": 5.0, "ufl": 15.0, "hc": 50000, "mw": 16.04, "densidade_rel": 0.55,
        "desc": "Gás natural. Muito leve, sobe rapidamente."
    },
    "Metanol": {
        "lfl": 6.0, "ufl": 36.0, "hc": 20000, "mw": 32.04, "densidade_rel": 1.11,
        "desc": "Álcool metílico. Chama quase invisível. Tóxico se inalado."
    },
    "Monóxido de Carbono (CO)": {
        "lfl": 12.5, "ufl": 74.0, "hc": 10100, "mw": 28.01, "densidade_rel": 0.97,
        "desc": "Gás tóxico e inflamável. Chama azulada."
    },
    "Pentano": {
        "lfl": 1.5, "ufl": 7.8, "hc": 45000, "mw": 72.15, "densidade_rel": 2.49,
        "desc": "Componente da gasolina. Queima rápida."
    },
    "Propano": {
        "lfl": 2.1, "ufl": 9.5, "hc": 46350, "mw": 44.10, "densidade_rel": 1.52,
        "desc": "GLP industrial. Gás pesado, rasteja pelo chão."
    },
    "Propileno": {
        "lfl": 2.0, "ufl": 11.1, "hc": 45800, "mw": 42.08, "densidade_rel": 1.45,
        "desc": "Similar ao propano, mas mais reativo."
    },
    "Tolueno": {
        "lfl": 1.2, "ufl": 7.1, "hc": 40400, "mw": 92.14, "densidade_rel": 3.18,
        "desc": "Solvente aromático. Chama fuliginosa."
    },
    "Xileno": {
        "lfl": 1.0, "ufl": 7.0, "hc": 41000, "mw": 106.17, "densidade_rel": 3.66,
        "desc": "Solvente aromático. Similar ao tolueno."
    },
    "Óxido de Etileno": {
        "lfl": 3.0, "ufl": 100.0, "hc": 29000, "mw": 44.05, "densidade_rel": 1.52,
        "desc": "Esterilizante. Pode decompor explosivamente."
    },
    "Cloreto de Vinila": {
        "lfl": 3.6, "ufl": 33.0, "hc": 19000, "mw": 62.50, "densidade_rel": 2.16,
        "desc": "Monômero de PVC. Queima tóxica (gera HCl e Fosgênio)."
    },
    "Acetato de Etila": {
        "lfl": 2.0, "ufl": 11.5, "hc": 23600, "mw": 88.11, "densidade_rel": 3.04,
        "desc": "Solvente comum. Chama amarelada."
    },
    "Dimetil Éter (DME)": {
        "lfl": 3.4, "ufl": 27.0, "hc": 28900, "mw": 46.07, "densidade_rel": 1.59,
        "desc": "Combustível alternativo. Chama azulada."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "lfl": 4.3, "ufl": 46.0, "hc": 15200, "mw": 34.08, "densidade_rel": 1.18,
        "desc": "Gás ácido. Queima emite SO2 tóxico."
    },
    "OUTRAS (Entrada Manual)": {
        "lfl": 0.0, "ufl": 0.0, "hc": 0, "mw": 0, "densidade_rel": 1.0,
        "desc": "Configure manualmente os parâmetros da substância."
    }
}

# Limites de Dose Térmica (kJ/m²) - TNO / Eisenberg
LIMITES_DOSE = {
    "Dor Intensa": {
        "dose": 100,
        "cor": "#FFD700",
        "desc": "Exposição causa dor intensa, mas sem queimaduras permanentes."
    },
    "Queimadura 1º Grau": {
        "dose": 200,
        "cor": "#FF8C00",
        "desc": "Vermelhidão e dor. Cicatriza em alguns dias."
    },
    "Queimadura 2º Grau": {
        "dose": 600,
        "cor": "#FF4500",
        "desc": "Bolhas e dano à pele. Requer tratamento médico."
    },
    "Letalidade": {
        "dose": 1000,
        "cor": "#8B0000",
        "desc": "Morte provável por queimaduras extensas e choque."
    }
}

# Coeficientes de Dispersão Pasquill-Gifford (σy e σz em metros)
# Fonte: TNO Yellow Book
PASQUILL_SIGMA = {
    "A": {"a": 0.32, "b": 0.0004, "c": 0.24, "d": 0.0001},
    "B": {"a": 0.32, "b": 0.0004, "c": 0.24, "d": 0.0001},
    "C": {"a": 0.22, "b": 0.0004, "c": 0.20, "d": 0.0001},
    "D": {"a": 0.16, "b": 0.0004, "c": 0.14, "d": 0.0003},
    "E": {"a": 0.11, "b": 0.0004, "c": 0.08, "d": 0.0015},
    "F": {"a": 0.11, "b": 0.0004, "c": 0.08, "d": 0.0015}
}

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================
def calcular_sigma_pasquill(distancia_m, classe_estabilidade):
    """
    Calcula os coeficientes de dispersão σy e σz usando correlações Pasquill-Gifford.
    """
    params = PASQUILL_SIGMA.get(classe_estabilidade, PASQUILL_SIGMA["D"])
    
    # σy = a * x^b
    sigma_y = params["a"] * (distancia_m ** params["b"]) * distancia_m
    
    # σz = c * x^d
    sigma_z = params["c"] * (distancia_m ** params["d"]) * distancia_m
    
    return sigma_y, sigma_z

def calcular_concentracao_gaussiana(q_kg_s, u_m_s, sigma_y, sigma_z, altura_m, x_m, y_m=0, z_m=0):
    """
    Modelo de Pluma Gaussiana para dispersão atmosférica.
    
    C(x,y,z) = (Q / (2π σy σz U)) * exp(-y²/(2σy²)) * [exp(-(z-H)²/(2σz²)) + exp(-(z+H)²/(2σz²))]
    """
    if u_m_s <= 0 or sigma_y <= 0 or sigma_z <= 0:
        return 0.0
    
    # Converter Q de kg/s para g/s e depois para concentração em % vol
    # Assumindo ar a 25°C, 1 atm: densidade do ar ≈ 1.2 kg/m³
    densidade_ar = 1.2  # kg/m³
    
    # Concentração em kg/m³
    termo_base = q_kg_s / (2 * math.pi * sigma_y * sigma_z * u_m_s)
    
    termo_y = math.exp(-(y_m ** 2) / (2 * sigma_y ** 2))
    
    termo_z1 = math.exp(-((z_m - altura_m) ** 2) / (2 * sigma_z ** 2))
    termo_z2 = math.exp(-((z_m + altura_m) ** 2) / (2 * sigma_z ** 2))
    
    concentracao_kg_m3 = termo_base * termo_y * (termo_z1 + termo_z2)
    
    # Converter para % vol (aproximação)
    # % vol ≈ (concentracao_kg/m³ / densidade_substancia) * 100
    # Para simplificar, usamos uma conversão baseada na massa molecular
    # Assumindo comportamento de gás ideal
    concentracao_ppm = (concentracao_kg_m3 / densidade_ar) * 1e6
    
    # Converter ppm para % vol
    concentracao_percent = concentracao_ppm / 10000.0
    
    return concentracao_percent

def calcular_zona_inflamavel(substancia_dados, q_kg_s, u_m_s, altura_m, classe_estabilidade):
    """
    Calcula a zona onde a concentração está entre LFL e UFL.
    Retorna lista de pontos (x, y) que delimitam a região inflamável.
    """
    lfl = substancia_dados["lfl"]
    ufl = substancia_dados["ufl"]
    
    if lfl == 0 or ufl == 0:
        return []
    
    pontos_inflamaveis = []
    
    # Varrer distâncias a favor do vento (x)
    for x in np.arange(10, 1000, 5):  # De 10m a 1000m, passo de 5m
        sigma_y, sigma_z = calcular_sigma_pasquill(x, classe_estabilidade)
        
        # Varrer lateralmente (y)
        for y in np.arange(-200, 201, 10):  # -200m a +200m, passo de 10m
            conc = calcular_concentracao_gaussiana(q_kg_s, u_m_s, sigma_y, sigma_z, altura_m, x, y, 0)
            
            if lfl <= conc <= ufl:
                pontos_inflamaveis.append((x, y))
    
    return pontos_inflamaveis

def calcular_energia_flash_fire(pontos_inflamaveis, substancia_dados, q_kg_s, u_m_s, altura_m, classe_estabilidade):
    """
    Calcula a energia total disponível para combustão na zona inflamável.
    """
    if not pontos_inflamaveis:
        return 0.0, 0.0, 0.0
    
    lfl = substancia_dados["lfl"]
    ufl = substancia_dados["ufl"]
    hc = substancia_dados["hc"]
    
    massa_inflamavel = 0.0
    
    # Estimar massa na zona inflamável (integração simplificada)
    for x, y in pontos_inflamaveis:
        sigma_y, sigma_z = calcular_sigma_pasquill(x, classe_estabilidade)
        conc = calcular_concentracao_gaussiana(q_kg_s, u_m_s, sigma_y, sigma_z, altura_m, x, y, 0)
        
        # Massa por unidade de volume (aproximação)
        # Assumindo que a concentração média na zona é (LFL + UFL) / 2
        conc_media = (lfl + ufl) / 2.0
        densidade_ar = 1.2  # kg/m³
        massa_volumetrica = (conc_media / 100.0) * densidade_ar
        
        # Volume elementar (aproximação)
        volume_elementar = 5.0 * 10.0 * sigma_z  # dx * dy * dz aproximado
        massa_inflamavel += massa_volumetrica * volume_elementar
    
    # Energia total disponível
    energia_total = massa_inflamavel * hc  # kJ
    
    # Fator radiativo (χr) - típico 0.15 a 0.35
    chi_r = 0.25  # Valor médio conservador
    energia_radiativa = energia_total * chi_r
    
    return energia_total, energia_radiativa, massa_inflamavel

def calcular_duracao_flash_fire(pontos_inflamaveis, u_m_s):
    """
    Estima a duração do Flash Fire baseado no comprimento da nuvem e velocidade de propagação.
    """
    if not pontos_inflamaveis:
        return 0.5
    
    # Comprimento máximo da zona inflamável
    x_max = max([p[0] for p in pontos_inflamaveis]) if pontos_inflamaveis else 100
    
    # Velocidade de propagação da chama (típico: 5-15 m/s para hidrocarbonetos)
    velocidade_chama = 10.0  # m/s (valor médio)
    
    # Duração = comprimento / velocidade
    duracao = x_max / velocidade_chama
    
    # Limitar entre 0.5 e 2.0 segundos (típico de Flash Fires)
    duracao = max(0.5, min(2.0, duracao))
    
    return duracao

def calcular_dose_termica(energia_radiativa_kj, area_m2, duracao_s):
    """
    Calcula a dose térmica recebida.
    
    D = q^(4/3) * t
    Onde q é o fluxo de calor médio (kW/m²)
    """
    if area_m2 <= 0 or duracao_s <= 0:
        return 0.0, 0.0  # Retornar tupla mesmo em caso de erro
    
    # Fluxo de calor médio
    fluxo_medio_kw_m2 = energia_radiativa_kj / (area_m2 * duracao_s)
    
    # Dose térmica (correlação TNO/Eisenberg)
    dose_kj_m2 = (fluxo_medio_kw_m2 ** (4/3)) * duracao_s
    
    return dose_kj_m2, fluxo_medio_kw_m2

def avaliar_dano_humano(dose_kj_m2):
    """
    Avalia o dano humano baseado na dose térmica.
    """
    if dose_kj_m2 < LIMITES_DOSE["Dor Intensa"]["dose"]:
        return "Sem Dano", "green", "Exposição abaixo do limiar de dor."
    elif dose_kj_m2 < LIMITES_DOSE["Queimadura 1º Grau"]["dose"]:
        return "Dor Intensa", LIMITES_DOSE["Dor Intensa"]["cor"], LIMITES_DOSE["Dor Intensa"]["desc"]
    elif dose_kj_m2 < LIMITES_DOSE["Queimadura 2º Grau"]["dose"]:
        return "Queimadura 1º Grau", LIMITES_DOSE["Queimadura 1º Grau"]["cor"], LIMITES_DOSE["Queimadura 1º Grau"]["desc"]
    elif dose_kj_m2 < LIMITES_DOSE["Letalidade"]["dose"]:
        return "Queimadura 2º Grau", LIMITES_DOSE["Queimadura 2º Grau"]["cor"], LIMITES_DOSE["Queimadura 2º Grau"]["desc"]
    else:
        return "Letalidade", LIMITES_DOSE["Letalidade"]["cor"], LIMITES_DOSE["Letalidade"]["desc"]

def calcular_tempo_maximo_exposicao(dose_limite_kj_m2, fluxo_kw_m2):
    """
    Calcula o tempo máximo de exposição segura para uma dose limite.
    """
    if fluxo_kw_m2 <= 0:
        return float('inf')
    
    # D = q^(4/3) * t  =>  t = D / q^(4/3)
    tempo_max = dose_limite_kj_m2 / (fluxo_kw_m2 ** (4/3))
    
    return tempo_max

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🔥 Flash Fire - Incêndio Transitório")
    st.markdown("Simulação de ignição rápida de nuvem inflamável com efeito térmico sobre pessoas e estruturas.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O que é um Flash Fire?", expanded=True):
        st.markdown("""
        **O Fenômeno:**
        
        Um Flash Fire ocorre quando uma **nuvem de gás/vapor inflamável** encontra uma fonte de ignição e queima 
        **rapidamente** (0.5 a 2 segundos), liberando calor intenso **sem gerar sobrepressão significativa**.
        
        **Diferença Chave:**
        - ❌ **NÃO é uma explosão** (não há onda de choque)
        - ✅ **É um incêndio transitório** (queima rápida, efeito térmico)
        
        **Como Funciona:**
        1. **Vazamento:** Gás/vapor escapa e forma uma nuvem
        2. **Dispersão:** O vento espalha a nuvem pelo ambiente
        3. **Zona Inflamável:** Apenas onde a concentração está entre **LFL** e **UFL** pode queimar
        4. **Ignição:** Uma faísca acende a nuvem
        5. **Flash:** A chama se propaga pela nuvem em frações de segundo
        6. **Dano:** O calor liberado causa queimaduras em pessoas expostas
        
        **O que Mata:**
        Não é o pico de calor, mas a **Dose Térmica** (calor × tempo). 
        Mesmo uma chama muito quente, se durar menos de 0.1 segundo, pode não causar dano permanente.
        """)

    with st.expander("🔬 Conceitos Técnicos", expanded=False):
        st.markdown("""
        **LFL (Lower Flammability Limit):** Concentração mínima (% vol) para que a mistura ar-combustível queime.
        
        **UFL (Upper Flammability Limit):** Concentração máxima (% vol) para que a mistura ainda queime.
        
        **Dose Térmica:** Medida do dano causado pelo calor. Fórmula: D = q^(4/3) × t
        - q = fluxo de calor (kW/m²)
        - t = tempo de exposição (s)
        
        **Limites de Dano Humano:**
        - **100 kJ/m²:** Dor intensa
        - **200 kJ/m²:** Queimadura 1º grau
        - **600 kJ/m²:** Queimadura 2º grau
        - **>1000 kJ/m²:** Letalidade
        """)

    st.markdown("---")

    # --- SEÇÃO 1: SUBSTÂNCIA ---
    st.subheader("1️⃣ Substância Inflamável")
    
    substancia_nome = st.selectbox(
        "Selecione a substância:",
        list(SUBSTANCIAS_FLASH.keys()),
        help="Escolha a substância envolvida no vazamento. Use 'OUTRAS' para entrada manual."
    )
    
    substancia_dados = SUBSTANCIAS_FLASH[substancia_nome]
    
    if substancia_nome == "OUTRAS (Entrada Manual)":
        st.markdown("**⚙️ Configuração Manual:**")
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            lfl_manual = st.number_input("LFL (% vol)", min_value=0.0, value=2.0, step=0.1, key="lfl_man")
            ufl_manual = st.number_input("UFL (% vol)", min_value=0.0, value=10.0, step=0.1, key="ufl_man")
            hc_manual = st.number_input("Calor de Combustão (kJ/kg)", min_value=0.0, value=40000.0, step=100.0, key="hc_man")
        
        with col_man2:
            mw_manual = st.number_input("Massa Molecular (g/mol)", min_value=0.0, value=50.0, step=0.1, key="mw_man")
            dens_manual = st.number_input("Densidade Relativa ao Ar", min_value=0.0, value=2.0, step=0.1, key="dens_man")
        
        # Atualizar dados
        substancia_dados = {
            "lfl": lfl_manual,
            "ufl": ufl_manual,
            "hc": hc_manual,
            "mw": mw_manual,
            "densidade_rel": dens_manual,
            "desc": "Substância configurada manualmente."
        }
        
        if lfl_manual == 0 or ufl_manual == 0:
            st.warning("⚠️ LFL e UFL devem ser maiores que zero para substâncias inflamáveis!")
    else:
        st.info(f"ℹ️ **{substancia_nome}**\n\n{substancia_dados['desc']}")
        
        col_prop1, col_prop2, col_prop3 = st.columns(3)
        col_prop1.metric("LFL", f"{substancia_dados['lfl']:.1f}% vol")
        col_prop2.metric("UFL", f"{substancia_dados['ufl']:.1f}% vol")
        col_prop3.metric("Calor de Combustão", f"{substancia_dados['hc']/1000:.1f} MJ/kg")

    st.markdown("---")

    # --- SEÇÃO 2: CENÁRIO DE VAZAMENTO ---
    st.subheader("2️⃣ Cenário de Vazamento")
    
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
        else:
            massa_total = st.number_input(
                "Massa Total Liberada (kg)",
                min_value=0.1,
                value=100.0,
                step=10.0
            )
            tempo_liberacao = st.number_input(
                "Tempo de Liberação (s)",
                min_value=0.1,
                value=10.0,
                step=1.0
            )
            q_kg_s = massa_total / tempo_liberacao
        
        altura_liberacao = st.number_input(
            "Altura da Liberação (m)",
            min_value=0.0,
            value=2.0,
            step=0.5,
            help="Altura do ponto de vazamento acima do solo"
        )
    
    with col_cen2:
        st.markdown("**🌬️ Condições Atmosféricas:**")
        
        velocidade_vento = st.number_input(
            "Velocidade do Vento (m/s)",
            min_value=0.1,
            value=5.0,
            step=0.5,
            help="Velocidade do vento na direção predominante"
        )
        
        classe_estabilidade = st.selectbox(
            "Classe de Estabilidade (Pasquill):",
            ["A", "B", "C", "D", "E", "F"],
            index=3,
            help="A = Muito instável | D = Neutra | F = Muito estável"
        )
        
        st.caption(f"ℹ️ Classe {classe_estabilidade}: {'Muito instável' if classe_estabilidade == 'A' else 'Muito estável' if classe_estabilidade == 'F' else 'Neutra' if classe_estabilidade == 'D' else 'Instável' if classe_estabilidade in ['B','C'] else 'Estável'}")
        
        temperatura = st.number_input(
            "Temperatura Ambiente (°C)",
            min_value=-50.0,
            max_value=50.0,
            value=25.0,
            step=1.0
        )

    st.markdown("---")

    # --- SEÇÃO 3: GEORREFERENCIAMENTO ---
    st.subheader("3️⃣ Localização do Incidente")
    
    col_geo1, col_geo2 = st.columns(2)
    
    with col_geo1:
        lat = st.number_input("Latitude", value=-22.8625, format="%.6f")
    
    with col_geo2:
        lon = st.number_input("Longitude", value=-43.2245, format="%.6f")

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("🔥 Calcular Flash Fire", type="primary", use_container_width=True):
        st.session_state['flash_fire_calc'] = True

    if st.session_state.get('flash_fire_calc', False):
        # Verificar se a substância é inflamável
        if substancia_dados["lfl"] == 0 or substancia_dados["ufl"] == 0:
            st.error("🚨 **SUBSTÂNCIA NÃO INFLAMÁVEL:** Esta substância não pode gerar Flash Fire. Verifique os valores de LFL e UFL.")
        else:
            # Calcular zona inflamável
            with st.spinner("Calculando zona inflamável..."):
                pontos_inflamaveis = calcular_zona_inflamavel(
                    substancia_dados, q_kg_s, velocidade_vento, altura_liberacao, classe_estabilidade
                )
            
            if not pontos_inflamaveis:
                st.warning("⚠️ **ZONA INFLAMÁVEL NÃO DETECTADA:** As condições não geram concentrações entre LFL e UFL. "
                          "O vazamento pode ser muito pequeno ou as condições atmosféricas muito dispersivas.")
            else:
                # Calcular energia
                energia_total, energia_radiativa, massa_inflamavel = calcular_energia_flash_fire(
                    pontos_inflamaveis, substancia_dados, q_kg_s, velocidade_vento, altura_liberacao, classe_estabilidade
                )
                
                # Calcular duração
                duracao = calcular_duracao_flash_fire(pontos_inflamaveis, velocidade_vento)
                
                # Estimar área da zona inflamável
                if pontos_inflamaveis:
                    x_coords = [p[0] for p in pontos_inflamaveis]
                    y_coords = [p[1] for p in pontos_inflamaveis]
                    if x_coords and y_coords:
                        largura = max(x_coords) - min(x_coords)
                        altura = max(y_coords) - min(y_coords)
                        area_aproximada = max(largura * altura, 100.0)  # Mínimo de 100 m²
                    else:
                        area_aproximada = 1000.0
                else:
                    area_aproximada = 1000.0
                
                # Calcular dose térmica
                dose_termica, fluxo_medio = calcular_dose_termica(energia_radiativa, area_aproximada, duracao)
                
                # Avaliar dano
                nivel_dano, cor_dano, desc_dano = avaliar_dano_humano(dose_termica)
                
                st.markdown("---")
                st.markdown("### 📊 Resultados da Simulação")
                
                # Métricas principais
                col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                
                col_res1.metric("Duração do Flash", f"{duracao:.2f} s", "Tempo de queima")
                col_res2.metric("Energia Radiativa", f"{energia_radiativa/1000:.1f} MJ", "Calor liberado")
                col_res3.metric("Fluxo de Calor Médio", f"{fluxo_medio:.1f} kW/m²", "Intensidade térmica")
                col_res4.metric("Dose Térmica", f"{dose_termica:.0f} kJ/m²", "Dano potencial")
                
                # Diagnóstico de dano
                st.markdown("#### 🚨 Avaliação de Dano Humano")
                st.markdown(f"**Nível de Dano:** <span style='color:{cor_dano}; font-size:20px; font-weight:bold'>{nivel_dano}</span>", unsafe_allow_html=True)
                st.info(f"📋 {desc_dano}")
                
                # Tempos de exposição crítica
                st.markdown("#### ⏱️ Tempos de Exposição Crítica")
                
                tempo_dor = calcular_tempo_maximo_exposicao(LIMITES_DOSE["Dor Intensa"]["dose"], fluxo_medio)
                tempo_1grau = calcular_tempo_maximo_exposicao(LIMITES_DOSE["Queimadura 1º Grau"]["dose"], fluxo_medio)
                tempo_2grau = calcular_tempo_maximo_exposicao(LIMITES_DOSE["Queimadura 2º Grau"]["dose"], fluxo_medio)
                
                col_tempo1, col_tempo2, col_tempo3 = st.columns(3)
                col_tempo1.metric("Tempo para Dor Intensa", f"{tempo_dor:.2f} s", "Limite seguro")
                col_tempo2.metric("Tempo para 1º Grau", f"{tempo_1grau:.2f} s", "Queimadura leve")
                col_tempo3.metric("Tempo para 2º Grau", f"{tempo_2grau:.2f} s", "Queimadura grave")
                
                if tempo_dor < duracao:
                    st.warning(f"⚠️ **ATENÇÃO:** A duração do Flash Fire ({duracao:.2f}s) excede o tempo seguro de exposição ({tempo_dor:.2f}s). "
                              f"Pessoas na zona inflamável sofrerão danos!")
                else:
                    st.success(f"✅ A duração do Flash Fire ({duracao:.2f}s) é menor que o tempo seguro ({tempo_dor:.2f}s). "
                              f"Exposição direta pode não causar dano permanente.")
                
                # Mapa
                st.markdown("---")
                st.markdown("#### 🗺️ Visualização da Zona Flash Fire")
                
                m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
                
                # Marcador do ponto de vazamento
                folium.Marker(
                    [lat, lon],
                    tooltip="Ponto de Vazamento",
                    icon=folium.Icon(color="red", icon="fire", prefix="fa")
                ).add_to(m)
                
                # Desenhar zona inflamável (simplificado - círculo representativo)
                if pontos_inflamaveis:
                    x_coords = [p[0] for p in pontos_inflamaveis]
                    y_coords = [p[1] for p in pontos_inflamaveis]
                    
                    # Converter coordenadas relativas para geográficas
                    # 1 grau de latitude ≈ 111 km
                    # 1 grau de longitude ≈ 111 km * cos(latitude)
                    
                    raio_max = max([math.sqrt(x**2 + y**2) for x, y in zip(x_coords, y_coords)]) if x_coords else 100
                    raio_graus = raio_max / 111000  # Converter metros para graus
                    
                    # Zonas de dano (círculos concêntricos simplificados)
                    # Zona letal (mais próxima)
                    folium.Circle(
                        [lat, lon],
                        radius=raio_max * 0.3,
                        color=LIMITES_DOSE["Letalidade"]["cor"],
                        fill=True,
                        fill_opacity=0.4,
                        tooltip=f"Zona Letal: {dose_termica:.0f} kJ/m²"
                    ).add_to(m)
                    
                    # Zona de queimadura 2º grau
                    folium.Circle(
                        [lat, lon],
                        radius=raio_max * 0.6,
                        color=LIMITES_DOSE["Queimadura 2º Grau"]["cor"],
                        fill=True,
                        fill_opacity=0.3,
                        tooltip="Zona de Queimadura 2º Grau"
                    ).add_to(m)
                    
                    # Zona de queimadura 1º grau
                    folium.Circle(
                        [lat, lon],
                        radius=raio_max * 0.8,
                        color=LIMITES_DOSE["Queimadura 1º Grau"]["cor"],
                        fill=True,
                        fill_opacity=0.2,
                        tooltip="Zona de Queimadura 1º Grau"
                    ).add_to(m)
                    
                    # Zona de dor
                    folium.Circle(
                        [lat, lon],
                        radius=raio_max,
                        color=LIMITES_DOSE["Dor Intensa"]["cor"],
                        fill=True,
                        fill_opacity=0.1,
                        tooltip="Zona de Exposição Dolorosa"
                    ).add_to(m)
                
                st_folium(m, width=None, height=600)
                
                st.caption("💡 As zonas são representações simplificadas. A zona real depende da direção do vento e das condições atmosféricas.")
                
                # Recomendações
                st.markdown("---")
                st.markdown("#### 💡 Recomendações Táticas")
                
                if nivel_dano == "Letalidade":
                    st.error("🚨 **EVACUAÇÃO IMEDIATA:** A zona Flash Fire é letal. Nenhuma pessoa deve permanecer na área.")
                elif nivel_dano == "Queimadura 2º Grau":
                    st.warning("⚠️ **ALTO RISCO:** Exposição direta causa queimaduras graves. Evacuação recomendada.")
                elif nivel_dano == "Queimadura 1º Grau":
                    st.warning("⚠️ **RISCO MODERADO:** Exposição causa queimaduras leves. Limite o tempo de permanência.")
                else:
                    st.info("✅ **RISCO BAIXO:** Exposição causa apenas desconforto. Monitore a situação.")
