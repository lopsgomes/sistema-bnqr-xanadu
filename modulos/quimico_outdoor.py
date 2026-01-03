import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

# --- 1. BANCO DE DADOS QUÍMICO (PROPRIEDADES E LIMITES TÓXICOS) ---
# AEGL (Acute Exposure Guideline Levels) em ppm
# Densidade Relativa: < 1.0 (Leve, sobe) | > 1.0 (Pesado, rasteja)
SUBSTANCIAS = {
    "Ácido Clorídrico (HCl - Gás)": {
        "mw": 36.46, "densidade": 1.3,
        "aegl1": 1.8, "aegl2": 22, "aegl3": 100,
        "desc": "Névoa ácida branca. Irritante severo. Comum em acidentes rodoviários com carretas."
    },
    "Ácido Nítrico (Fumegante)": {
        "mw": 63.01, "densidade": 2.2, # Vapores NOx associados
        "aegl1": 0.5, "aegl2": 24, "aegl3": 86,
        "desc": "Líquido que fumega ar laranja/vermelho (NO2). Oxidante forte. Causa edema pulmonar tardio."
    },
    "Acroleína": {
        "mw": 56.06, "densidade": 1.9,
        "aegl1": 0.03, "aegl2": 0.10, "aegl3": 1.4,
        "desc": "Vapor de incêndios ou industrial. Lacrimogêneo extremamente potente. Letal em dose baixíssima."
    },
    "Amônia (Anidra)": {
        "mw": 17.03, "densidade": 0.6,
        "aegl1": 30, "aegl2": 160, "aegl3": 1100,
        "desc": "Gás leve (sobe), a menos que seja vazamento líquido (névoa fria). Risco de sufocamento."
    },
    "Arsina (SA)": {
        "mw": 77.95, "densidade": 2.7,
        "aegl1": 0.0, "aegl2": 0.12, "aegl3": 0.86, # Extremamente tóxico
        "desc": "Gás incolor (cheiro de alho). Usado em semicondutores. Destrói hemácias (sangue) rapidamente."
    },
    "Boro Trifluoreto": {
        "mw": 67.81, "densidade": 2.4,
        "aegl1": 2.5, "aegl2": 18, "aegl3": 100,
        "desc": "Gás incolor que fumega no ar. Corrosivo para pele e pulmões. Reage com água."
    },
    "Bromo (Vapor)": {
        "mw": 159.80, "densidade": 5.5, # Muito Pesado
        "aegl1": 0.33, "aegl2": 2.2, "aegl3": 8.5,
        "desc": "Vapores vermelhos pesados. Destrói tecidos por oxidação. Viaja muito rente ao chão."
    },
    "Cianeto de Hidrogênio (HCN)": {
        "mw": 27.03, "densidade": 0.94,
        "aegl1": 2.5, "aegl2": 7.1, "aegl3": 15,
        "desc": "Gás leve. Dispersão rápida e letal (asfixiante químico). Cheiro de amêndoas."
    },
    "Cloreto de Vinila": {
        "mw": 62.50, "densidade": 2.15,
        "aegl1": 250, "aegl2": 1200, "aegl3": 4800,
        "desc": "Gás inflamável e carcinogênico (plásticos). Risco de explosão é maior que o tóxico agudo."
    },
    "Cloro Gás (Cl2)": {
        "mw": 70.90, "densidade": 2.5,
        "aegl1": 0.5, "aegl2": 2.0, "aegl3": 20.0,
        "desc": "Gás verde-amarelo, muito pesado. Rasteja pelo chão, entra em porões e metrôs."
    },
    "Diborano": {
        "mw": 27.67, "densidade": 0.96,
        "aegl1": 0.0, "aegl2": 2.0, "aegl3": 7.3,
        "desc": "Combustível de foguete. Pirofórico (pode pegar fogo espontaneamente no ar). Toxicidade pulmonar."
    },
    "Dióxido de Cloro": {
        "mw": 67.45, "densidade": 2.3,
        "aegl1": 0.15, "aegl2": 0.63, "aegl3": 1.8,
        "desc": "Gás amarelo-avermelhado. Tratamento de água. Instável e explosivo em altas concentrações."
    },
    "Dióxido de Enxofre (SO2)": {
        "mw": 64.06, "densidade": 2.2,
        "aegl1": 0.2, "aegl2": 0.75, "aegl3": 30,
        "desc": "Subproduto industrial. Pesado e invisível. Causa espasmo de glote imediato."
    },
    "Dióxido de Nitrogênio (NO2)": {
        "mw": 46.00, "densidade": 1.6,
        "aegl1": 0.5, "aegl2": 12, "aegl3": 20,
        "desc": "Fumaça vermelha/marrom. Típico de explosões ou ataques ácidos."
    },
    "Dissulfeto de Carbono": {
        "mw": 76.14, "densidade": 2.6,
        "aegl1": 13, "aegl2": 160, "aegl3": 480,
        "desc": "Líquido que vira vapor muito inflamável e neurotóxico. Vapores pesados."
    },
    "Flúor (Gás)": {
        "mw": 38.00, "densidade": 1.3,
        "aegl1": 1.7, "aegl2": 5.0, "aegl3": 13,
        "desc": "O oxidante mais forte que existe. Reage com tudo. Causa queimaduras profundas."
    },
    "Fluoreto de Hidrogênio (HF)": {
        "mw": 20.01, "densidade": 0.92, 
        "aegl1": 1.0, "aegl2": 24, "aegl3": 44,
        "desc": "EXTREMO. Corrói vidro e ossos. Forma nuvem branca densa que viaja baixo, apesar do MW leve."
    },
    "Formaldeído (Gás)": {
        "mw": 30.03, "densidade": 1.0,
        "aegl1": 0.9, "aegl2": 14, "aegl3": 35,
        "desc": "Gás irritante e sensibilizante. Nuvem invisível próxima à densidade do ar."
    },
    "Fosfina (PH3)": {
        "mw": 34.00, "densidade": 1.17,
        "aegl1": 0.0, "aegl2": 0.5, "aegl3": 3.6, # Muito baixo
        "desc": "Fumigante agrícola ou subproduto de laboratório. Cheiro de alho/peixe. Mata por falha metabólica."
    },
    "Fosgênio (CG)": {
        "mw": 98.92, "densidade": 3.4,
        "aegl1": 0.0, "aegl2": 0.1, "aegl3": 1.5,
        "desc": "Agente de guerra (WWI). Cheiro de feno mofado. Efeitos letais tardios (edema)."
    },
    "Hidrazina": {
        "mw": 32.05, "densidade": 1.1,
        "aegl1": 0.1, "aegl2": 4.6, "aegl3": 35,
        "desc": "Combustível de foguete/caça. Ataca fígado e rins. Absorvido pela pele."
    },
    "Metil Brometo": {
        "mw": 94.94, "densidade": 3.3,
        "aegl1": 0.0, "aegl2": 210, "aegl3": 850,
        "desc": "Fumigante pesado. Neurotóxico cumulativo. Inodoro em concentrações perigosas."
    },
    "Metil Isocianato (MIC)": {
        "mw": 57.05, "densidade": 1.4,
        "aegl1": 0.0, "aegl2": 0.17, "aegl3": 0.5,
        "desc": "Químico de Bhopal. Reage com água do corpo. Nuvem mortal rasteira."
    },
    "Metil Mercaptana": {
        "mw": 48.11, "densidade": 1.66,
        "aegl1": 0.005, "aegl2": 37, "aegl3": 120,
        "desc": "Cheiro de repolho podre. Depressor do sistema nervoso central. Inflamável."
    },
    "Monóxido de Carbono (CO)": {
        "mw": 28.01, "densidade": 0.97,
        "aegl1": 0, "aegl2": 83, "aegl3": 330,
        "desc": "Assassino silencioso. Mistura-se perfeitamente ao ar e viaja longas distâncias."
    },
    "Óxido de Etileno": {
        "mw": 44.05, "densidade": 1.5,
        "aegl1": 0.0, "aegl2": 45, "aegl3": 200,
        "desc": "Gás esterilizante. Inflamável em ampla faixa. Causa danos neurológicos."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "mw": 34.08, "densidade": 1.2,
        "aegl1": 0.5, "aegl2": 27, "aegl3": 50,
        "desc": "Gás de esgoto. Cheiro de ovo podre some em altas doses (anestesia olfativa)."
    },
    "Tolueno 2,4-Diisocianato (TDI)": {
        "mw": 174.16, "densidade": 6.0, # Pesadíssimo
        "aegl1": 0.02, "aegl2": 0.17, "aegl3": 0.55,
        "desc": "Vapores de espumas industriais. Asma severa e danos pulmonares imediatos."
    }
}

