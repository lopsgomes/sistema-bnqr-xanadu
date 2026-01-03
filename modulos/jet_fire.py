import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS: GASES PRESSURIZADOS
# =============================================================================
# Propriedades:
# Hc: Calor de Combustão (kJ/kg)
# MW: Peso Molecular (g/mol)
# Cp/Cv (Gamma): Razão de calores específicos (aprox 1.3-1.4)
# T_comb: Temperatura aproximada da chama (K)
SUBSTANCIAS_JET = {
    "Acetileno": {
        "Hc": 48200, "mw": 26.04, "gamma": 1.26,
        "desc": "Solda industrial. Chama extremamente quente e instável. Risco de detonação e recuo de chama."
    },
    "Amônia (Gás)": {
        "Hc": 18600, "mw": 17.03, "gamma": 1.31,
        "desc": "Refrigeração industrial. Difícil de acender, mas forma Jet Fire se houver calor externo. Gera NOx."
    },
    "Butadieno (1,3)": {
        "Hc": 45500, "mw": 54.09, "gamma": 1.12,
        "desc": "Matéria-prima de borracha. Queima fuliginosa. Polimeriza violentamente se aquecido."
    },
    "Butano (GLP Doméstico)": {
        "Hc": 45750, "mw": 58.12, "gamma": 1.09,
        "desc": "Botijão de cozinha (P13). Chama amarela intensa e radiante."
    },
    "Cloreto de Metila": {
        "Hc": 13200, "mw": 50.49, "gamma": 1.20,
        "desc": "Refrigerante antigo. Queima difícil, mas sob pressão gera chama tóxica (HCl)."
    },
    "Cloreto de Vinila": {
        "Hc": 19000, "mw": 62.50, "gamma": 1.18,
        "desc": "Monômero de PVC. Jato de fogo tóxico (gera Fosgênio e HCl). Carcinogênico."
    },
    "Dimetil Éter (DME)": {
        "Hc": 28900, "mw": 46.07, "gamma": 1.11,
        "desc": "Combustível alternativo. Chama azulada similar ao Gás Natural, mas mais densa."
    },
    "Etano": {
        "Hc": 47500, "mw": 30.07, "gamma": 1.19,
        "desc": "Comum em processamento de gás natural. Queima muito limpa e quente."
    },
    "Etileno": {
        "Hc": 47100, "mw": 28.05, "gamma": 1.24,
        "desc": "Polo petroquímico. Queima rápida, muito reativa e luminosa."
    },
    "Formaldeído (Gás)": {
        "Hc": 19000, "mw": 30.03, "gamma": 1.23,
        "desc": "Industrial. Gás inflamável e tóxico. Chama azulada pouco visível."
    },
    "Gás Natural (Metano)": {
        "Hc": 50000, "mw": 16.04, "gamma": 1.31,
        "desc": "Tubulações de rua (GNV/Gás Encanado). Chama azulada/amarela, muito leve, tende a subir."
    },
    "Hidrogênio": {
        "Hc": 120000, "mw": 2.01, "gamma": 1.41,
        "desc": "Indústria química e baterias. PERIGO INVISÍVEL: Chama transparente de dia e emite UV intenso."
    },
    "Isobutano": {
        "Hc": 45600, "mw": 58.12, "gamma": 1.09,
        "desc": "Refrigerante R600a (Geladeiras). Pressão de vapor alta, inflamação fácil."
    },
    "Monóxido de Carbono": {
        "Hc": 10100, "mw": 28.01, "gamma": 1.40,
        "desc": "Siderurgia. Gás tóxico e inflamável. Chama azulada."
    },
    "Óxido de Etileno": {
        "Hc": 29000, "mw": 44.05, "gamma": 1.21,
        "desc": "Esterilizante. Chama violenta, pode decompor explosivamente dentro do tubo."
    },
    "Propano (GLP Industrial)": {
        "Hc": 46350, "mw": 44.10, "gamma": 1.13,
        "desc": "Tanques industriais e P45. Chama luminosa, gera fuligem. Mais pesado que o ar."
    },
    "Propileno": {
        "Hc": 45800, "mw": 42.08, "gamma": 1.15,
        "desc": "Plásticos. Similar ao propano, mas queima com temperatura ligeiramente maior."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "Hc": 15200, "mw": 34.08, "gamma": 1.32,
        "desc": "Gás ácido/sour. Jet fire emite nuvem letal de SO2. Chama azulada."
    },
    "Metilamina": {
        "Hc": 31000, "mw": 31.06, "gamma": 1.28,
        "desc": "Amina volátil. Usada em síntese química. Queima com chama amarela, gera NOx tóxico."
    },
    "Dimetilamina": {
        "Hc": 35000, "mw": 45.08, "gamma": 1.22,
        "desc": "Amina secundária. Inflamável e tóxica. Chama amarela, gera produtos de combustão tóxicos."
    },
    "Trimetilamina": {
        "Hc": 38000, "mw": 59.11, "gamma": 1.18,
        "desc": "Amina terciária. Odor característico de peixe. Queima com chama amarela."
    },
    "Metil Mercaptano": {
        "Hc": 28000, "mw": 48.11, "gamma": 1.25,
        "desc": "Tiol volátil. Odor extremamente forte. Queima formando SO2. Usado como odorizante de gás."
    },
    "Etil Mercaptano": {
        "Hc": 32000, "mw": 62.13, "gamma": 1.20,
        "desc": "Tiol de cadeia maior. Odor forte. Queima formando SO2. Usado como odorizante."
    },
    "Acroleína": {
        "Hc": 25000, "mw": 56.06, "gamma": 1.26,
        "desc": "Aldeído insaturado. Extremamente tóxico e irritante. Queima com chama amarela. Carcinogênico."
    },
    "Acetonitrila": {
        "Hc": 31000, "mw": 41.05, "gamma": 1.30,
        "desc": "Nitrila volátil. Solvente polar. Queima formando HCN e NOx. Extremamente tóxico."
    },
    "Metanoato de Metila (Formiato)": {
        "Hc": 18000, "mw": 60.05, "gamma": 1.15,
        "desc": "Éster volátil. Solvente industrial. Queima com chama azulada. Tóxico por inalação."
    },
    "Pentano": {
        "Hc": 45000, "mw": 72.15, "gamma": 1.08,
        "desc": "Hidrocarboneto alifático. Componente de gasolina. Vapor pesado, queima com chama amarela."
    },
    "Hexano (Vapor)": {
        "Hc": 44700, "mw": 86.18, "gamma": 1.06,
        "desc": "Hidrocarboneto alifático. Solvente comum. Vapor muito pesado, acumula próximo ao solo."
    },
    "Ciclopropano": {
        "Hc": 46000, "mw": 42.08, "gamma": 1.30,
        "desc": "Hidrocarboneto cíclico. Anestésico antigo. Extremamente reativo devido à tensão do anel."
    },
    "Metil Isocianato": {
        "Hc": 22000, "mw": 57.05, "gamma": 1.35,
        "desc": "Isocianato volátil. Extremamente tóxico (Bhopal). Pode queimar formando CO e HCN. Muito reativo."
    },
    "Dióxido de Carbono (CO2)": {
        "Hc": 0, "mw": 44.01, "gamma": 1.30,
        "desc": "Gás inerte. Não inflamável, mas pode ser liberado em jato pressurizado causando asfixia e congelamento."
    },
    "Argon": {
        "Hc": 0, "mw": 39.95, "gamma": 1.67,
        "desc": "Gás nobre inerte. Não inflamável. Jato pressurizado pode causar asfixia e lesões por frio extremo."
    },
    "Nitrogênio (N2)": {
        "Hc": 0, "mw": 28.01, "gamma": 1.40,
        "desc": "Gás inerte. Não inflamável. Jato pressurizado pode causar asfixia por deslocamento de oxigênio."
    }
}

