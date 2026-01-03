import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS DE ISÓTOPOS (CONHECIMENTO TÉCNICO)
# =============================================================================
# Isótopos radioativos comumente encontrados em fontes órfãs ou dispositivos
# que podem ser utilizados em RDD (Radiological Dispersal Device).
# Baseado em: IAEA Incident and Trafficking Database, NRC Source Registry
ISOTOPOS = {
    "Césio-137 (Cs-137)": {
        "meia_vida": "30 anos", 
        "energia": "Gama/Beta", 
        "gama_const": 3.3,  # mSv/h a 1m por Ci
        "risco": "Contaminação de longo prazo (acidente de Goiânia). Liga-se quimicamente ao solo. Perigo de contaminação interna se inalado ou ingerido.",
        "uso": "Hospitais (Radioterapia antiga), Medidores de Nível Industriais, Densímetros."
    },
    "Cobalto-60 (Co-60)": {
        "meia_vida": "5.2 anos", 
        "energia": "Gama Muito Forte (1.17 e 1.33 MeV)", 
        "gama_const": 13.0,  # mSv/h a 1m por Ci
        "risco": "Irradiação externa aguda. Alta energia gama penetrante. Morte rápida se exposição a alta dose. Difícil de blindar.",
        "uso": "Esterilização de Alimentos, Radioterapia, Irradiadores Industriais."
    },
    "Irídio-192 (Ir-192)": {
        "meia_vida": "73 dias", 
        "energia": "Gama (múltiplas energias)", 
        "gama_const": 4.8,  # mSv/h a 1m por Ci
        "risco": "Queimaduras graves por contato direto. Decai relativamente rápido (meses). Principal causa de acidentes industriais com radiação.",
        "uso": "Gamagrafia Industrial (Raio-X de soldas em tubulações, vasos de pressão)."
    },
    "Amerício-241 (Am-241)": {
        "meia_vida": "432 anos", 
        "energia": "Alfa/Gama Fraco", 
        "gama_const": 0.1,  # mSv/h a 1m por Ci
        "risco": "Perigo extremo se inalado (pó fino). Emite partículas alfa que causam dano severo se incorporado. Gama fraco, mas contaminação interna é letal.",
        "uso": "Perfilagem de Poços de Petróleo, Detectores de Fumaça (antigos), Para-raios (obsoletos)."
    },
    "Estrôncio-90 (Sr-90)": {
        "meia_vida": "28 anos", 
        "energia": "Beta Puro", 
        "gama_const": 0.0,  # Beta puro, sem gama direto
        "risco": "Se ingerido ou inalado, fixa-se nos ossos como cálcio (análogo químico). Causa câncer ósseo e leucemia. Emite beta forte, mas sem gama direto.",
        "uso": "Geradores Termoelétricos Radioisotópicos (RTG) em Faróis Remotos, Satélites, Sondas Espaciais."
    },
    "Tecnécio-99m (Tc-99m)": {
        "meia_vida": "6 horas", 
        "energia": "Gama (140 keV)", 
        "gama_const": 0.2,  # mSv/h a 1m por Ci
        "risco": "Isótopo médico mais comum. Decai muito rápido (horas), mas em grandes quantidades pode causar contaminação. Baixa energia gama.",
        "uso": "Medicina Nuclear (diagnóstico por imagem - cintilografia). Mais de 80% dos procedimentos de medicina nuclear."
    },
    "Iodo-131 (I-131)": {
        "meia_vida": "8 dias", 
        "energia": "Gama/Beta", 
        "gama_const": 2.2,  # mSv/h a 1m por Ci
        "risco": "Muito volátil. Produto de fissão nuclear. Acumula na tireoide humana se inalado ou ingerido. Causa câncer de tireoide. Perigo em acidentes de reator.",
        "uso": "Terapia de Câncer de Tireoide, Medicina Nuclear, Produto de Fissão em Reatores."
    },
    "Rádio-226 (Ra-226)": {
        "meia_vida": "1600 anos", 
        "energia": "Alfa/Gama", 
        "gama_const": 0.8,  # mSv/h a 1m por Ci
        "risco": "Fonte órfã histórica. Muito persistente (milênios). Emite radônio-222 gasoso como produto de decaimento. Perigo de contaminação interna.",
        "uso": "Fontes Órfãs Históricas (relógios luminosos, pinturas radioluminescentes antigas)."
    },
    "Polônio-210 (Po-210)": {
        "meia_vida": "138 dias", 
        "energia": "Alfa Puro", 
        "gama_const": 0.0,  # Alfa puro, sem gama
        "risco": "Extremamente tóxico se ingerido ou inalado. Emite partículas alfa de alta energia. Caso Litvinenko (2006). Muito difícil de detectar (sem gama).",
        "uso": "Fontes de Nêutrons (misturado com Berílio), Pesquisa Científica."
    },
    "Plutônio-239 (Pu-239)": {
        "meia_vida": "24100 anos", 
        "energia": "Alfa/Gama Muito Fraco", 
        "gama_const": 0.0002,  # mSv/h a 1m por Ci
        "risco": "Material físsil. Perigo de contaminação interna e criticidade. Gama muito fraco, mas alfa extremamente perigoso se incorporado. Carcinogênico.",
        "uso": "Combustível de Reatores, Armas Nucleares, Pesquisa."
    },
    "Urânio-238 (U-238)": {
        "meia_vida": "4.46 bilhões de anos", 
        "energia": "Alfa/Gama Muito Fraco", 
        "gama_const": 0.0001,  # mSv/h a 1m por Ci
        "risco": "Urânio natural. Principalmente perigo químico (metal pesado tóxico) e de contaminação interna. Gama muito fraco. Muito persistente.",
        "uso": "Combustível de Reatores, Munição Depleted Uranium (DU), Pesquisa."
    },
    "Tório-232 (Th-232)": {
        "meia_vida": "14 bilhões de anos", 
        "energia": "Alfa/Gama Fraco", 
        "gama_const": 0.0003,  # mSv/h a 1m por Ci
        "risco": "Tório natural. Muito persistente. Perigo de contaminação interna. Gama fraco. Usado em alguns reatores experimentais.",
        "uso": "Combustível de Reatores Experimentais, Eletrodos de Solda TIG, Pesquisa."
    },
    "Carbono-14 (C-14)": {
        "meia_vida": "5730 anos", 
        "energia": "Beta Puro", 
        "gama_const": 0.0,  # Beta puro
        "risco": "Baixo risco externo (beta fraco), mas pode incorporar-se biologicamente. Usado em datação por carbono. Contaminação de longo prazo.",
        "uso": "Datação por Carbono-14, Traçador Radioativo em Pesquisa."
    },
    "Fósforo-32 (P-32)": {
        "meia_vida": "14 dias", 
        "energia": "Beta Forte", 
        "gama_const": 0.0,  # Beta puro
        "risco": "Beta de alta energia. Perigo de queimaduras por contato. Se ingerido, acumula em tecidos com alto metabolismo (osso, medula).",
        "uso": "Medicina Nuclear (terapia), Pesquisa Biológica, Tratamento de Policitemia Vera."
    },
    "Enxofre-35 (S-35)": {
        "meia_vida": "87 dias", 
        "energia": "Beta Fraco", 
        "gama_const": 0.0,  # Beta puro
        "risco": "Beta de baixa energia. Baixo risco externo, mas pode incorporar-se biologicamente. Usado como traçador em pesquisa.",
        "uso": "Pesquisa Biológica (traçador), Estudos Metabólicos."
    }
}

