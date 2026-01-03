import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math

# =============================================================================
# 1. BANCO DE DADOS: SENSORES TÁTICOS
# =============================================================================
# Sensores comumente utilizados em drones para reconhecimento e mapeamento
# FOV = Field of View (Campo de Visão) em graus
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
    },
    "LIDAR (Light Detection and Ranging)": {
        "fov": 40,
        "uso": "Mapeamento 3D de terreno, detecção de estruturas e medição de alturas. Útil para navegação em áreas complexas."
    },
    "Multiespectral": {
        "fov": 47,
        "uso": "Análise de vegetação, detecção de contaminação do solo e identificação de materiais específicos."
    },
    "Hiperespectral": {
        "fov": 30,
        "uso": "Identificação química detalhada de materiais e contaminação. Análise espectral avançada."
    },
    "Detector de Partículas (PM2.5/PM10)": {
        "fov": 360,
        "uso": "Monitoramento de qualidade do ar e detecção de partículas suspensas. Mapeamento de dispersão de aerossóis."
    },
    "Câmera de Gás Óptica (OGI)": {
        "fov": 20,
        "uso": "Detecção visual de vazamentos de gases invisíveis através de imagens térmicas especializadas."
    },
    "Radar de Abertura Sintética (SAR)": {
        "fov": 60,
        "uso": "Mapeamento através de nuvens e condições climáticas adversas. Detecção de estruturas e mudanças no terreno."
    },
    "Detector de Compostos Orgânicos Voláteis (VOC)": {
        "fov": 360,
        "uso": "Detecção de vapores orgânicos tóxicos e identificação de fontes de contaminação química."
    },
    "Sensor de Metano (CH4)": {
        "fov": 360,
        "uso": "Detecção de vazamentos de metano, monitoramento de infraestrutura de gás e identificação de fontes."
    },
    "Câmera de Visão Noturna (IV/IR)": {
        "fov": 50,
        "uso": "Operações noturnas, detecção de fontes de calor e reconhecimento em condições de baixa luminosidade."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO DE MISSÃO
# =============================================================================
# Baseado em: Fotogrametria Aérea, Planejamento de Missões de Drones
# O padrão de varredura (lawnmower pattern) é o mais eficiente para mapeamento
# Referências: ASPRS Guidelines, FAA Part 107, ISO 21384-1

def calcular_geometria_voo(altura, fov, largura_area, comprimento_area, sobreposicao):
    """
    Calcula os parâmetros geométricos da varredura aérea (padrão lawnmower).
    
    O padrão de varredura consiste em linhas paralelas que cobrem toda a área,
    com sobreposição lateral para garantir cobertura completa e qualidade da imagem.
    
    Parâmetros:
    - altura: Altura de voo em metros
    - fov: Campo de visão do sensor em graus
    - largura_area: Largura da área a ser mapeada em metros (eixo leste-oeste)
    - comprimento_area: Comprimento da área a ser mapeada em metros (eixo norte-sul)
    - sobreposicao: Sobreposição lateral entre faixas (0-1, onde 0.3 = 30%)
    
    Retorna:
    - largura_sensor_solo: Largura da faixa coberta pelo sensor no solo (metros)
    - num_passagens: Número de linhas de voo necessárias
    - distancia_total: Distância total a ser percorrida (metros)
    """
    # Calcular largura da faixa no solo (swath width)
    # Usando trigonometria: largura = 2 × altura × tan(FOV/2)
    largura_sensor_solo = 2 * altura * math.tan(math.radians(fov / 2))
    
    # Distância entre linhas de voo (considerando sobreposição)
    # Sobreposição garante que não há lacunas entre faixas
    distancia_entre_linhas = largura_sensor_solo * (1 - sobreposicao)
    
    # Número de passagens necessárias para cobrir toda a largura
    num_passagens = math.ceil(largura_area / distancia_entre_linhas)
    
    # Distância total percorrida (cada passagem percorre o comprimento da área)
    distancia_total = num_passagens * comprimento_area
    
    return largura_sensor_solo, num_passagens, distancia_total

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Planejamento de Missão de Reconhecimento Aéreo (Drone)")
    st.markdown("**Reconhecimento aéreo autônomo para mapeamento de áreas de risco e planejamento de missões de drone**")
    st.markdown("---")
    
    with st.expander("Fundamentos do Reconhecimento Aéreo com Drones", expanded=True):
        st.markdown("""
        #### Padrão de Varredura (Lawnmower Pattern)
        
        O padrão de varredura é o método mais eficiente para mapear uma área retangular:
        - **Linhas Paralelas:** O drone voa em linhas paralelas cobrindo toda a área
        - **Sobreposição Lateral:** Garante que não há lacunas entre faixas e melhora a qualidade
        - **Cobertura Completa:** Cada ponto da área é coberto pelo sensor
        
        #### Parâmetros Importantes
        
        **Altura de Voo:**
        - **Voo Baixo (10-30m):** Maior resolução, mais detalhe, menor área coberta por passagem
        - **Voo Médio (30-60m):** Balanceamento entre resolução e eficiência
        - **Voo Alto (60-120m):** Maior área coberta, menor resolução, missão mais rápida
        
        **Campo de Visão (FOV):**
        - Determina a largura da faixa coberta no solo
        - Sensores com FOV maior cobrem mais área por passagem
        - Sensores com FOV menor têm maior resolução mas requerem mais passagens
        
        **Sobreposição Lateral:**
        - **30-40%:** Padrão para mapeamento geral
        - **50-60%:** Para fotogrametria e modelos 3D
        - **70-80%:** Para análise detalhada e reconstrução precisa
        
        #### Tipos de Sensores
        
        **Sensores Ópticos:**
        - Câmeras RGB, térmicas, multiespectrais
        - Requerem condições de iluminação adequadas
        - Não funcionam através de nuvens ou neblina
        
        **Sensores Ativos:**
        - LIDAR, Radar (SAR)
        - Funcionam em qualquer condição de iluminação
        - Podem penetrar nuvens (SAR) ou vegetação (LIDAR)
        
        **Sensores Químicos:**
        - Sniffers de gás, detectores de partículas
        - Requerem voo próximo à fonte (baixa altitude)
        - FOV geralmente 360° (cobertura omnidirecional)
        
        #### Limitações e Considerações
        
        - **Autonomia:** Drones têm tempo de voo limitado (geralmente 20-30 minutos)
        - **Regulamentação:** Verificar regulamentos locais (altura máxima, áreas restritas)
        - **Condições Meteorológicas:** Vento, chuva e neblina afetam a operação
        - **Interferência:** Estruturas, linhas de energia e outros obstáculos
        - **Privacidade:** Considerar questões de privacidade em áreas urbanas
        """)

    # --- SEÇÃO 1: LOCALIZAÇÃO ---
    st.subheader("1. Localização do Incidente")
    with st.expander("Configurar Coordenadas do Ponto Inicial", expanded=True):
        col_lat, col_lon = st.columns(2)
        lat_input = col_lat.number_input(
            "Latitude (Graus Decimais)", 
            value=-22.8625, 
            format="%.6f",
            help="Coordenada geográfica norte-sul. Exemplo: -22.8625 (negativo = hemisfério sul)"
        )
        lon_input = col_lon.number_input(
            "Longitude (Graus Decimais)", 
            value=-43.2245, 
            format="%.6f",
            help="Coordenada geográfica leste-oeste. Exemplo: -43.2245 (negativo = hemisfério oeste)"
        )
        st.caption("**Ponto de Referência:** O drone iniciará o padrão de varredura a partir deste ponto "
                  "(canto inferior esquerdo da área de mapeamento). Este ponto também serve como ponto de decolagem e pouso.")

    # --- SEÇÃO 2: PARÂMETROS TÉCNICOS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2. Configuração do Sensor")
        sensor_nome = st.selectbox(
            "Selecione o Sensor Embarcado", 
            list(SENSORES.keys()),
            help="Escolha o sensor que será utilizado na missão. Cada sensor tem características específicas de FOV e aplicação."
        )
        dados_sensor = SENSORES[sensor_nome]
        st.info(f"**Aplicação:** {dados_sensor['uso']}")
        st.caption(f"**Campo de Visão (FOV):** {dados_sensor['fov']}°")
        
        st.markdown("---")
        st.markdown("**Parâmetros de Voo**")
        altura_voo = st.slider(
            "Altura de Voo (metros)", 
            10, 150, 30, 
            step=5,
            help="Altura acima do solo. Voo baixo = maior resolução e detalhe, menor área coberta. "
                 "Voo alto = maior área coberta, menor resolução, missão mais rápida."
        )
        sobreposicao_percent = st.slider(
            "Sobreposição Lateral (%)", 
            10, 80, 30, 
            step=5,
            help="Percentual de sobreposição entre faixas adjacentes. "
                 "30-40% para mapeamento geral, 50-60% para fotogrametria, 70-80% para análise detalhada."
        )
        sobreposicao = sobreposicao_percent / 100

    with col2:
        st.subheader("3. Dimensões da Área de Mapeamento")
        largura_m = st.number_input(
            "Largura da Zona (metros)", 
            value=200, 
            step=50,
            min_value=50,
            help="Extensão no eixo Leste-Oeste (largura da área a ser mapeada)"
        )
        comprimento_m = st.number_input(
            "Comprimento da Zona (metros)", 
            value=300, 
            step=50,
            min_value=50,
            help="Extensão no eixo Norte-Sul (comprimento da área a ser mapeada)"
        )
        
        st.markdown("---")
        st.markdown("**Parâmetros de Performance**")
        velocidade = st.number_input(
            "Velocidade do Drone (m/s)", 
            value=5.0, 
            step=0.5,
            min_value=1.0,
            max_value=15.0,
            help="Velocidade de cruzeiro do drone durante a varredura. "
                 "Típico: 3-8 m/s para mapeamento, até 15 m/s para reconhecimento rápido."
        )
        
        autonomia_bateria = st.number_input(
            "Autonomia da Bateria (minutos)", 
            value=25.0, 
            step=1.0,
            min_value=5.0,
            max_value=60.0,
            help="Tempo de voo disponível com uma bateria. Típico: 20-30 minutos para drones comerciais."
        )

    # --- EXECUÇÃO ---
    if 'drone_calc' not in st.session_state: 
        st.session_state['drone_calc'] = False
    
    st.markdown("---")
    if st.button("GERAR PLANO DE VOO E MAPA", type="primary", use_container_width=True):
        st.session_state['drone_calc'] = True

    if st.session_state['drone_calc']:
        swath, passagens, dist_total = calcular_geometria_voo(
            altura_voo, 
            dados_sensor['fov'], 
            largura_m, 
            comprimento_m, 
            sobreposicao
        )
        tempo_min = (dist_total / velocidade) / 60
        tempo_seg = tempo_min * 60
        
        st.markdown("---")
        st.markdown("### Resumo da Missão")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Largura da Faixa (Swath)", 
            f"{swath:.1f} m", 
            help="Largura da faixa coberta pelo sensor no solo"
        )
        m2.metric(
            "Número de Passagens", 
            f"{passagens}", 
            help="Número de linhas de voo paralelas necessárias"
        )
        m3.metric(
            "Distância Total", 
            f"{dist_total:.0f} m",
            f"{dist_total/1000:.2f} km",
            help="Distância total a ser percorrida pelo drone"
        )
        m4.metric(
            "Tempo de Voo Estimado", 
            f"{tempo_min:.1f} min",
            f"{int(tempo_seg)} seg",
            help="Tempo necessário para completar a missão"
        )
        
        # Análise de viabilidade
        st.markdown("---")
        margem_seguranca = 0.8  # 80% da autonomia para segurança
        autonomia_util = autonomia_bateria * margem_seguranca
        
        if tempo_min > autonomia_util:
            st.error(f"**ALERTA DE AUTONOMIA:** O tempo estimado ({tempo_min:.1f} min) excede a autonomia disponível "
                    f"({autonomia_util:.1f} min com margem de segurança). "
                    f"Planeje troca de bateria ou divida a missão em múltiplos voos.")
        elif tempo_min > autonomia_bateria * 0.9:
            st.warning(f"**ATENÇÃO:** O tempo estimado ({tempo_min:.1f} min) está próximo do limite da autonomia "
                      f"({autonomia_bateria:.1f} min). Considere reduzir a área ou aumentar a velocidade.")
        else:
            st.success(f"**MISSÃO VIÁVEL:** O tempo estimado ({tempo_min:.1f} min) está dentro da autonomia disponível "
                      f"({autonomia_bateria:.1f} min). Há margem de segurança adequada.")
        
        # Métricas adicionais
        st.markdown("---")
        col_met1, col_met2, col_met3 = st.columns(3)
        
        area_cobertura = largura_m * comprimento_m / 10000  # Converter para hectares
        area_por_minuto = area_cobertura / tempo_min if tempo_min > 0 else 0
        
        col_met1.metric(
            "Área Total de Cobertura",
            f"{area_cobertura:.2f} hectares",
            f"{largura_m * comprimento_m:.0f} m²",
            help="Área total a ser mapeada"
        )
        col_met2.metric(
            "Eficiência de Cobertura",
            f"{area_por_minuto:.2f} ha/min",
            help="Área coberta por minuto de voo"
        )
        col_met3.metric(
            "Distância entre Linhas",
            f"{swath * (1 - sobreposicao):.1f} m",
            help="Distância entre linhas de voo adjacentes"
        )

        # --- MAPA INTERATIVO ---
        st.markdown("---")
        st.subheader("Visualização Tática do Padrão de Varredura")
        
        # Criação do Mapa centrado na coordenada inserida
        m = folium.Map(location=[lat_input, lon_input], zoom_start=17, tiles="OpenStreetMap")
        
        # Marcador do Ponto de Decolagem/Pouso
        folium.Marker(
            [lat_input, lon_input], 
            tooltip=f"<b>PONTO DE DECOLAGEM/POUSO</b><br>Lat: {lat_input:.6f}<br>Lon: {lon_input:.6f}",
            popup=f"<b>Home Point</b><br>Coordenadas: {lat_input:.6f}, {lon_input:.6f}<br>Drone decola e pousa aqui",
            icon=folium.Icon(color="blue", icon="home", prefix="fa")
        ).add_to(m)
        
        # Cálculo Geográfico da Área
        # 1 grau de latitude ≈ 111.000 metros (constante)
        dlat = (comprimento_m / 111000)
        # Longitude depende da latitude (cosseno da latitude)
        dlon = (largura_m / (111000 * math.cos(math.radians(lat_input))))
        
        # Coordenadas dos cantos da área
        canto_inferior_esquerdo = [lat_input, lon_input]
        canto_superior_direito = [lat_input + dlat, lon_input + dlon]
        
        # Desenhar o Polígono da Área de Busca
        folium.Rectangle(
            bounds=[canto_inferior_esquerdo, canto_superior_direito],
            color="blue", 
            fill=True, 
            fill_opacity=0.15,
            weight=3,
            tooltip=f"<b>ÁREA DE COBERTURA TOTAL</b><br>Largura: {largura_m} m<br>Comprimento: {comprimento_m} m<br>Área: {area_cobertura:.2f} ha",
            popup=f"<b>Área de Mapeamento</b><br>Dimensões: {largura_m} × {comprimento_m} m<br>Área: {area_cobertura:.2f} hectares<br>Passagens: {passagens}"
        ).add_to(m)

        # Gerar e desenhar as linhas de varredura (Sweep Lines)
        # Padrão alternado de cores para facilitar visualização
        for i in range(passagens):
            # Offset lateral proporcional à largura do sensor e sobreposição
            offset_m = i * (swath * (1 - sobreposicao))
            offset_lon = offset_m / (111000 * math.cos(math.radians(lat_input)))
            
            # Alternar cores para facilitar visualização
            cor = "red" if i % 2 == 0 else "orange"
            
            # Coordenadas da linha de varredura
            ponto_inicio = [lat_input, lon_input + offset_lon]
            ponto_fim = [lat_input + dlat, lon_input + offset_lon]
            
            folium.PolyLine(
                [ponto_inicio, ponto_fim],
                color=cor, 
                weight=3, 
                opacity=0.8,
                tooltip=f"<b>Linha de Varredura {i+1}/{passagens}</b><br>Largura da faixa: {swath:.1f} m",
                popup=f"<b>Passagem {i+1}</b><br>Largura da faixa: {swath:.1f} m<br>Offset: {offset_m:.1f} m"
            ).add_to(m)
            
            # Adicionar marcadores nos pontos de início e fim das linhas (apenas nas extremidades)
            if i == 0 or i == passagens - 1:
                folium.CircleMarker(
                    ponto_inicio,
                    radius=5,
                    color=cor,
                    fill=True,
                    tooltip=f"Início Passagem {i+1}"
                ).add_to(m)
                folium.CircleMarker(
                    ponto_fim,
                    radius=5,
                    color=cor,
                    fill=True,
                    tooltip=f"Fim Passagem {i+1}"
                ).add_to(m)

        # Adicionar legenda
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Legenda</b><br>
        <i class="fa fa-home" style="color:blue"></i> Ponto de Decolagem<br>
        <span style="color:blue">█</span> Área de Cobertura<br>
        <span style="color:red">━</span> Linhas de Varredura (ímpares)<br>
        <span style="color:orange">━</span> Linhas de Varredura (pares)
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        st_folium(m, width=None, height=600)
        st.caption(f"**Localização da Missão:** {lat_input:.6f}°N, {lon_input:.6f}°W | "
                  f"**Área:** {area_cobertura:.2f} hectares | "
                  f"**Passagens:** {passagens} linhas de voo")
        
        # Recomendações
        st.markdown("---")
        st.markdown("### Recomendações Operacionais")
        
        st.markdown("""
        **ANTES DO VOO:**
        1. **Verificar Regulamentação:** Confirmar altura máxima permitida e áreas restritas
        2. **Condições Meteorológicas:** Verificar vento (máx 10-15 m/s), visibilidade e precipitação
        3. **Checklist de Equipamento:** Baterias carregadas, sensor calibrado, GPS funcionando
        4. **Plano de Contingência:** Definir procedimentos para perda de sinal ou emergência
        5. **Comunicação:** Informar autoridades e população sobre a operação
        
        **DURANTE O VOO:**
        1. **Monitoramento Contínuo:** Acompanhar telemetria (altitude, velocidade, bateria)
        2. **Manter Linha de Visão:** Operador deve manter contato visual com o drone
        3. **Ajustes em Tempo Real:** Pausar missão se condições mudarem
        4. **Backup de Dados:** Garantir que dados estão sendo salvos durante o voo
        
        **APÓS O VOO:**
        1. **Download de Dados:** Transferir dados do sensor imediatamente
        2. **Análise Inicial:** Verificar qualidade e cobertura das imagens/dados
        3. **Processamento:** Processar dados conforme necessário (ortomosaico, nuvem de pontos, etc.)
        4. **Relatório:** Documentar condições do voo, anomalias e resultados
        """)
        
        st.markdown("---")
        st.markdown("### Considerações Técnicas")
        st.info("""
        **Limitações do Modelo:**
        - Assume terreno plano (não considera elevações ou relevo)
        - Não considera obstáculos (edifícios, árvores, linhas de energia)
        - Assume condições ideais de voo (sem vento, visibilidade perfeita)
        - Não modela consumo de bateria variável (subida, descida, vento)
        - Assume velocidade constante durante toda a missão
        
        **Interpretação dos Resultados:**
        - Os tempos são estimativas baseadas em condições ideais
        - Adicione 10-20% de margem para condições reais
        - Considere tempo adicional para decolagem, pouso e manobras
        - Altitude real pode variar devido a elevações do terreno
        - Verifique sempre a regulamentação local antes de voar
        
        **Melhorias Futuras:**
        - Consideração de terreno e elevações (DEM - Digital Elevation Model)
        - Modelagem de obstáculos e zonas de exclusão
        - Cálculo de consumo de bateria baseado em perfil de voo
        - Otimização de rota considerando vento e condições meteorológicas
        - Integração com sistemas de planejamento de missão (Mission Planner, QGroundControl)
        """)