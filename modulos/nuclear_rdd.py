import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

# --- 1. BANCO DE DADOS DE ISÓTOPOS (CONHECIMENTO TÉCNICO) ---
ISOTOPOS = {
    "Césio-137 (Cs-137)": {
        "meia_vida": "30 anos", 
        "energia": "Gama/Beta", 
        "risco": "Contaminação de longo prazo (Goiânia). Liga-se ao solo quimicamente.",
        "uso": "Hospitais (Radioterapia antiga), Medidores de Nível Industriais."
    },
    "Cobalto-60 (Co-60)": {
        "meia_vida": "5.2 anos", 
        "energia": "Gama Muito Forte", 
        "risco": "Irradiação externa aguda. Morte rápida se alta dose.",
        "uso": "Esterilização de Alimentos, Radioterapia."
    },
    "Irídio-192 (Ir-192)": {
        "meia_vida": "73 dias", 
        "energia": "Gama", 
        "risco": "Queimaduras graves se tocado. Decai rápido (meses).",
        "uso": "Gamagrafia (Raio-X de soldas em tubulações)."
    },
    "Amerício-241 (Am-241)": {
        "meia_vida": "432 anos", 
        "energia": "Alfa/Gama", 
        "risco": "Perigo extremo se inalado (pó).",
        "uso": "Perfilagem de Poços de Petróleo, Para-raios antigos."
    },
    "Estrôncio-90 (Sr-90)": {
        "meia_vida": "28 anos", 
        "energia": "Beta Puro", 
        "risco": "Se ingerido, fixa-se nos ossos como cálcio.",
        "uso": "Geradores Termoelétricos (Faróis remotos, Satélites)."
    }
}

# Níveis de Contaminação no Solo (Ci/m2) - Baseados em manuais de resposta (IAEA/EPA)
LIMITES_INTERVENCAO = {
    "Evacuação Imediata": 0.01,    # Zona Quente (Vermelho)
    "Relocação Temporária": 0.001, # Zona Morna (Laranja)
    "Monitoramento/Abrigo": 0.0001 # Zona Fria/Alerta (Amarelo)
}

# --- 2. MOTOR DE CÁLCULO (PLUMA E GEOMETRIA) ---
def calcular_pluma_rdd(atividade_ci, explosivo_kg, vento_ms, direcao_graus):
    """
    Simula a dispersão de particulado radioativo (Gaussian Puff simplificado para deposição).
    """
    # 1. Altura da Nuvem (Fórmula de Church para explosões químicas)
    # H = 76 * (kg_TNT)^0.25
    altura_efetiva = 76 * (explosivo_kg ** 0.25)
    
    # 2. Termo Fonte (Release Fraction)
    # Em "Bombas Sujas", assume-se que 20% vira pó fino respirável/dispersível.
    # O resto (80%) são estilhaços grandes que caem na cratera.
    RF = 0.20 
    Q_efetivo = atividade_ci * RF
    
    # Velocidade de deposição típica para aerossóis (1 cm/s)
    v_d = 0.01 
    
    resultados = {}
    
    # Loop inteligente: calcula as 3 zonas automaticamente
    for nivel, limite in LIMITES_INTERVENCAO.items():
        # Inversão da equação de deposição para achar a distância (comprimento da pluma)
        # Lógica: Quanto mais forte a fonte (Q) e mais fraco o vento, maior a mancha.
        fator_forca = (Q_efetivo * v_d) / (vento_ms * limite)
        
        # Comprimento estimado da mancha no chão
        comprimento = math.sqrt(fator_forca) * 50 
        
        # Travas de segurança física (Limites do modelo)
        if comprimento < 20: comprimento = 20
        if comprimento > 15000: comprimento = 15000 # Limite de 15km
        
        # Largura da pluma (Abertura lateral devido à turbulência)
        largura = comprimento * 0.35 
        
        resultados[nivel] = {
            "comprimento": comprimento,
            "largura": largura,
            "cor": {"Evacuação Imediata": "#FF0000", "Relocação Temporária": "#FF8C00", "Monitoramento/Abrigo": "#FFD700"}[nivel]
        }
        
    return resultados, altura_efetiva