# =============================================================================
# 2. LIMITES DE INTERVENÇÃO (NÍVEIS DE CONTAMINAÇÃO NO SOLO)
# =============================================================================
# Baseados em: IAEA Safety Standards, EPA Protective Action Guides (PAGs),
# NRC Emergency Response Guidelines
# Unidade: Curie por metro quadrado (Ci/m²) - atividade depositada no solo
LIMITES_INTERVENCAO = {
    "Evacuação Imediata": 0.01,    # Zona Quente (Hot Zone) - Vermelho
    "Relocação Temporária": 0.001, # Zona Morna (Warm Zone) - Laranja
    "Monitoramento/Abrigo": 0.0001 # Zona Fria/Alerta (Cold Zone) - Amarelo
}

# =============================================================================
# 3. MOTOR DE CÁLCULO (DISPERSÃO E DEPOSIÇÃO)
# =============================================================================
# Baseado em: Gaussian Puff Model simplificado, Church's Explosion Formula,
# IAEA Technical Reports Series No. 418 (Radiological Consequences)
def calcular_pluma_rdd(atividade_ci, explosivo_kg, vento_ms, direcao_graus, gama_const=3.3):
    """
    Simula a dispersão de particulado radioativo após detonação de RDD.
    
    Parâmetros:
    - atividade_ci: Atividade inicial em Curies (Ci)
    - explosivo_kg: Massa equivalente de TNT em quilogramas
    - vento_ms: Velocidade do vento em metros por segundo
    - direcao_graus: Direção de onde vem o vento (0° = Norte, 90° = Leste)
    - gama_const: Constante gama do isótopo (mSv/h a 1m por Ci)
    
    Retorna:
    - resultados: Dicionário com dimensões das zonas de contaminação
    - altura_efetiva: Altura da nuvem de detritos em metros
    - dados_detalhados: DataFrame com informações detalhadas por zona
    """
    # 1. Altura da Nuvem (Fórmula de Church para explosões químicas)
    # H = 76 * (kg_TNT)^0.25
    # Baseado em: Church, H.E. (1969) - "Explosions and Blast Waves"
    altura_efetiva = 76 * (explosivo_kg ** 0.25)
    
    # 2. Termo Fonte (Release Fraction - Fração Liberada)
    # Em RDD ("Bombas Sujas"), assume-se que 20% do material vira pó fino
    # respirável/dispersível. O resto (80%) são estilhaços grandes que caem
    # na cratera próxima ao ponto zero.
    # Baseado em: DHS/NRC RDD Assessment Guidelines
    RF = 0.20 
    Q_efetivo = atividade_ci * RF
    
    # 3. Velocidade de Deposição (Deposition Velocity)
    # Velocidade típica para aerossóis radioativos: ~1 cm/s
    # Depende do tamanho da partícula, densidade e condições meteorológicas
    v_d = 0.01  # m/s
    
    resultados = {}
    dados_detalhados = []
    
    # Loop: calcula as 3 zonas de intervenção automaticamente
    for nivel, limite in LIMITES_INTERVENCAO.items():
        # Inversão da equação de deposição para encontrar a distância
        # Equação simplificada: C = (Q * v_d) / (u * L)
        # Onde: C = concentração depositada (Ci/m²), Q = fonte (Ci),
        #       v_d = velocidade de deposição (m/s), u = velocidade do vento (m/s),
        #       L = comprimento da pluma (m)
        # Reorganizando: L = (Q * v_d) / (u * C)
        fator_forca = (Q_efetivo * v_d) / (vento_ms * limite)
        
        # Comprimento estimado da mancha no chão (em metros)
        comprimento = math.sqrt(fator_forca) * 50 
        
        # Limites físicos do modelo (validação)
        if comprimento < 20: comprimento = 20  # Mínimo: 20 metros
        if comprimento > 15000: comprimento = 15000  # Máximo: 15 km
        
        # Largura da pluma (Abertura lateral devido à turbulência atmosférica)
        # Razão típica largura/comprimento para plumas gaussianas: ~0.35
        largura = comprimento * 0.35 
        
        # Área contaminada (aproximação elíptica)
        area_contaminada = math.pi * (comprimento / 2) * (largura / 2)
        
        # Taxa de dose estimada no centro da zona (Ground Shine)
        # Aproximação: dose diminui com distância e decaimento temporal
        # Para simplificação, usamos a constante gama ajustada pela atividade depositada
        dose_rate_centro = (gama_const * limite * 1000) / (1.0 ** 2)  # mSv/h (aproximado)
        
        resultados[nivel] = {
            "comprimento": comprimento,
            "largura": largura,
            "area": area_contaminada,
            "dose_rate_centro": dose_rate_centro,
            "cor": {"Evacuação Imediata": "#FF0000", "Relocação Temporária": "#FF8C00", "Monitoramento/Abrigo": "#FFD700"}[nivel]
        }
        
        dados_detalhados.append({
            "Zona": nivel,
            "Comprimento (m)": comprimento,
            "Largura (m)": largura,
            "Área (m²)": area_contaminada,
            "Área (km²)": area_contaminada / 1e6,
            "Contaminação (Ci/m²)": limite,
            "Taxa de Dose (mSv/h)": dose_rate_centro
        })
    
    df_detalhado = pd.DataFrame(dados_detalhados)
    
    return resultados, altura_efetiva, df_detalhado

