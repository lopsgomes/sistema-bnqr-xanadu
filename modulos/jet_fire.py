import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

# =============================================================================
# 1. BANCO DE DADOS: GASES PRESSURIZADOS
# =============================================================================
# Propriedades:
# Hc: Calor de Combustão (kJ/kg)
# MW: Peso Molecular (g/mol)
# Cp/Cv (Gamma): Razão de calores específicos (aprox 1.3-1.4)
# T_comb: Temperatura aproximada da chama (K)
SUBSTANCIAS_JET = {
    "Gás Natural (Metano)": {
        "Hc": 50000, "mw": 16.04, "gamma": 1.31,
        "desc": "Tubulações de rua (GNV/Gás Encanado). Chama azulada/amarela, muito leve, tende a subir."
    },
    "Propano (GLP Industrial)": {
        "Hc": 46350, "mw": 44.1, "gamma": 1.13,
        "desc": "Tanques industriais e P45. Chama luminosa, gera fuligem. Mais pesado que o ar."
    },
    "Butano (GLP Doméstico)": {
        "Hc": 45750, "mw": 58.12, "gamma": 1.09,
        "desc": "Botijão de cozinha (P13). Similar ao propano, chama amarela intensa."
    },
    "Hidrogênio": {
        "Hc": 120000, "mw": 2.01, "gamma": 1.41,
        "desc": "Indústria química e baterias. PERIGO INVISÍVEL: A chama é quase transparente de dia e emite UV intenso."
    },
    "Acetileno": {
        "Hc": 48200, "mw": 26.04, "gamma": 1.26,
        "desc": "Solda industrial. Chama extremamente quente e instável. Risco de detonação."
    },
    "Etileno": {
        "Hc": 47100, "mw": 28.05, "gamma": 1.24,
        "desc": "Polo petroquímico. Queima rápida e muito reativa."
    },
    "Amônia (Gás)": {
        "Hc": 18600, "mw": 17.03, "gamma": 1.31,
        "desc": "Refrigeração industrial. Difícil de acender, mas forma Jet Fire se houver calor externo."
    },
    "Monóxido de Carbono": {
        "Hc": 10100, "mw": 28.01, "gamma": 1.40,
        "desc": "Siderurgia. Gás tóxico e inflamável. Chama azulada."
    }
}

