import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math

# =============================================================================
# 1. BANCO DE DADOS: SENSORES TÁTICOS
# =============================================================================
SENSORES = {
    "Câmera Térmica (FLIR)": {
        "fov": 57, 
        "uso": "Localizar vítimas pelo calor e identificar focos de incêndio ou vazamentos criogênicos."
    },
    "Detector de Radiação (Gama)": {
        "fov": 90, 
        "uso": "Mapear taxas de dose e localizar fontes órfãs ou áreas de deposição de fallout."
    },
    "Sniffer de Gás (Multi-Gás)": {
        "fov": 30, 
        "uso": "Detectar nuvens tóxicas e identificar a composição química da pluma."
    },
    "Câmera RGB (Alta Resolução)": {
        "fov": 80,
        "uso": "Reconhecimento visual detalhado de danos estruturais e leitura de placas de perigo."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO DE MISSÃO
# =============================================================================
def calcular_geometria_voo(altura, fov, largura_area, comprimento_area, sobreposicao):
    """Calcula os parâmetros da varredura aérea."""
    largura_sensor_solo = 2 * altura * math.tan(math.radians(fov / 2))
    distancia_entre_linhas = largura_sensor_solo * (1 - sobreposicao)
    num_passagens = math.ceil(largura_area / distancia_entre_linhas)
    distancia_total = num_passagens * comprimento_area
    return largura_sensor_solo, num_passagens, distancia_total

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🚁 Planejamento de Voo Drone (Survey)")
    st.markdown("Reconhecimento aéreo autônomo para mapeamento de áreas de risco.")
    st.markdown("---")

    # --- SEÇÃO 1: LOCALIZAÇÃO ---
    st.subheader("📍 1. Localização do Incidente")
    with st.expander("Configurar Coordenadas do Ponto Inicial", expanded=True):
        col_lat, col_lon = st.columns(2)
        lat_input = col_lat.number_input(
            "Latitude (Decimal)", 
            value=-22.8625, 
            format="%.6f",
            help="Exemplo: -22.8625. Coordenada norte-sul."
        )
        lon_input = col_lon.number_input(
            "Longitude (Decimal)", 
            value=-43.2245, 
            format="%.6f",
            help="Exemplo: -43.2245. Coordenada leste-oeste."
        )
        st.caption("💡 O drone iniciará o zigue-zague a partir deste ponto (Canto Inferior Esquerdo da área).")

    # --- SEÇÃO 2: PARÂMETROS TÉCNICOS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛠️ 2. Configuração do Sensor")
        sensor_nome = st.selectbox("Selecione o Sensor Embarcado", list(SENSORES.keys()))
        dados_sensor = SENSORES[sensor_nome]
        st.info(f"🎯 **Uso:** {dados_sensor['uso']}")
        
        altura_voo = st.slider("Altura de Voo (metros)", 10, 120, 30, help="Voo baixo = Mais detalhe / Voo alto = Mais rapidez.")
        sobreposicao = st.slider("Sobreposição Lateral (%)", 10, 80, 30, help="Quanto as faixas de imagem se cruzam.") / 100

    with col2:
        st.subheader("📐 3. Dimensões da Varredura")
        largura_m = st.number_input("Largura da Zona (metros)", value=200, step=50, help="Extensão no eixo Leste-Oeste.")
        comprimento_m = st.number_input("Comprimento da Zona (metros)", value=300, step=50, help="Extensão no eixo Norte-Sul.")
        velocidade = st.number_input("Velocidade do Drone (m/s)", value=5.0, step=1.0)

    # --- EXECUÇÃO ---
    if 'drone_calc' not in st.session_state: st.session_state['drone_calc'] = False
    
    if st.button("🗺️ Gerar Plano de Voo e Mapa", type="primary", use_container_width=True):
        st.session_state['drone_calc'] = True

    if st.session_state['drone_calc']:
        swath, passagens, dist_total = calcular_geometria_voo(altura_voo, dados_sensor['fov'], largura_m, comprimento_m, sobreposicao)
        tempo_min = (dist_total / velocidade) / 60
        
        st.write("---")
        st.markdown("### 📋 Resumo da Missão")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Largura da Faixa", f"{swath:.1f} m", "Visão do sensor no solo")
        m2.metric("Nº de Passagens", f"{passagens}", "Linhas de voo")
        m3.metric("Tempo de Voo", f"{tempo_min:.1f} min", "Estimado")

        if tempo_min > 20:
            st.warning("⚠️ **Alerta de Autonomia:** O tempo excede uma bateria comum. Planeje a troca.")
        else:
            st.success("✅ **Missão Viável** com uma única bateria.")

        # --- MAPA INTERATIVO ---
        st.subheader("🗺️ Visualização Tática do Padrão de Busca")
        
        # Criação do Mapa centrado na coordenada inserida
        m = folium.Map(location=[lat_input, lon_input], zoom_start=17)
        
        # Marcador do Ponto de Decolagem
        folium.Marker(
            [lat_input, lon_input], 
            tooltip="Ponto de Início (Home)",
            icon=folium.Icon(color="blue", icon="home")
        ).add_to(m)
        
        # Cálculo Geográfico da Área
        # 1 grau de latitude é aprox 111.000 metros
        dlat = (comprimento_m / 111000)
        # Longitude depende da latitude (cosseno)
        dlon = (largura_m / (111000 * math.cos(math.radians(lat_input))))
        
        # Desenhar o Polígono da Área de Busca
        folium.Rectangle(
            bounds=[[lat_input, lon_input], [lat_input + dlat, lon_input + dlon]],
            color="blue", 
            fill=True, 
            fill_opacity=0.1, 
            tooltip="Área de Cobertura Total"
        ).add_to(m)

        # Gerar e desenhar as linhas de varredura (Sweep Lines)
        for i in range(passagens):
            # Offset lateral proporcional à largura do sensor e sobreposição
            offset_m = i * (swath * (1 - sobreposicao))
            offset_lon = offset_m / (111000 * math.cos(math.radians(lat_input)))
            
            cor = "red" if i % 2 == 0 else "orange"
            folium.PolyLine(
                [[lat_input, lon_input + offset_lon], [lat_input + dlat, lon_input + offset_lon]],
                color=cor, 
                weight=3, 
                opacity=0.8,
                tooltip=f"Linha de Varredura {i+1}"
            ).add_to(m)

        st_folium(m, width=700, height=500)
        st.caption(f"📍 Missão planejada para: {lat_input:.6f}, {lon_input:.6f}")