def gerar_poligono_pluma(lat_origem, lon_origem, comprimento, largura, direcao_vento_graus):
    """
    Gera os pontos geográficos (Lat/Lon) para desenhar a pluma no mapa.
    
    Utiliza geometria vetorial para criar uma forma de "gota" (teardrop) que
    representa a dispersão da nuvem radioativa. A pluma se estende na direção
    oposta ao vento (vento vem de X, pluma vai para X + 180°).
    
    Parâmetros:
    - lat_origem: Latitude do ponto zero (graus decimais)
    - lon_origem: Longitude do ponto zero (graus decimais)
    - comprimento: Comprimento da pluma em metros
    - largura: Largura máxima da pluma em metros
    - direcao_vento_graus: Direção de onde vem o vento (0° = Norte)
    
    Retorna:
    - coords_mapa: Lista de coordenadas [lat, lon] para desenhar o polígono
    """
    # Matemática Vetorial: O vento vem de X, a pluma vai para X + 180°.
    angulo_pluma = (direcao_vento_graus + 180) % 360
    theta = math.radians(90 - angulo_pluma)  # Ajuste para o Norte geográfico

    pontos_base = []
    n_pontos = 30  # Resolução da curva (número de pontos na metade da gota)
    
    # Desenhar metade da gota e espelhar para criar simetria
    for i in range(n_pontos + 1):
        t = (i / n_pontos) * math.pi 
        # Equação paramétrica da forma de "Gota/Lágrima" (teardrop shape)
        dx_local = comprimento * math.sin(t/2)
        dy_local = (largura / 2) * math.sin(t) * (dx_local / comprimento) * 2 
        
        pontos_base.append((dx_local, dy_local))
        pontos_base.insert(0, (dx_local, -dy_local))  # Espelhar para criar simetria

    # Converter Metros -> Graus Lat/Lon (Projeção aproximada)
    # Usa aproximação de esfera para pequenas distâncias (< 100 km)
    coords_mapa = []
    r_terra = 6378137  # Raio da Terra em metros (WGS84)
    
    for x, y in pontos_base:
        # Rotacionar os pontos baseado na direção do vento
        x_rot = x * math.cos(theta) - y * math.sin(theta)
        y_rot = x * math.sin(theta) + y * math.cos(theta)
        
        # Transladar para a coordenada de origem
        # Conversão: 1 grau de latitude ≈ 111 km, longitude varia com latitude
        d_lat = (y_rot / r_terra) * (180 / math.pi)
        d_lon = (x_rot / r_terra) * (180 / math.pi) / math.cos(math.radians(lat_origem))
        
        coords_mapa.append([lat_origem + d_lat, lon_origem + d_lon])
        
    return coords_mapa