# Limites de Radiação Térmica (kW/m²) - API 521 / CCPS
LIMITES_TERM_JET = {
    "Dano Estrutural / Morte (12.5 kW/m²)": {
        "fluxo": 12.5, "cor": "#FF0000", 
        "desc": "Morte rápida. Plástico derrete, madeira inflama. Falha de estruturas metálicas sem proteção."
    },
    "Combate a Incêndio (5.0 kW/m²)": {
        "fluxo": 5.0, "cor": "#FF8C00", 
        "desc": "Limite para bombeiros com roupa de aproximação (Bunker Gear)."
    },
    "Evacuação Segura (1.5 kW/m²)": {
        "fluxo": 1.5, "cor": "#FFD700", 
        "desc": "Público geral pode sentir desconforto, mas consegue fugir."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (MODELO DE PONTO DA API 521)
# =============================================================================
def calcular_vazao_sonica(diametro_mm, pressao_bar, temperatura_c, gas_props):
    """
    Estima a vazão mássica (kg/s) de um gás vazando por um orifício.
    Assume escoamento sônico (Choked Flow), que é o caso em vazamentos de alta pressão.
    """
    # Conversões
    P_pa = pressao_bar * 100000 # Pascal
    T_k = temperatura_c + 273.15
    Area = math.pi * ((diametro_mm / 1000.0 / 2) ** 2)
    MW = gas_props['mw'] / 1000.0 # kg/mol
    Gamma = gas_props['gamma']
    R = 8.314 # J/(mol.K)
    Cd = 0.85 # Coeficiente de descarga (orifício irregular/quebrado)

    # Densidade do gás na pressão do tanque
    rho = (P_pa * MW) / (R * T_k)

    # Fórmula de Vazão Sônica (Choked Flow)
    termo_compressibilidade = (2 / (Gamma + 1)) ** ((Gamma + 1) / (2 * (Gamma - 1)))
    vazao_kg_s = Cd * Area * P_pa * math.sqrt(Gamma * MW / (R * T_k)) * termo_compressibilidade
    
    # Se a pressão for muito baixa, a fórmula muda, mas para "Jet Fire" assumimos alta pressão.
    return vazao_kg_s

def calcular_jet_fire(vazao_kg_s, gas_props):
    """
    Calcula comprimento da chama e zonas de radiação.
    Correlação Simplificada (Lowesmith and Moorhouse / API 521).
    """
    Hc = gas_props['Hc']
    
    # 1. Taxa de Liberação de Calor (Q em kW)
    Q_kw = vazao_kg_s * Hc
    
    # 2. Comprimento da Chama (L em metros)
    # Correlação comum: L = 15 * D * sqrt(P) ... mas baseada em Q é mais robusta para fins didáticos.
    # API 521 simplificado: L (m) ≈ 0.235 * (Q_kw)^(0.4) para gases leves?
    # Vamos usar a correlação de Chamberlain (1987) adaptada:
    # L_b = 18.5 * (m_dot)^0.41 ... Aproximação aceitável para hidrocarbonetos.
    # Ajuste empírico para visualização consistente:
    comprimento_chama = 15.0 * (vazao_kg_s ** 0.45) 
    
    # 3. Zonas de Radiação (Point Source Model)
    # Assume que todo calor irradia do CENTRO da chama (L/2).
    # Fração de radiação (F): Hidrogênio 0.15, Hidrocarbonetos 0.25-0.30
    F = 0.25
    if gas_props['mw'] < 4: F = 0.15 # Hidrogênio irradia menos calor (chama transparente)
    
    tau = 0.7 # Transmissividade atmosférica (média)
    
    Q_radiado = Q_kw * F * tau
    
    raios = {}
    for nome, dados in LIMITES_TERM_JET.items():
        fluxo_limite = dados['fluxo']
        # I = Q_rad / (4 * pi * r^2)  --> r = sqrt(Q_rad / (4 * pi * I))
        if fluxo_limite > 0:
            r = math.sqrt(Q_radiado / (4 * math.pi * fluxo_limite))
            raios[nome] = r
        else:
            raios[nome] = 0
            
    return comprimento_chama, Q_kw, raios

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🔥 Jet Fire (Incêndio em Jato)")
    st.markdown("Modelagem de vazamentos de gás pressurizado com ignição imediata.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O que é um Jet Fire?", expanded=True):
        st.markdown("""
        **O Fenômeno:** Imagine um maçarico gigante. O gás sai com tanta força (pressão) que forma uma língua de fogo longa e direcionada.
        
        **Características:**
        * 🔊 **Barulho:** Produz um ruído ensurdecedor (como turbina de avião).
        * 🔥 **Direcional:** O fogo aponta para onde o buraco estiver virado, mas o calor irradia para todos os lados.
        * 🛡️ **Dano:** Pode cortar estruturas metálicas e enfraquecer tanques vizinhos, causando um **BLEVE** (explosão secundária).
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Cenário")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        subs_nome = st.selectbox("Gás Envolvido", list(SUBSTANCIAS_JET.keys()))
        dados_gas = SUBSTANCIAS_JET[subs_nome]
        st.caption(f"ℹ️ {dados_gas['desc']}")

    with col2:
        st.subheader("⚙️ Dados do Vazamento")
        
        c2a, c2b = st.columns(2)
        pressao = c2a.number_input("Pressão (bar)", value=10.0, min_value=1.0, help="Pressão interna da tubulação/tanque.")
        diametro = c2b.number_input("Diâmetro do Furo (mm)", value=20.0, min_value=1.0, help="Tamanho do buraco ou válvula quebrada.")
        
        temp = st.slider("Temperatura do Gás (°C)", -50, 100, 25)

    # Botão
    if 'jet_calc' not in st.session_state: st.session_state['jet_calc'] = False
    
    if st.button("🔥 Acender o Maçarico", type="primary", use_container_width=True):
        st.session_state['jet_calc'] = True

    if st.session_state['jet_calc']:
        # 1. Calcular Vazão
        vazao = calcular_vazao_sonica(diametro, pressao, temp, dados_gas)
        
        # 2. Calcular Fogo
        comp_chama, potencia, raios = calcular_jet_fire(vazao, dados_gas)
        
        st.markdown("#### 📊 Análise do Jato")
        
        # Métricas
        k1, k2, k3 = st.columns(3)
        k1.metric("Vazão de Gás", f"{vazao*3600:.1f} kg/h", f"{vazao:.2f} kg/s")
        k2.metric("Comprimento da Chama", f"{comp_chama:.1f} metros", "Lança de Fogo", delta_color="inverse")
        k3.metric("Potência Térmica", f"{potencia/1000:.1f} MW", "Calor Total")
        
        st.write("---")
        
        # Zonas de Segurança
        c1, c2, c3 = st.columns(3)
        c1.metric("Raio Letal (12.5 kW)", f"{raios['Dano Estrutural / Morte (12.5 kW/m²)']:.1f} m", "Morte/Colapso", delta_color="inverse")
        c2.metric("Raio Combate (5.0 kW)", f"{raios['Combate a Incêndio (5.0 kW/m²)']:.1f} m", "Bombeiros", delta_color="off")
        c3.metric("Raio Público (1.5 kW)", f"{raios['Evacuação Segura (1.5 kW/m²)']:.1f} m", "Evacuação")

        if subs_nome == "Hidrogênio":
            st.warning("⚠️ **ALERTA DE HIDROGÊNIO:** A chama pode ser INVISÍVEL durante o dia. Use câmeras térmicas!")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=17, tiles="OpenStreetMap")
        
        # Marcador da Fonte
        folium.Marker(
            [lat, lon], 
            tooltip=f"Jet Fire: {subs_nome}",
            icon=folium.Icon(color="red", icon="fire", prefix="fa")
        ).add_to(m)
        
        # Desenhar Zonas (Círculos centrados na fonte - conservador, pois o jato pode girar)
        zonas_ordem = [
            ("Evacuação Segura (1.5 kW/m²)", LIMITES_TERM_JET["Evacuação Segura (1.5 kW/m²)"]),
            ("Combate a Incêndio (5.0 kW/m²)", LIMITES_TERM_JET["Combate a Incêndio (5.0 kW/m²)"]),
            ("Dano Estrutural / Morte (12.5 kW/m²)", LIMITES_TERM_JET["Dano Estrutural / Morte (12.5 kW/m²)"])
        ]
        
        for nome, dados in zonas_ordem:
            r = raios[nome]
            if r > 0.5:
                folium.Circle(
                    [lat, lon],
                    radius=r,
                    color=dados['cor'],
                    fill=True,
                    fill_opacity=0.3,
                    tooltip=f"{nome}: {r:.1f}m"
                ).add_to(m)
        
        # Representação da Chama (Linha grossa indicativa - assumindo direção Leste para visualização)
        # Apenas visual para dar noção de escala do comprimento
        ponto_final = [lat, lon + (comp_chama / 111000)] # Aproximando conversão m -> graus
        folium.PolyLine(
            [[lat, lon], ponto_final],
            color="yellow", weight=8, opacity=0.8,
            tooltip=f"Comprimento da Chama: {comp_chama:.1f}m"
        ).add_to(m)

        st_folium(m, width=None, height=600)