def gerar_poligono_pluma(lat_origem, lon_origem, comprimento, largura, direcao_vento_graus):
    """
    Gera os pontos Lat/Lon para desenhar a 'Gota' no mapa.
    """
    # Matemática Vetorial: O vento vem de X, a pluma vai para X + 180.
    angulo_pluma = (direcao_vento_graus + 180) % 360
    theta = math.radians(90 - angulo_pluma) # Ajuste para o Norte geográfico

    pontos_base = []
    n_pontos = 30 # Resolução da curva
    
    # Desenhar metade da gota e espelhar
    for i in range(n_pontos + 1):
        t = (i / n_pontos) * math.pi 
        # Equação paramétrica da forma de "Gota/Lágrima"
        dx_local = comprimento * math.sin(t/2)
        dy_local = (largura / 2) * math.sin(t) * (dx_local / comprimento) * 2 
        
        pontos_base.append((dx_local, dy_local))
        pontos_base.insert(0, (dx_local, -dy_local))

    # Converter Metros -> Graus Lat/Lon (Projeção aproximada)
    coords_mapa = []
    r_terra = 6378137 # Raio da Terra
    
    for x, y in pontos_base:
        # Rotacionar os pontos baseado na direção do vento
        x_rot = x * math.cos(theta) - y * math.sin(theta)
        y_rot = x * math.sin(theta) + y * math.cos(theta)
        
        # Transladar para a coordenada de origem
        d_lat = (y_rot / r_terra) * (180 / math.pi)
        d_lon = (x_rot / r_terra) * (180 / math.pi) / math.cos(math.radians(lat_origem))
        
        coords_mapa.append([lat_origem + d_lat, lon_origem + d_lon])
        
    return coords_mapa