# Limites de Radiação Térmica (kW/m²) - API 521 / CCPS Guidelines
LIMITES_TERM_JET = {
    "Dano Estrutural / Morte (12.5 kW/m²)": {
        "fluxo": 12.5,
        "cor": "#e74c3c",
        "desc": "Morte rápida por exposição prolongada. Plásticos derretem, madeira inflama espontaneamente. "
               "Falha de estruturas metálicas sem proteção térmica após tempo de exposição."
    },
    "Combate a Incêndio (5.0 kW/m²)": {
        "fluxo": 5.0,
        "cor": "#f39c12",
        "desc": "Limite máximo para operação de bombeiros com equipamento de proteção térmica (Bunker Gear). "
               "Tempo de exposição limitado. Queimaduras de segundo grau em exposição prolongada."
    },
    "Evacuação Segura (1.5 kW/m²)": {
        "fluxo": 1.5,
        "cor": "#f1c40f",
        "desc": "Limite para evacuação segura do público geral. Desconforto térmico significativo, "
               "mas possível evacuação sem lesões graves em tempo limitado."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (MODELO DE PONTO DA API 521)
# =============================================================================
def calcular_vazao_sonica(diametro_mm, pressao_bar, temperatura_c, gas_props):
    """
    Estima a vazão mássica (kg/s) de um gás vazando por um orifício.
    Assume escoamento sônico (Choked Flow), que é o caso em vazamentos de alta pressão.
    
    Parâmetros:
        diametro_mm: Diâmetro do orifício de vazamento (mm)
        pressao_bar: Pressão interna do gás (bar)
        temperatura_c: Temperatura do gás (°C)
        gas_props: Dicionário com propriedades do gás (mw, gamma)
    
    Retorna:
        Vazão mássica em kg/s
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
    Calcula comprimento da chama e zonas de radiação térmica.
    Utiliza correlação simplificada baseada em API 521 e modelos de ponto fonte.
    
    Parâmetros:
        vazao_kg_s: Vazão mássica do gás (kg/s)
        gas_props: Dicionário com propriedades do gás (Hc, mw)
    
    Retorna:
        Tupla: (comprimento_chama_m, potencia_kw, raios_zonas)
        - comprimento_chama_m: Comprimento da chama em metros
        - potencia_kw: Potência térmica total em kW
        - raios_zonas: Dicionário com raios de cada zona de radiação
    """
    Hc = gas_props['Hc']
    
    # 1. Taxa de Liberação de Calor (Q em kW)
    # Energia liberada = vazão mássica × calor de combustão
    Q_kw = vazao_kg_s * Hc
    
    # 2. Comprimento da Chama (L em metros)
    # Correlação empírica baseada em API 521 e estudos de Chamberlain (1987)
    # Para hidrocarbonetos e gases combustíveis, o comprimento é proporcional à vazão elevada a uma potência
    # Ajuste empírico para visualização consistente: L ≈ 15 × (m_dot)^0.45
    if vazao_kg_s > 0:
        comprimento_chama = 15.0 * (vazao_kg_s ** 0.45)
    else:
        comprimento_chama = 0 
    
    # 3. Zonas de Radiação (Point Source Model)
    # Assume que todo calor irradia do centro da chama (modelo simplificado)
    # Fração de radiação (F): varia com o tipo de gás
    # - Hidrogênio: ~0.15 (chama transparente, menos radiação)
    # - Hidrocarbonetos: 0.25-0.30 (chama luminosa, mais radiação)
    F = 0.25  # Valor padrão para hidrocarbonetos
    if gas_props['mw'] < 4:
        F = 0.15  # Hidrogênio irradia menos calor (chama transparente)
    elif gas_props['Hc'] == 0:
        # Gases inertes não produzem radiação térmica
        F = 0.0
    
    # Transmissividade atmosférica (tau): fração de radiação que atravessa a atmosfera
    # Valor médio de 0.7 assume condições atmosféricas normais (umidade, partículas)
    tau = 0.7
    
    # Potência térmica radiada efetiva
    Q_radiado = Q_kw * F * tau
    
    # Calcular raios para cada zona de radiação
    # Modelo de ponto fonte: I = Q_rad / (4 × π × r²)
    # Rearranjando: r = √(Q_rad / (4 × π × I))
    raios = {}
    for nome, dados in LIMITES_TERM_JET.items():
        fluxo_limite = dados['fluxo']
        if fluxo_limite > 0 and Q_radiado > 0:
            r = math.sqrt(Q_radiado / (4 * math.pi * fluxo_limite))
            raios[nome] = r
        else:
            raios[nome] = 0
    
    # Se o gás não é inflamável (Hc = 0), não há chama
    if gas_props['Hc'] == 0:
        comprimento_chama = 0
        Q_kw = 0
        raios = {nome: 0 for nome in LIMITES_TERM_JET.keys()}
            
    return comprimento_chama, Q_kw, raios

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Dardo de Fogo")
    st.markdown("**Modelagem de Jet Fire: Análise de Vazamentos de Gás Pressurizado com Ignição**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de Jet Fire", expanded=True):
        st.markdown("""
        **O que é um Jet Fire?**
        
        Um Jet Fire (incêndio em jato) ocorre quando um gás pressurizado vaza através de um orifício e é imediatamente 
        inflamado, formando uma chama direcionada similar a um maçarico industrial de grande escala.
        
        **Características Físicas:**
        
        1. **Vazamento Sônico:** Em vazamentos de alta pressão, o gás atinge velocidade sônica no orifício, 
           limitando a vazão máxima independente da pressão a jusante (choked flow).
        
        2. **Chama Direcionada:** A chama segue a direção do jato de gás, mas a radiação térmica se propaga 
           radialmente em todas as direções a partir do centro da chama.
        
        3. **Radiação Térmica:** O principal mecanismo de transferência de calor é a radiação, não a convecção. 
           Isso permite que o calor atinja alvos a distâncias significativas.
        
        4. **Efeitos Secundários:** O calor intenso pode enfraquecer estruturas metálicas próximas, causando falhas 
           estruturais e potencialmente desencadeando eventos secundários como BLEVE (Boiling Liquid Expanding Vapor Explosion).
        
        **Metodologia de Cálculo:**
        
        Este módulo utiliza:
        - **Modelo de Vazão Sônica:** Calcula a vazão mássica através de um orifício usando equações de escoamento 
          compressível (choked flow).
        - **Correlação de Comprimento de Chama:** Estima o comprimento da chama baseado na vazão mássica e propriedades 
          do gás (API 521, Chamberlain 1987).
        - **Modelo de Ponto Fonte:** Calcula a radiação térmica assumindo que toda a energia radiante emana do centro 
          da chama, com atenuação atmosférica.
        
        **Limitações do Modelo:**
        
        Este modelo assume condições ideais e não considera:
        - Efeitos de vento na direção e forma da chama
        - Obstruções que podem redirecionar o jato
        - Variações na fração de radiação com a distância
        - Efeitos de múltiplas chamas ou interações complexas
        
        **Aviso Importante:** Para gases não inflamáveis (como nitrogênio, argônio, CO2), o modelo indica ausência de 
        chama, mas o jato pressurizado ainda pode causar lesões por impacto, asfixia ou congelamento.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros do Gás")
        
        subs_nome = st.selectbox("Substância", list(SUBSTANCIAS_JET.keys()))
        dados_gas = SUBSTANCIAS_JET[subs_nome]
        
        st.info(f"**{subs_nome}**\n\n**Descrição:** {dados_gas['desc']}\n\n"
               f"**Calor de Combustão:** {dados_gas['Hc']} kJ/kg\n"
               f"**Peso Molecular:** {dados_gas['mw']} g/mol\n"
               f"**Razão Cp/Cv (γ):** {dados_gas['gamma']:.2f}")
        
        if dados_gas['Hc'] == 0:
            st.warning("**Atenção:** Esta substância não é inflamável. O jato pressurizado ainda pode causar "
                      "lesões por impacto, asfixia ou congelamento, mas não produzirá chama.")

    with col2:
        st.subheader("Parâmetros do Vazamento")
        
        c2a, c2b = st.columns(2)
        pressao = c2a.number_input("Pressão Interna (bar)", value=10.0, min_value=0.1, step=1.0, 
                                   help="Pressão interna da tubulação ou tanque.")
        diametro = c2b.number_input("Diâmetro do Orifício (mm)", value=20.0, min_value=0.1, step=1.0, 
                                    help="Tamanho do orifício de vazamento ou válvula quebrada.")
        
        temp = st.slider("Temperatura do Gás (°C)", -50, 200, 25, 
                        help="Temperatura do gás no momento do vazamento.")
        
        st.subheader("Georreferenciamento")
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f")

    # Botão de cálculo
    if 'jet_calc' not in st.session_state:
        st.session_state['jet_calc'] = False
    
    if st.button("Calcular Jet Fire", type="primary", use_container_width=True):
        st.session_state['jet_calc'] = True

    if st.session_state['jet_calc']:
        # 1. Calcular Vazão
        vazao = calcular_vazao_sonica(diametro, pressao, temp, dados_gas)
        
        # 2. Calcular Jet Fire
        comp_chama, potencia, raios = calcular_jet_fire(vazao, dados_gas)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        k1, k2, k3 = st.columns(3)
        k1.metric("Vazão de Gás", f"{vazao*3600:.1f} kg/h", f"{vazao:.3f} kg/s")
        if dados_gas['Hc'] > 0:
            k2.metric("Comprimento da Chama", f"{comp_chama:.1f} m", "Comprimento do jato de fogo", delta_color="inverse")
            k3.metric("Potência Térmica", f"{potencia/1000:.2f} MW", f"{potencia:.0f} kW")
        else:
            k2.metric("Tipo de Jato", "Gás Inerte", "Sem chama")
            k3.metric("Vazão", f"{vazao*3600:.1f} kg/h", "Jato pressurizado")
        
        # Alerta para hidrogênio
        if subs_nome == "Hidrogênio" and dados_gas['Hc'] > 0:
            st.warning("**ALERTA CRÍTICO - HIDROGÊNIO:** A chama de hidrogênio pode ser praticamente invisível durante "
                      "o dia devido à baixa emissão de luz visível. A chama emite radiação ultravioleta intensa que pode "
                      "causar queimaduras sem percepção visual. Utilize câmeras térmicas ou detectores de UV para localização.")
        
        # Alerta para gases inertes
        if dados_gas['Hc'] == 0:
            st.info("**Gás Não Inflamável:** Esta substância não produz chama, mas o jato pressurizado ainda representa "
                   "riscos significativos: asfixia por deslocamento de oxigênio, lesões por impacto do jato, e congelamento "
                   "devido à expansão adiabática. Estabeleça zona de exclusão baseada na velocidade e alcance do jato.")
        
        if dados_gas['Hc'] > 0:
            st.markdown("---")
            st.markdown("#### Zonas de Radiação Térmica")
            
            # Zonas de Segurança
            c1, c2, c3 = st.columns(3)
            c1.metric("Zona Letal (12.5 kW/m²)", 
                     f"{raios['Dano Estrutural / Morte (12.5 kW/m²)']:.1f} m", 
                     "Morte/Colapso estrutural", delta_color="inverse")
            c2.metric("Zona de Combate (5.0 kW/m²)", 
                     f"{raios['Combate a Incêndio (5.0 kW/m²)']:.1f} m", 
                     "Limite para bombeiros", delta_color="off")
            c3.metric("Zona de Evacuação (1.5 kW/m²)", 
                     f"{raios['Evacuação Segura (1.5 kW/m²)']:.1f} m", 
                     "Evacuação do público")

            # Mapa
            m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
            
            # Marcador da Fonte
            folium.Marker(
                [lat, lon],
                popup=f"<b>Origem do Jet Fire</b><br>Substância: {subs_nome}<br>Vazão: {vazao:.3f} kg/s<br>Pressão: {pressao} bar",
                tooltip="Ponto de Origem",
                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
            ).add_to(m)
            
            # Desenhar Zonas de Radiação (Círculos centrados na fonte)
            # Nota: O modelo assume radiação isotrópica, mas o jato real é direcional
            # Esta representação é conservadora (pior caso)
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
                        popup=f"<b>{nome}</b><br>Raio: {r:.1f} m<br>Fluxo: {dados['fluxo']} kW/m²<br><br>{dados['desc']}",
                        tooltip=f"{nome}: {r:.1f} m",
                        color=dados['cor'],
                        fill=True,
                        fillColor=dados['cor'],
                        fillOpacity=0.25,
                        weight=2
                    ).add_to(m)
            
            # Representação da Chama (Linha indicativa - assumindo direção Leste para visualização)
            # Apenas para dar noção visual do comprimento do jato
            if comp_chama > 0:
                # Conversão aproximada: 1 grau de longitude ≈ 111 km no equador
                # Ajuste para latitude média do Brasil
                fator_conversao = 111000 * math.cos(math.radians(lat))
                ponto_final = [lat, lon + (comp_chama / fator_conversao)]
                folium.PolyLine(
                    [[lat, lon], ponto_final],
                    color="#FFD700",
                    weight=6,
                    opacity=0.7,
                    tooltip=f"Comprimento da Chama: {comp_chama:.1f} m"
                ).add_to(m)
            
            st_folium(m, width=700, height=500)
            
            # Tabela de resultados
            st.markdown("#### Tabela de Zonas de Radiação Térmica")
            
            df_resultados = pd.DataFrame({
                'Zona de Risco': list(raios.keys()),
                'Fluxo Térmico (kW/m²)': [LIMITES_TERM_JET[nome]['fluxo'] for nome in raios.keys()],
                'Raio (m)': [raios[nome] for nome in raios.keys()],
                'Descrição': [LIMITES_TERM_JET[nome]['desc'] for nome in raios.keys()]
            })
            
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            # Interpretação e recomendações
            with st.expander("Interpretação dos Resultados e Recomendações Operacionais", expanded=False):
                st.markdown(f"""
                **Análise do Cenário:**
                
                - **Substância:** {subs_nome}
                - **Vazão Mássica:** {vazao:.3f} kg/s ({vazao*3600:.1f} kg/h)
                - **Pressão Interna:** {pressao} bar
                - **Diâmetro do Orifício:** {diametro} mm
                - **Temperatura:** {temp} °C
                """)
                
                if dados_gas['Hc'] > 0:
                    st.markdown(f"""
                    - **Comprimento da Chama:** {comp_chama:.1f} m
                    - **Potência Térmica Total:** {potencia:.0f} kW ({potencia/1000:.2f} MW)
                    """)
                
                st.markdown("""
                **Zonas de Risco:**
                """)
                
                for nome in zonas_ordem:
                    nome_zona = nome[0]
                    r = raios[nome_zona]
                    dados_limite = LIMITES_TERM_JET[nome_zona]
                    st.markdown(f"- **{nome_zona}:** Raio de {r:.1f} m ({dados_limite['fluxo']} kW/m²)")
                    st.markdown(f"  - {dados_limite['desc']}")
                
                st.markdown("""
                
                **Recomendações Operacionais:**
                
                1. **Evacuação Imediata:** Todas as pessoas dentro da zona de 1.5 kW/m² devem ser evacuadas imediatamente.
                
                2. **Zona de Exclusão:** Estabelecer perímetro de segurança mínimo igual ao maior raio calculado, 
                   considerando que o jato pode mudar de direção.
                
                3. **Proteção de Equipamentos Críticos:** Identificar tanques, tubulações e equipamentos dentro das 
                   zonas de radiação. O calor pode enfraquecer estruturas metálicas, causando falhas e potencialmente 
                   desencadeando eventos secundários (BLEVE, explosões).
                
                4. **Operação de Combate:** Bombeiros podem operar dentro da zona de 5.0 kW/m² apenas com equipamento 
                   de proteção térmica adequado (Bunker Gear) e tempo de exposição limitado.
                
                5. **Resfriamento Preventivo:** Aplicar água em estruturas críticas próximas para prevenir falhas por 
                   aquecimento, mas evitar direcionar água diretamente na chama (pode espalhar o fogo se houver líquido 
                   inflamável).
                
                6. **Controle do Vazamento:** Priorizar o fechamento da válvula ou isolamento da fonte. Enquanto o vazamento 
                   continuar, a chama persistirá.
                
                7. **Monitoramento:** Estabelecer pontos de observação seguros para monitorar mudanças na direção ou 
                   intensidade do jato.
                
                **Aviso Importante:** Este modelo assume radiação isotrópica (uniforme em todas as direções). Na realidade, 
                o jato de fogo é direcional e a radiação é mais intensa na direção do jato. A representação em círculos é 
                conservadora (pior caso). Fatores como vento, obstruções e geometria do vazamento podem alterar significativamente 
                os resultados. Sempre valide com observações de campo e considere múltiplos cenários.
                """)