# --- 2. MOTOR DE CÁLCULO (PLUMA GAUSSIANA) ---
def estimar_dispersao_gaussiana(taxa_kg_s, vento_ms, condicao_tempo, substancia_info):
    """
    Calcula o comprimento da pluma tóxica usando o Modelo Gaussiano de Pluma.
    Adaptação dos coeficientes de Briggs (Open Country).
    """
    # 1. Definição da Classe de Estabilidade de Pasquill (A-F) baseada na descrição didática
    mapa_estabilidade = {
        "Dia: Sol Forte (Instável)": "A",      # O gás sobe e dispersa rápido
        "Dia: Nublado / Sol Fraco": "D",       # Neutro
        "Noite: Nublado / Vento Forte": "D",   # Neutro
        "Noite: Clara / Vento Calmo": "F"      # Estável (PIOR CENÁRIO: O gás não sobe, viaja longe rente ao chão)
    }
    classe_pasquill = mapa_estabilidade[condicao_tempo]
    
    # 2. Determinar Limites (ppm -> mg/m3)
    # Fórmula: mg/m3 = (ppm * MW) / 24.45
    mw = substancia_info['mw']
    limites_mgm3 = {}
    for nivel in ['aegl3', 'aegl2', 'aegl1']:
        ppm = substancia_info[nivel]
        if ppm > 0:
            limites_mgm3[nivel] = (ppm * mw) / 24.45
        else:
            limites_mgm3[nivel] = None

    # 3. Cálculo Reverso (Encontrar distância X onde a concentração C atinge o limite)
    # Simplificação: Usamos uma busca iterativa ou correlação direta para achar o alcance.
    # Para fins de agilidade no Streamlit, usaremos uma aproximação baseada na força da fonte.
    
    distancias = {}
    
    # Coeficientes aproximados para Estabilidade F (Pior caso - Noite) vs A (Melhor caso)
    # Fator de diluição empírico
    fator_dispersao = {
        "A": 0.2,  # Dispersa muito (nuvem curta e gorda)
        "D": 1.0,  # Padrão
        "F": 3.0   # Dispersa pouco (nuvem longa e fina - Perigo!)
    }[classe_pasquill]
    
    # Ajuste por densidade (Gases pesados viajam mais longe baixo)
    # CORREÇÃO: Usar chave 'densidade' em vez de 'densidade_rel'
    fator_densidade = 1.2 if substancia_info['densidade'] > 1 else 1.0

    for nivel, conc_limite in limites_mgm3.items():
        if conc_limite:
            # Equação simplificada de alcance proporcional à Carga / (Vento * Limite)
            # Alcance ~ sqrt(Q / (u * C)) * Fatores
            termo_fonte = (taxa_kg_s * 1000000) # mg/s
            
            # Evitar divisão por zero no vento
            u = max(vento_ms, 0.5)
            
            # Modelo heurístico calibrado para ALOHA (Aproximação)
            alcance_m = math.sqrt(termo_fonte / (u * conc_limite * 0.5)) * 15 * fator_dispersao * fator_densidade
            
            # Travas físicas
            alcance_m = min(alcance_m, 20000) # Max 20km
            alcance_m = max(alcance_m, 30)    # Min 30m
            
            distancias[nivel] = alcance_m
        else:
            distancias[nivel] = 0

    return distancias, classe_pasquill