# =============================================================================
# 4. INTERFACE VISUAL (FRONT-END)
# =============================================================================
def renderizar():
    st.title("RDD - Dispersão de Material Radioativo")
    st.markdown("**Modelagem de deposição de material particulado radioativo no solo após detonação de explosivo convencional (Radiological Dispersal Device)**")
    st.markdown("---")

    # --- GUIA DIDÁTICO EXPANSÍVEL ---
    with st.expander("Fundamentos Teóricos e Conceitos Operacionais", expanded=True):
        st.markdown("""
        #### O que é um RDD (Radiological Dispersal Device)?
        
        Um RDD, também conhecido como "Bomba Suja" (Dirty Bomb), é um dispositivo onde um explosivo convencional (TNT, C4, dinamite) é detonado junto com material radioativo. É importante compreender que:
        
        * **NÃO ocorre explosão nuclear:** Não há fissão ou fusão nuclear. A energia vem apenas do explosivo químico.
        * **NÃO se forma o cogumelo atômico clássico:** A nuvem é similar a uma explosão química convencional.
        * **O PERIGO PRINCIPAL:** O explosivo pulveriza o material radioativo, criando uma poeira fina (aerossol) que o vento carrega e deposita sobre a área circundante. A contaminação radioativa se espalha, criando zonas de risco que podem persistir por anos ou décadas.
        
        #### Mecanismo de Dispersão
        
        1. **Detonação:** O explosivo fragmenta a fonte radioativa em partículas finas.
        2. **Formação da Nuvem:** As partículas são lançadas na atmosfera, formando uma nuvem de detritos.
        3. **Transporte Atmosférico:** O vento carrega a nuvem na direção de seu fluxo.
        4. **Deposição:** As partículas se depositam no solo por gravidade e turbulência, criando uma "mancha" de contaminação.
        5. **Ground Shine:** O material depositado emite radiação continuamente, criando zonas de exposição externa.
        
        #### Parâmetros de Entrada
        
        **1. Atividade da Fonte (Curies - Ci):**
        A atividade radioativa mede a "potência" da fonte. Valores típicos:
        * **Pequena (Industrial):** 10 a 50 Ci - Fontes de gamagrafia, medidores de nível
        * **Média (Gamagrafia/Medicina):** 50 a 200 Ci - Fontes de Irídio-192, Césio-137 hospitalar
        * **Grande (Radioterapia/Irradiadores):** 1.000 a 10.000 Ci - Cobalto-60, fontes de esterilização (**Extremamente Perigoso**)
        
        **2. Carga Explosiva (kg TNT equivalente):**
        A massa do explosivo determina a altura da nuvem e a eficiência de pulverização:
        * **Pequena:** 1-5 kg - Mochila-bomba, dispositivo portátil
        * **Média:** 10-50 kg - Veículo pequeno, dispositivo médio
        * **Grande:** 100-500 kg - Carro-bomba, dispositivo grande
        
        Quanto maior a carga, maior a altura da nuvem e maior a área potencialmente afetada.
        
        **3. Condições Meteorológicas:**
        * **Velocidade do Vento:** Determina a velocidade de transporte da nuvem. Ventos muito fracos (< 1 m/s) podem fazer a nuvem ficar estacionária sobre o local (muito perigoso). Ventos fortes (> 10 m/s) esticam a pluma mas reduzem a concentração.
        * **Direção do Vento:** A pluma se desloca na direção **oposta** à direção de onde vem o vento. Exemplo: Vento vindo do Norte (0°) -> Contaminação vai para o Sul (180°).
        
        #### Zonas de Intervenção (Limites de Contaminação)
        
        Baseados em padrões internacionais (IAEA, EPA, NRC), as zonas são definidas pela atividade depositada no solo:
        
        * **Zona Vermelha (Evacuação Imediata):** ≥ 0.01 Ci/m² - Nível crítico. Risco de morte ou queimaduras graves por exposição prolongada. Evacuação imediata obrigatória.
        * **Zona Laranja (Relocação Temporária):** 0.001 a 0.01 Ci/m² - Nível alto. Moradores devem ser relocados temporariamente até descontaminação.
        * **Zona Amarela (Monitoramento/Abrigo):** 0.0001 a 0.001 Ci/m² - Nível de alerta. Abrigo no local (fechar janelas, evitar áreas externas). Requer monitoramento e descontaminação urbana.
        
        #### Limitações do Modelo
        
        Este modelo utiliza simplificações para fins didáticos e operacionais:
        * Assume condições meteorológicas estáveis (sem mudanças de vento)
        * Não considera topografia complexa (montanhas, vales)
        * Usa fração de liberação fixa (20%) - na realidade varia com tipo de explosivo e material
        * Não modela decaimento radioativo temporal (assume atividade constante)
        * Não considera chuvas ou outras condições atmosféricas que afetam deposição
        
        Para análises detalhadas, utilize modelos atmosféricos avançados (CALPUFF, AERMOD, HYSPLIT).
        """)

    # Layout de Colunas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Localização e Meteorologia")
        st.markdown("**Coordenadas Geográficas do Ponto Zero**")
        lat = st.number_input("Latitude (graus decimais)", value=-22.8625, format="%.5f", 
                             help="Coordenada geográfica do local da detonação. Use o Google Maps (botão direito > 'O que há aqui?') para obter coordenadas precisas.")
        lon = st.number_input("Longitude (graus decimais)", value=-43.2245, format="%.5f",
                             help="Coordenada geográfica do local da detonação.")
        
        st.markdown("---")
        st.markdown("**Condições Meteorológicas**")
        st.caption("As condições meteorológicas determinam o formato, direção e extensão da pluma de contaminação.")
        vento_vel = st.number_input("Velocidade do Vento (m/s)", min_value=0.1, value=3.0, step=0.5, 
                                   help="Velocidade do vento em metros por segundo. Valores típicos: Calmaria (< 1 m/s), Leve (1-3 m/s), Moderado (3-7 m/s), Forte (> 7 m/s). Ventos muito fracos podem fazer a nuvem ficar estacionária (muito perigoso).")
        vento_dir = st.number_input("Direção do Vento (graus)", min_value=0, max_value=360, value=90, 
                                   help="Direção DE ONDE vem o vento (direção de origem). 0° = Norte, 90° = Leste, 180° = Sul, 270° = Oeste. A pluma se desloca na direção oposta.")

    with col2:
        st.subheader("Termo Fonte (Características da Ameaça)")
        
        nome_iso = st.selectbox("Isótopo Radioativo Envolvido", list(ISOTOPOS.keys()), 
                               help="Selecione o isótopo radioativo identificado na fonte. Consulte a marcação da fonte ou utilize detectores de radiação para identificação.")
        dados_iso = ISOTOPOS[nome_iso]
        
        # Mostra detalhes técnicos do isótopo escolhido
        st.info(f"**Meia-vida:** {dados_iso['meia_vida']} | **Energia:** {dados_iso['energia']} | **Constante Gama:** {dados_iso.get('gama_const', 0.0):.2f} mSv/h·m²/Ci")
        st.caption(f"**Risco Principal:** {dados_iso['risco']}")
        st.caption(f"**Uso Típico:** {dados_iso['uso']}")
        
        st.markdown("---")
        atividade = st.number_input("Atividade Estimada (Curies - Ci)", min_value=1.0, value=100.0, step=10.0, 
                                   help="Atividade radioativa total da fonte em Curies. Fontes órfãs geralmente têm entre 10 e 200 Ci. Fontes de radioterapia podem ter milhares de Curies.")
        
        explosivo = st.number_input("Massa do Explosivo (kg TNT equivalente)", min_value=0.5, value=10.0, step=1.0, 
                                   help="Massa do explosivo em quilogramas de TNT equivalente. Mochila-bomba típica: 5-10 kg. Carro-bomba: 50-500 kg. Quanto maior, maior a altura da nuvem e área afetada.")

    # Controle de Estado (Para o mapa não sumir)
    if 'rdd_calculado' not in st.session_state:
        st.session_state['rdd_calculado'] = False

    st.markdown("---")
    
    # Botão de Ação
    if st.button("SIMULAR ZONAS DE CONTAMINAÇÃO", type="primary", use_container_width=True):
        st.session_state['rdd_calculado'] = True

    # Exibição dos Resultados
    if st.session_state['rdd_calculado']:
        
        gama_const = dados_iso.get('gama_const', 3.3)  # Usa constante gama do isótopo
        zonas, altura_nuvem, df_detalhado = calcular_pluma_rdd(atividade, explosivo, vento_vel, vento_dir, gama_const)
        
        st.success(f"**SIMULAÇÃO CONCLUÍDA PARA {nome_iso.upper()}**")
        
        # Métricas principais
        st.markdown("### Resultados da Simulação")
        
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
            st.metric("Altura da Nuvem", f"{altura_nuvem:.1f} m", 
                     help="Altura efetiva da nuvem de detritos após a detonação")
        with col_met2:
            st.metric("Zona Vermelha", f"{zonas['Evacuação Imediata']['comprimento']:.0f} m", 
                     delta="Crítico", delta_color="inverse",
                     help="Zona de evacuação imediata - risco de morte por exposição")
        with col_met3:
            st.metric("Zona Laranja", f"{zonas['Relocação Temporária']['comprimento']:.0f} m", 
                     delta="Alto Risco", delta_color="off",
                     help="Zona de relocação temporária - requer descontaminação")
        with col_met4:
            st.metric("Zona Amarela", f"{zonas['Monitoramento/Abrigo']['comprimento']:.0f} m", 
                     delta="Alerta",
                     help="Zona de monitoramento - abrigo no local recomendado")
        
        # Tabela detalhada
        st.markdown("### Detalhamento das Zonas de Contaminação")
        st.dataframe(df_detalhado, use_container_width=True, hide_index=True)
        
        # Informações adicionais
        st.markdown("---")
        st.markdown("### Informações Técnicas")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"""
            **Atividade Total:** {atividade:.1f} Ci  
            **Atividade Efetiva (20% liberada):** {atividade * 0.20:.1f} Ci  
            **Carga Explosiva:** {explosivo:.1f} kg TNT  
            **Velocidade do Vento:** {vento_vel:.1f} m/s  
            **Direção do Vento:** {vento_dir}° (origem)
            """)
        with col_info2:
            st.markdown(f"""
            **Constante Gama:** {gama_const:.2f} mSv/h·m²/Ci  
            **Meia-vida:** {dados_iso['meia_vida']}  
            **Tipo de Radiação:** {dados_iso['energia']}  
            **Área Total Contaminada (Zona Amarela):** {zonas['Monitoramento/Abrigo']['area']/1e6:.2f} km²
            """)

        # --- MAPA FOLIUM ---
        st.markdown("---")
        st.markdown("### Mapa de Dispersão e Zonas de Contaminação")
        
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")

        # Marcador do Epicentro (Ponto Zero)
        folium.Marker(
            [lat, lon], 
            tooltip=f"<b>PONTO ZERO (Epicentro)</b><br>Explosivo: {explosivo:.1f} kg TNT<br>Atividade: {atividade:.1f} Ci {nome_iso}<br>Altura da Nuvem: {altura_nuvem:.1f} m",
            popup=f"<b>Local da Detonação</b><br>Isótopo: {nome_iso}<br>Atividade: {atividade:.1f} Ci<br>Explosivo: {explosivo:.1f} kg TNT",
            icon=folium.Icon(color="black", icon="radiation", prefix="fa")
        ).add_to(m)

        # Desenhar Plumas (Ordem inversa: Amarelo -> Laranja -> Vermelho, para o menor ficar em cima)
        ordem = ["Monitoramento/Abrigo", "Relocação Temporária", "Evacuação Imediata"]
        nomes_legenda = {
            "Evacuação Imediata": "Zona Vermelha - Evacuação Imediata",
            "Relocação Temporária": "Zona Laranja - Relocação Temporária",
            "Monitoramento/Abrigo": "Zona Amarela - Monitoramento/Abrigo"
        }
        
        for nivel in ordem:
            dados = zonas[nivel]
            poligono = gerar_poligono_pluma(lat, lon, dados['comprimento'], dados['largura'], vento_dir)
            
            folium.Polygon(
                locations=poligono,
                color=dados['cor'],
                fill=True,
                fill_color=dados['cor'],
                fill_opacity=0.4,
                weight=3,
                tooltip=f"<b>{nomes_legenda[nivel]}</b><br>Comprimento: {dados['comprimento']:.0f} m<br>Largura: {dados['largura']:.0f} m<br>Área: {dados['area']/1e6:.2f} km²<br>Contaminação: {LIMITES_INTERVENCAO[nivel]:.4f} Ci/m²",
                popup=f"<b>{nomes_legenda[nivel]}</b><br>Comprimento: {dados['comprimento']:.0f} m<br>Largura: {dados['largura']:.0f} m<br>Área: {dados['area']/1e6:.2f} km²<br>Contaminação: {LIMITES_INTERVENCAO[nivel]:.4f} Ci/m²<br>Taxa de Dose (centro): {dados['dose_rate_centro']:.2f} mSv/h"
            ).add_to(m)

        # Adicionar legenda
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <b>Legenda das Zonas</b><br>
        <span style="color: #FF0000;">●</span> Vermelho: Evacuação Imediata<br>
        <span style="color: #FF8C00;">●</span> Laranja: Relocação Temporária<br>
        <span style="color: #FFD700;">●</span> Amarelo: Monitoramento/Abrigo
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        st_folium(m, width=None, height=600)
        
        # Recomendações Operacionais
        st.markdown("---")
        st.markdown("### Recomendações Operacionais")
        
        st.warning("""
        **AÇÕES IMEDIATAS:**
        1. Estabelecer perímetro de segurança baseado na Zona Vermelha
        2. Evacuar imediatamente todas as pessoas dentro da Zona Vermelha
        3. Estabelecer pontos de controle de acesso (checkpoints) nas bordas das zonas
        4. Implementar abrigo no local para pessoas na Zona Amarela (fechar janelas, desligar sistemas de ventilação)
        5. Ativar equipes de descontaminação e monitoramento radiológico
        6. Coordenar com autoridades de saúde pública para relocação temporária da Zona Laranja
        """)
        
        st.info("""
        **CONSIDERAÇÕES TÉCNICAS:**
        - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
        - A contaminação pode persistir por décadas dependendo da meia-vida do isótopo.
        - Chuvas podem redistribuir a contaminação e criar pontos de concentração.
        - A descontaminação urbana é complexa e pode levar meses ou anos.
        - Consulte especialistas em proteção radiológica para análises detalhadas.
        """)