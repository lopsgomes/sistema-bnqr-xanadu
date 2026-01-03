import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

# =============================================================================
# 1. BANCO DE DADOS: GASES E VAPORES INFLAMÁVEIS
# =============================================================================
# Propriedades:
# Hc: Calor de Combustão (kJ/kg)
# Reatividade: Classificação de quão fácil o gás detona (Baixa, Média, Alta)
SUBSTANCIAS_VCE = {
    "Gás Natural (Metano)": {
        "Hc": 50000, 
        "reatividade": "Baixa",
        "desc": "Sobe rápido. Difícil explodir ao ar livre, requer confinamento forte."
    },
    "Propano (GLP)": {
        "Hc": 46350, 
        "reatividade": "Média",
        "desc": "Mais pesado que o ar. Acumula em baixadas e esgotos. Explosão clássica."
    },
    "Butano": {
        "Hc": 45750, 
        "reatividade": "Média",
        "desc": "Gás de cozinha. Comportamento similar ao Propano."
    },
    "Gasolina (Vapores)": {
        "Hc": 44400, 
        "reatividade": "Média",
        "desc": "Evaporação de grandes derramamentos. Nuvem rasteira."
    },
    "Etileno": {
        "Hc": 47100, 
        "reatividade": "Alta",
        "desc": "Muito reativo. Acelera a chama rapidamente, gerando fortes explosões."
    },
    "Hidrogênio": {
        "Hc": 120000, 
        "reatividade": "Alta",
        "desc": "Detonação muito fácil. Onda de choque rápida e 'seca'."
    },
    "Acetileno": {
        "Hc": 48200, 
        "reatividade": "Alta",
        "desc": "Instável. Pode detonar com pouquíssima energia."
    },
    "Óxido de Etileno": {
        "Hc": 29000, 
        "reatividade": "Alta",
        "desc": "Pode explodir mesmo sem oxigênio (decomposição). Extremamente violento."
    }
}