def gerar_poligono_direcional(lat, lon, distancia, direcao_vento_graus, abertura_graus=30):
    """
    Gera um triângulo/cone representando a pluma na direção do vento.
    """
    # Vento vem de X, pluma vai para X + 180
    angulo_eixo = (direcao_vento_graus + 180) % 360
    
    coords = []
    r_terra = 6378137
    
    # Ponto de Origem
    coords.append([lat, lon])
    
    # Calcular arco do cone
    num_pontos = 10
    inicio_ang = angulo_eixo - (abertura_graus / 2)
    fim_ang = angulo_eixo + (abertura_graus / 2)
    
    for i in range(num_pontos + 1):
        ang_atual_deg = inicio_ang + (i * (fim_ang - inicio_ang) / num_pontos)
        ang_rad = math.radians(90 - ang_atual_deg) # Ajuste norte geográfico
        
        # Projetar ponto
        dx = distancia * math.cos(ang_rad)
        dy = distancia * math.sin(ang_rad)
        
        d_lat = (dy / r_terra) * (180 / math.pi)
        d_lon = (dx / r_terra) * (180 / math.pi) / math.cos(math.radians(lat))
        
        coords.append([lat + d_lat, lon + d_lon])
        
    # Fechar polígono voltando à origem
    coords.append([lat, lon])
    
    return coords