# --- 3. INTERFACE VISUAL (FRONT-END) ---
def renderizar():
    st.markdown("### ☢️ Nuclear RDD (Dispersão de 'Bomba Suja')")
    st.markdown("Modelagem de deposição de material particulado radioativo no solo após detonação de explosivo convencional.")
    st.markdown("---")

    # --- GUIA DIDÁTICO EXPANSÍVEL ---
    with st.expander("📖 Clique aqui para entender os conceitos (Guia Rápido)", expanded=True):
        st.markdown("""
        #### O que é um RDD ("Bomba Suja")?
        É um dispositivo terrorista ou acidental onde um explosivo comum (Dinamite, TNT, C4) é detonado junto com uma fonte radioativa.
        * **NÃO** ocorre explosão nuclear (fissão/fusão).
        * **NÃO** se forma o cogumelo atômico clássico.
        * **O PERIGO:** O explosivo pulveriza o metal radioativo, criando uma poeira invisível que o vento carrega e deposita sobre a cidade.
        
        #### Como preencher os dados?
        1. **Atividade da Fonte (Curies - Ci):** É a "potência" da radiação.
           * *Pequena (Industrial):* 10 a 50 Ci.
           * *Média (Gamagrafia):* 50 a 100 Ci.
           * *Grande (Hospitalar/Radioterapia):* 1.000 a 5.000 Ci (**Extremamente Perigoso**).
        2. **Carga Explosiva:** Quanto de bomba foi usado?
           * O explosivo joga a poeira para o alto. Quanto mais alto, mais longe vai, mas mais "espalhada" fica.
        3. **Vento:** * A mancha vermelha vai sempre na direção PARA ONDE o vento sopra.
           * *Exemplo:* Vento vindo do Norte (0°) -> Contaminação vai para o Sul (180°).
        
        #### Legenda do Mapa (Ground Shine)
        * 🔴 **Vermelho (Evacuação):** Nível crítico. Risco de morte ou queimadura se permanecer.
        * 🟠 **Laranja (Relocação):** Nível alto. Moradores devem sair temporariamente.
        * 🟡 **Amarelo (Abrigo/Limpeza):** Nível de alerta. Fique dentro de casa, feche janelas. Requer descontaminação urbana.
        """)

    # Layout de Colunas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Localização e Meteorologia")
        lat = st.number_input("Latitude (Local do Evento)", value=-22.8625, format="%.5f", help="Use o Google Maps (botão direito) para pegar este número.")
        lon = st.number_input("Longitude (Local do Evento)", value=-43.2245, format="%.5f")
        
        st.info("👇 A Meteorologia define o formato da nuvem.")
        vento_vel = st.number_input("Velocidade do Vento (m/s)", min_value=0.1, value=3.0, step=0.5, help="Se < 1 m/s, a nuvem fica parada em cima do local (muito perigoso). Se ventar muito, ela se estica.")
        vento_dir = st.number_input("Direção do Vento (Graus)", min_value=0, max_value=360, value=90, help="Direção DE ONDE vem o vento. 0=Norte, 90=Leste, 180=Sul, 270=Oeste.")

    with col2:
        st.subheader("☢️ Termo Fonte (Ameaça)")
        
        nome_iso = st.selectbox("Isótopo Envolvido", list(ISOTOPOS.keys()), help="Identifique o símbolo radioativo na fonte.")
        dados_iso = ISOTOPOS[nome_iso]
        
        # Mostra detalhes técnicos do isótopo escolhido
        st.caption(f"ℹ️ **Detalhes:** {dados_iso['risco']} ({dados_iso['uso']})")
        
        atividade = st.number_input("Atividade Estimada (Ci)", min_value=1.0, value=100.0, step=10.0, help="Quantidade de Curies. Fontes órfãs geralmente têm entre 10 e 200 Ci.")
        
        explosivo = st.number_input("Massa do Explosivo (kg TNT)", min_value=0.5, value=10.0, step=1.0, help="Estimativa da bomba usada. Mochila-bomba ≈ 5kg. Carro-bomba ≈ 200kg.")

    # Controle de Estado (Para o mapa não sumir)
    if 'rdd_calculado' not in st.session_state:
        st.session_state['rdd_calculado'] = False

    # Botão de Ação
    if st.button("☣️ SIMULAR ZONAS DE CONTAMINAÇÃO", type="primary", use_container_width=True):
        st.session_state['rdd_calculado'] = True

    # Exibição dos Resultados
    if st.session_state['rdd_calculado']:
        
        zonas, altura_nuvem = calcular_pluma_rdd(atividade, explosivo, vento_vel, vento_dir)
        
        st.success(f"SIMULAÇÃO CONCLUÍDA PARA {nome_iso.upper()}")
        st.write(f"A nuvem de detritos atingiu **{altura_nuvem:.1f} metros de altura** antes de se deslocar.")
        
        # Métricas visuais
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Zona Vermelha (Evacuar)", f"{zonas['Evacuação Imediata']['comprimento']:.0f} m", delta="Crítico", delta_color="inverse")
        with m2:
            st.metric("Zona Laranja (Controle)", f"{zonas['Relocação Temporária']['comprimento']:.0f} m", delta="Alto Risco", delta_color="off")
        with m3:
            st.metric("Zona Amarela (Limpeza)", f"{zonas['Monitoramento/Abrigo']['comprimento']:.0f} m", delta="Alerta")

        # --- MAPA FOLIUM ---
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")

        # Marcador do Epicentro
        folium.Marker(
            [lat, lon], 
            tooltip=f"<b>PONTO ZERO</b><br>{explosivo}kg TNT + {atividade}Ci {nome_iso}",
            icon=folium.Icon(color="black", icon="radiation", prefix="fa")
        ).add_to(m)

        # Desenhar Plumas (Ordem inversa: Amarelo -> Laranja -> Vermelho, para o menor ficar em cima)
        ordem = ["Monitoramento/Abrigo", "Relocação Temporária", "Evacuação Imediata"]
        
        for nivel in ordem:
            dados = zonas[nivel]
            poligono = gerar_poligono_pluma(lat, lon, dados['comprimento'], dados['largura'], vento_dir)
            
            folium.Polygon(
                locations=poligono,
                color=dados['cor'],
                fill=True,
                fill_color=dados['cor'],
                fill_opacity=0.5,
                weight=2,
                tooltip=f"<b>Zona: {nivel}</b><br>Extensão: {dados['comprimento']:.0f}m"
            ).add_to(m)

        st_folium(m, width=None, height=600)