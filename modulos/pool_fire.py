import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

# =============================================================================
# 1. BANCO DE DADOS DE COMBUSTÍVEIS
# =============================================================================
# Propriedades para cálculo de queima
# Taxa de Queima (Burn Rate): kg/m²/s
# Hc (Calor de Combustão): kJ/kg
# Densidade: kg/m³
COMBUSTIVEIS = {
    "Acetaldeído": {
        "burn_rate": 0.045, 
        "H_c": 25000, 
        "density": 780,
        "desc": "Líquido extremamente inflamável. Queima rápida e volátil. Risco de reignição."
    },
    "Acetato de Etila": {
        "burn_rate": 0.038, 
        "H_c": 23600, 
        "density": 902,
        "desc": "Solvente comum. Chama amarelada com fumaça moderada."
    },
    "Acetona": {
        "burn_rate": 0.041, 
        "H_c": 25800, 
        "density": 791,
        "desc": "Solvente industrial. Queima limpa e rápida, fácil de extinguir com água (miscível)."
    },
    "Benzeno": {
        "burn_rate": 0.085, 
        "H_c": 40100, 
        "density": 876,
        "desc": "Chama muito fuliginosa (fumaça preta densa). Alta taxa de radiação térmica."
    },
    "Ciclohexano": {
        "burn_rate": 0.070, 
        "H_c": 43400, 
        "density": 779,
        "desc": "Queima similar à gasolina. Chama intensa e quente."
    },
    "Diesel / Querosene": {
        "burn_rate": 0.045, 
        "H_c": 44400, 
        "density": 850,
        "desc": "Queima mais lenta que a gasolina, mas libera muito calor por longo tempo. Fumaça preta."
    },
    "Dissulfeto de Carbono": {
        "burn_rate": 0.110, 
        "H_c": 13000, 
        "density": 1260,
        "desc": "EXTREMO. Queima com chama azulada quase invisível. Taxa de queima altíssima. Gases tóxicos (SO2)."
    },
    "Estireno": {
        "burn_rate": 0.064, 
        "H_c": 39000, 
        "density": 906,
        "desc": "Monomero de plásticos. Queima com muita fuligem. Pode polimerizar violentamente se aquecido."
    },
    "Etanol (Álcool)": {
        "burn_rate": 0.015, 
        "H_c": 26800, 
        "density": 789,
        "desc": "Chama quase invisível (azulada) de dia. Menor radiação térmica, mas difícil visualização."
    },
    "Gasolina": {
        "burn_rate": 0.055, 
        "H_c": 43700, 
        "density": 740,
        "desc": "Referência de incêndio. Queima muito rápida com chama alta e muita fumaça preta."
    },
    "GPL (Liquefeito)": {
        "burn_rate": 0.099, 
        "H_c": 46000, 
        "density": 550,
        "desc": "Vazamento de gás liquefeito. Vaporiza e queima violentamente com turbulência."
    },
    "Hexano": {
        "burn_rate": 0.074, 
        "H_c": 44700, 
        "density": 655,
        "desc": "Alta taxa de queima. Solvente comum em indústrias de extração de óleo vegetal."
    },
    "Isopropanol (IPA)": {
        "burn_rate": 0.035, 
        "H_c": 30500, 
        "density": 786,
        "desc": "Álcool isopropílico. Queima um pouco mais 'sujo' (amarelado) que o etanol."
    },
    "Jet A-1 (Combustível de Aviação)": {
        "burn_rate": 0.050, 
        "H_c": 43000, 
        "density": 804,
        "desc": "Querosene de aviação. Incêndios de grande porte, muito difíceis de combater (alta energia)."
    },
    "Metanol": {
        "burn_rate": 0.017, 
        "H_c": 20000, 
        "density": 792,
        "desc": "Chama invisível e baixo calor radiante. Perigoso pois as vítimas entram no fogo sem ver."
    },
    "Petróleo Bruto (Crude Oil)": {
        "burn_rate": 0.048, 
        "H_c": 42600, 
        "density": 870,
        "desc": "Incêndio complexo. Risco de Boilover (expulsão violenta do óleo) se houver água no fundo."
    },
    "Tolueno": {
        "burn_rate": 0.062, 
        "H_c": 40500, 
        "density": 867,
        "desc": "Solvente de tintas. Chama avermelhada com fumaça densa."
    },
    "Xileno": {
        "burn_rate": 0.068, 
        "H_c": 40800, 
        "density": 860,
        "desc": "Solvente aromático. Comportamento similar ao Tolueno, queima intensa."
    }
}