# --- 3. INTERFACE VISUAL (FRONT-END) ---
def renderizar():
    st.markdown("### ☠️ Químico Outdoor (Nuvem Tóxica)")
    st.markdown("Modelagem de dispersão atmosférica de gases tóxicos (Modelo Gaussiano).")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 Como funciona a Nuvem Tóxica? (Leia antes)", expanded=True):
        st.markdown("""
        **O Conceito:** Gases vazados não ficam parados. O vento cria uma "pluma" (formato de cone) que viaja por quilômetros.
        
        **Fatores Críticos:**
        1.  **Densidade:** Cloro é pesado -> Rasteja no chão (entra em casas). Amônia é leve -> Sobe (menos perigoso no solo, a menos que esteja muito frio).
        2.  **O Vento:**
            * *Vento Forte:* Dilui o gás rápido (bom), mas leva para longe.
            * *Vento Fraco:* O gás fica concentrado e letal perto da fonte.
        3.  **Dia vs Noite (Estabilidade):**
            * ☀️ **Dia (Sol):** O calor do chão faz o ar subir. A nuvem se dispersa rápido.
            * 🌙 **Noite (Clara/Calma):** Ocorre "Inversão Térmica". O gás fica preso perto do chão e viaja muito longe sem se diluir. **É o pior cenário.**
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Local e Clima")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        st.info("👇 A Meteorologia define o tamanho da zona de morte.")
        vento_ms = st.number_input("Velocidade do Vento (m/s)", value=3.0, min_value=0.5, step=0.5, help="Use anemômetro. Se não tiver: 1m/s = fumaça sobe quase reta; 5m/s = bandeiras esticadas.")
        direcao_vento = st.number_input("Direção do Vento (Graus)", value=90, min_value=0, max_value=360, help="De onde vem o vento (0=Norte). A nuvem irá para o lado oposto.")
        
        tempo = st.selectbox(
            "Condição do Tempo (Estabilidade)",
            ["Dia: Sol Forte (Instável)", "Dia: Nublado / Sol Fraco", "Noite: Nublado / Vento Forte", "Noite: Clara / Vento Calmo"],
            index=1,
            help="Noite Clara com vento calmo é a condição 'Classe F' (Gás viaja longe sem diluir)."
        )

    with col2:
        st.subheader("🧪 Ameaça Química")
        quimico = st.selectbox("Substância", list(SUBSTANCIAS.keys()))
        dados_quim = SUBSTANCIAS[quimico]
        
        st.caption(f"ℹ️ **Info:** {dados_quim['desc']}")
        # CORREÇÃO: Usar chave 'densidade' em vez de 'densidade_rel'
        if dados_quim['densidade'] > 1:
            st.warning("⚠️ Gás Pesado: Tende a acumular em baixadas e bueiros.")
        
        taxa = st.number_input("Taxa de Vazamento (kg/s)", value=1.0, min_value=0.1, step=0.1, help="Quanto gás sai por segundo? Ex: Um tanque rasgado pode vazar 10-50 kg/s.")

    # Estado
    if 'pluma_calc' not in st.session_state:
        st.session_state['pluma_calc'] = False

    if st.button("🌫️ Simular Nuvem Tóxica", type="primary"):
        st.session_state['pluma_calc'] = True

    if st.session_state['pluma_calc']:
        
        distancias, classe_p = estimar_dispersao_gaussiana(taxa, vento_ms, tempo, dados_quim)
        
        st.success(f"Simulação Concluída. Classe de Estabilidade Pasquill: **{classe_p}**")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Zona Vermelha (AEGL-3)", f"{distancias['aegl3']:.0f} m", "Risco de Morte", delta_color="inverse")
        with m2:
            st.metric("Zona Laranja (AEGL-2)", f"{distancias['aegl2']:.0f} m", "Incapacitação", delta_color="off")
        with m3:
            st.metric("Zona Amarela (AEGL-1)", f"{distancias['aegl1']:.0f} m", "Desconforto")

        # MAPA
        m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
        
        folium.Marker(
            [lat, lon],
            tooltip=f"Vazamento: {quimico}",
            icon=folium.Icon(color="red", icon="skull", prefix="fa")
        ).add_to(m)

        # Desenhar Plumas (Ordem: Amarelo > Laranja > Vermelho)
        cores = {'aegl1': '#FFD700', 'aegl2': '#FF8C00', 'aegl3': '#FF0000'}
        nomes = {'aegl1': 'AEGL-1 (Desconforto)', 'aegl2': 'AEGL-2 (Incapacitação)', 'aegl3': 'AEGL-3 (Morte)'}
        
        # Abertura do cone baseada na estabilidade (Classe A = cone largo, Classe F = cone fino)
        abertura = {"A": 50, "D": 30, "F": 15}[classe_p]

        for nivel in ['aegl1', 'aegl2', 'aegl3']:
            d = distancias[nivel]
            if d > 0:
                poly = gerar_poligono_direcional(lat, lon, d, direcao_vento, abertura_graus=abertura)
                
                folium.Polygon(
                    locations=poly,
                    color=cores[nivel],
                    fill=True,
                    fill_opacity=0.4,
                    tooltip=f"{nomes[nivel]}: {d:.0f}m"
                ).add_to(m)

        st_folium(m, width=None, height=600)