# Limites de Sobrepressão (Overpressure) - PSI e BAR
# Fonte: EPA / CCPS "Yellow Book"
LIMITES_BLAST = {
    "Destruição Total / Ruptura Pulmão (10 psi)": {
        "psi": 10.0, "bar": 0.69, "cor": "#000000", # Preto
        "desc": "Demolição de prédios de concreto. Morte provável."
    },
    "Danos Graves / Ruptura Tímpano (5 psi)": {
        "psi": 5.0, "bar": 0.34, "cor": "#FF0000", # Vermelho
        "desc": "Paredes de alvenaria caem. Tímpanos estouram. Árvores arrancadas."
    },
    "Danos Médios / Derruba Pessoas (2 psi)": {
        "psi": 2.0, "bar": 0.14, "cor": "#FF8C00", # Laranja
        "desc": "Estruturas metálicas entortam. Pessoas são arremessadas. Destelhamento."
    },
    "Quebra de Vidros / Janelas (0.5 psi)": {
        "psi": 0.5, "bar": 0.03, "cor": "#FFD700", # Amarelo
        "desc": "Janelas quebram a quilômetros. Ferimentos por estilhaços."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (TNT EQUIVALENCE MODIFICADO)
# =============================================================================
def calcular_vce(massa_kg, gas_props, grau_confinamento):
    """
    Calcula os raios de sobrepressão baseado na massa da nuvem e no confinamento.
    Método: Equivalência TNT Ajustada por Eficiência (Yield Factor).
    """
    # 1. Definir Fator de Eficiência (Yield) baseado no cenário
    # Quanto mais obstáculos (tubos, paredes), maior a turbulência e a explosão.
    # Em campo aberto, a eficiência é quase zero (só fogo, sem blast).
    
    tabela_eficiencia = {
        "Campo Aberto (Sem Obstáculos)": 0.03,      # 3% (Quase só Flash Fire)
        "Urbano / Floresta (Obstáculos Médios)": 0.10, # 10% (Padrão industrial leve)
        "Refinaria / Processo (Muitos Tubos)": 0.20,   # 20% (Alta turbulência)
        "Confinado (Túnel / Bunker)": 0.40          # 40% (Devastador)
    }
    
    eficiencia = tabela_eficiencia[grau_confinamento]
    
    # Ajuste por reatividade química (Gases instáveis explodem melhor)
    if gas_props['reatividade'] == "Alta":
        eficiencia *= 1.3
    elif gas_props['reatividade'] == "Baixa":
        eficiencia *= 0.8
        
    # Trava de física (máximo teórico ~50% para nuvens de vapor)
    eficiencia = min(eficiencia, 0.5)

    # 2. Calcular Energia Equivalente em TNT
    # Energia = Massa * Hc * Eficiencia
    # 1 kg TNT = 4680 kJ
    energia_explosiva_kj = massa_kg * gas_props['Hc'] * eficiencia
    kg_tnt = energia_explosiva_kj / 4680.0
    
    # 3. Calcular Raios usando Lei de Escala de Hopkinson-Cranz
    # Z = R / W^(1/3)  -->  R = Z * W^(1/3)
    # Z é o "Scaled Distance" para cada sobrepressão.
    # Valores aproximados de Z para TNT (em m/kg^1/3):
    # 10 psi (0.69 bar) -> Z ~ 2.8
    # 5 psi (0.34 bar)  -> Z ~ 4.3
    # 2 psi (0.14 bar)  -> Z ~ 7.5
    # 0.5 psi (0.03 bar)-> Z ~ 22.0
    
    mapa_z = {
        10.0: 2.8,
        5.0: 4.3,
        2.0: 7.5,
        0.5: 22.0
    }
    
    raios = {}
    for nome, dados in LIMITES_BLAST.items():
        psi = dados['psi']
        z_factor = mapa_z.get(psi, 22.0)
        
        r = z_factor * (kg_tnt ** (1/3))
        raios[nome] = r
        
    return raios, kg_tnt, eficiencia

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### ☁️ VCE (Explosão de Nuvem de Vapor)")
    st.markdown("Modelagem de onda de choque gerada por ignição retardada de gás.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O Segredo do VCE: Por que demorou a explodir?", expanded=True):
        st.markdown("""
        **A Diferença Vital:**
        * **Jet Fire / Pool Fire:** O gás vaza e acende *na hora*. O risco é **CALOR**.
        * **VCE (Vapor Cloud Explosion):** O gás vaza, *não acende*, forma uma nuvem gigante que entra no meio dos prédios. Quando encontra uma faísca, a chama corre tão rápido que empurra o ar, criando uma **ONDA DE CHOQUE (Blast)**.
        
        **O Fator Confinamento:**
        Para haver explosão forte, a nuvem precisa de "obstáculos" (tubos, paredes, árvores) para gerar turbulência.
        * 🏕️ **Campo Aberto:** A nuvem queima devagar (Flash Fire). Pouca pressão.
        * 🏭 **Refinaria/Cidade:** A nuvem explode violentamente. Muita pressão.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Cenário")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        subs_nome = st.selectbox("Gás da Nuvem", list(SUBSTANCIAS_VCE.keys()))
        dados_gas = SUBSTANCIAS_VCE[subs_nome]
        st.caption(f"ℹ️ {dados_gas['desc']} (Reatividade: {dados_gas['reatividade']})")

    with col2:
        st.subheader("⚙️ Tamanho e Ambiente")
        massa = st.number_input("Massa na Nuvem (kg)", value=2000.0, step=500.0, help="Quanto gás vazou ANTES de acender?")
        
        confinamento = st.selectbox(
            "Grau de Confinamento / Obstáculos", 
            [
                "Campo Aberto (Sem Obstáculos)",
                "Urbano / Floresta (Obstáculos Médios)",
                "Refinaria / Processo (Muitos Tubos)",
                "Confinado (Túnel / Bunker)"
            ],
            index=1,
            help="Determina se será apenas um 'fogo' ou uma 'bomba'."
        )

    # Botão
    if 'vce_calc' not in st.session_state: st.session_state['vce_calc'] = False
    
    if st.button("💣 Detonar Nuvem", type="primary", use_container_width=True):
        st.session_state['vce_calc'] = True

    if st.session_state['vce_calc']:
        # Calcular
        raios, tnt_eq, efic = calcular_vce(massa, dados_gas, confinamento)
        
        st.markdown("#### 📊 Análise da Onda de Choque")
        
        # Métricas
        k1, k2, k3 = st.columns(3)
        k1.metric("Massa de Gás", f"{massa/1000:.1f} Ton", "Combustível")
        k2.metric("Eficiência da Explosão", f"{efic*100:.1f}%", f"Confinamento: {confinamento.split(' ')[0]}")
        k3.metric("Equivalência TNT", f"{tnt_eq/1000:.1f} Ton", "Energia Mecânica", delta_color="inverse")
        
        st.write("---")
        
        # Zonas de Impacto
        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Mortal (10 psi)", f"{raios['Destruição Total / Ruptura Pulmão (10 psi)']:.0f} m", "Colapso Total", delta_color="inverse")
        c2.metric("Tímpanos/Paredes (5 psi)", f"{raios['Danos Graves / Ruptura Tímpano (5 psi)']:.0f} m", "Danos Graves", delta_color="off")
        c3.metric("Quebra Vidros (0.5 psi)", f"{raios['Quebra de Vidros / Janelas (0.5 psi)']:.0f} m", "Estilhaços")

        if confinamento == "Campo Aberto (Sem Obstáculos)":
            st.info("💡 **Nota Tática:** Em campo aberto, a onda de choque é fraca. O risco principal seria o fogo (Flash Fire) dentro da nuvem, não a explosão à distância.")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
        
        # Marcador
        folium.Marker(
            [lat, lon], 
            tooltip=f"VCE: {subs_nome}",
            icon=folium.Icon(color="black", icon="cloud-meatball", prefix="fa")
        ).add_to(m)
        
        # Desenhar Zonas (Blast Rings)
        # Ordem: Amarelo (Maior) -> Laranja -> Vermelho -> Preto (Menor)
        zonas_ordem = [
            ("Quebra de Vidros / Janelas (0.5 psi)", LIMITES_BLAST["Quebra de Vidros / Janelas (0.5 psi)"]),
            ("Danos Médios / Derruba Pessoas (2 psi)", LIMITES_BLAST["Danos Médios / Derruba Pessoas (2 psi)"]),
            ("Danos Graves / Ruptura Tímpano (5 psi)", LIMITES_BLAST["Danos Graves / Ruptura Tímpano (5 psi)"]),
            ("Destruição Total / Ruptura Pulmão (10 psi)", LIMITES_BLAST["Destruição Total / Ruptura Pulmão (10 psi)"])
        ]
        
        for nome, dados in zonas_ordem:
            r = raios[nome]
            # Círculos de Blast: Apenas contorno (stroke) para diferenciar de pluma tóxica
            folium.Circle(
                [lat, lon],
                radius=r,
                color=dados['cor'],
                weight=3,
                fill=True,
                fill_opacity=0.2,
                tooltip=f"{nome}: {r:.0f}m ({dados['psi']} psi)"
            ).add_to(m)
        
        st_folium(m, width=None, height=600)