# Limites de Radiação Térmica (kW/m²) - Fonte: CCPS / TNO Green Book
LIMITES_TERMICOS = {
    "Zona Letal (Morte/Danos Estuturais)": {
        "fluxo": 12.5, 
        "cor": "#FF0000", # Vermelho
        "desc": "Madeira pega fogo espontaneamente. Plástico derrete. Morte em segundos."
    },
    "Zona de Lesão (Queimaduras Graves)": {
        "fluxo": 5.0, 
        "cor": "#FF8C00", # Laranja
        "desc": "Queimadura de 2º grau em 45 segundos. Dor insuportável imediata. Bombeiros precisam de roupa de aproximação."
    },
    "Zona de Alerta (Segurança Pública)": {
        "fluxo": 1.5, 
        "cor": "#FFD700", # Amarelo
        "desc": "Seguro para evacuação. Equivalente a um dia de sol muito forte na praia ao meio-dia."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (MUDAN & CROCE SIMPLIFICADO)
# =============================================================================
def calcular_pool_fire(area_poca, material):
    """
    Calcula a radiação térmica usando o modelo de Fonte Pontual (Point Source Model),
    que é adequado para distâncias de segurança (> 2 diâmetros da poça).
    """
    # 1. Dados Iniciais
    m_rate = material['burn_rate'] # kg/m2/s
    Hc = material['H_c']           # kJ/kg
    
    # Diâmetro equivalente (para fins de cálculo de chama)
    diametro = math.sqrt(4 * area_poca / math.pi)
    
    # 2. Taxa de Liberação de Calor Total (HRR - Heat Release Rate)
    # Q = m" * Area * Hc
    # Fator de eficiência (fração irradiada): Geralmente 0.30 a 0.40 para hidrocarbonetos
    eta = 0.35 
    Q_total = m_rate * area_poca * Hc * eta # kW (Kilowatts irradiados)

    # 3. Altura da Chama (Correlação de Thomas)
    # H/D = 42 * (m" / (rho_ar * sqrt(g*D)))^0.61
    rho_ar = 1.225
    g = 9.81
    
    termo_thomas = m_rate / (rho_ar * math.sqrt(g * diametro))
    altura_chama = diametro * 42 * (termo_thomas ** 0.61)
    
    # 4. Cálculo das Distâncias para cada Fluxo Crítico (Lei do Inverso do Quadrado)
    # I = Q / (4 * pi * r^2)  -->  r = sqrt(Q / (4 * pi * I))
    # Onde I é o fluxo alvo (kW/m2)
    
    raios = {}
    for zona, dados in LIMITES_TERMICOS.items():
        fluxo_alvo = dados['fluxo']
        
        # Distância do centro da chama
        dist = math.sqrt(Q_total / (4 * math.pi * fluxo_alvo))
        
        # Ajuste: A distância deve ser contada a partir da borda da poça ou do centro?
        # Para segurança, o Point Source conta do centro.
        # Se a distância for menor que o raio da poça, o modelo quebra (estamos dentro do fogo).
        raio_poca = diametro / 2
        if dist < raio_poca:
            dist = raio_poca + 1 # Segurança mínima
            
        raios[zona] = dist
        
    return raios, altura_chama, diametro, Q_total

def estimar_area_poca(massa_kg, densidade):
    """
    Se o usuário não sabe a área, estimamos considerando derramamento livre.
    Solo plano não permeável: espessura média de 1cm (0.01m).
    """
    volume = massa_kg / densidade # m3
    espessura_media = 0.01 # 1 cm
    area = volume / espessura_media
    return area

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🔥 Pool Fire (Incêndio em Poça)")
    st.markdown("Modelagem de radiação térmica de líquidos inflamáveis derramados.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 Entendendo o Fogo: Poça Confinada vs. Livre", expanded=True):
        st.markdown("""
        **O Cenário:** Um líquido inflamável vaza e pega fogo. O calor se espalha em todas as direções.
        
        **Fatores Críticos:**
        1.  **Confinamento:**
            * *Dique (Bacia):* O líquido fica preso numa área fixa. O fogo dura mais tempo, mas a área é menor.
            * *Chão Aberto:* O líquido se espalha até ficar bem fininho (aprox. 1cm). A poça fica gigante, o fogo é enorme, mas acaba rápido.
        2.  **O Perigo (Radiação Térmica - kW/m²):**
            * Não é a temperatura do ar, é a radiação (como o calor do sol na pele, mas 1000x mais forte).
            * **12.5 kW/m²:** Morte rápida. Estruturas de madeira pegam fogo.
            * **5.0 kW/m²:** Limite para bombeiros com roupa de combate.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Localização")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        tipo_combustivel = st.selectbox("Combustível", list(COMBUSTIVEIS.keys()))
        dados_comb = COMBUSTIVEIS[tipo_combustivel]
        st.caption(f"ℹ️ {dados_comb['desc']}")

    with col2:
        st.subheader("⛽ Vazamento")
        
        modo_calculo = st.radio("Tipo de Vazamento:", ["Derramamento Livre (Chão)", "Poça Confinada (Dique)"])
        
        area_calc = 0.0
        
        if modo_calculo == "Derramamento Livre (Chão)":
            massa = st.number_input("Massa Vazada (kg)", value=1000.0, step=100.0, help="Quantidade total no tanque.")
            # Cálculo automático da área
            area_calc = estimar_area_poca(massa, dados_comb['density'])
            st.info(f"💧 O líquido vai se espalhar cobrindo aprox. **{area_calc:.1f} m²**.")
            
        else:
            area_calc = st.number_input("Área do Dique (m²)", value=20.0, step=5.0, help="Área da bacia de contenção.")
            st.caption("Em diques, a poça não cresce, mas fica mais funda.")

    # Estado
    if 'fire_calc' not in st.session_state: st.session_state['fire_calc'] = False
    
    if st.button("🔥 Simular Incêndio", type="primary", use_container_width=True):
        st.session_state['fire_calc'] = True

    if st.session_state['fire_calc']:
        # Cálculos
        raios, altura, diametro, potencia = calcular_pool_fire(area_calc, dados_comb)
        
        st.markdown("#### 📊 Resultados da Análise Témica")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Altura da Chama", f"{altura:.1f} m", "Visível a km")
        k2.metric("Diâmetro do Fogo", f"{diametro:.1f} m", "Base da Poça")
        k3.metric("Potência Irradiada", f"{potencia/1000:.1f} MW", "Energia")

        st.write("---")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Letal (12.5 kW/m²)", f"{raios['Zona Letal (Morte/Danos Estuturais)']:.1f} m", "Evacuar Já", delta_color="inverse")
        c2.metric("Zona Lesão (5 kW/m²)", f"{raios['Zona de Lesão (Queimaduras Graves)']:.1f} m", "Combate", delta_color="off")
        c3.metric("Zona Alerta (1.5 kW/m²)", f"{raios['Zona de Alerta (Segurança Pública)']:.1f} m", "Público")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=18, tiles="OpenStreetMap")
        
        # Marcador do Fogo
        folium.Marker(
            [lat, lon], 
            tooltip=f"Incêndio: {tipo_combustivel}",
            icon=folium.Icon(color="red", icon="fire", prefix="fa")
        ).add_to(m)
        
        # Desenhar Zonas (Do maior para o menor)
        zonas_ordem = [
            ("Zona de Alerta (Segurança Pública)", LIMITES_TERMICOS["Zona de Alerta (Segurança Pública)"]),
            ("Zona de Lesão (Queimaduras Graves)", LIMITES_TERMICOS["Zona de Lesão (Queimaduras Graves)"]),
            ("Zona Letal (Morte/Danos Estuturais)", LIMITES_TERMICOS["Zona Letal (Morte/Danos Estuturais)"])
        ]
        
        for nome, dados in zonas_ordem:
            r = raios[nome]
            folium.Circle(
                [lat, lon],
                radius=r,
                color=dados['cor'],
                fill=True,
                fill_opacity=0.3,
                tooltip=f"{nome}: {r:.1f}m ({dados['fluxo']} kW/m²)"
            ).add_to(m)
            
        st_folium(m, width=None, height=600)

