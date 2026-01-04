import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

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
    },
    "Heptano": {
        "burn_rate": 0.072,
        "H_c": 44600,
        "density": 684,
        "desc": "Hidrocarboneto alifático. Componente de gasolina. Alta taxa de queima e radiação térmica."
    },
    "Octano": {
        "burn_rate": 0.070,
        "H_c": 44400,
        "density": 703,
        "desc": "Hidrocarboneto alifático. Componente principal de gasolina. Queima intensa e duradoura."
    },
    "Pentano": {
        "burn_rate": 0.076,
        "H_c": 45000,
        "density": 626,
        "desc": "Hidrocarboneto alifático volátil. Componente de gasolina. Taxa de queima muito alta."
    },
    "Metil Etil Cetona (MEK)": {
        "burn_rate": 0.048,
        "H_c": 31000,
        "density": 805,
        "desc": "Cetona industrial. Solvente polar comum. Queima com chama amarelada e fumaça moderada."
    },
    "Éter Dietílico": {
        "burn_rate": 0.052,
        "H_c": 33900,
        "density": 714,
        "desc": "Éter volátil. Extremamente inflamável. Baixo ponto de fulgor. Risco de explosão de vapor."
    },
    "Acetonitrila": {
        "burn_rate": 0.040,
        "H_c": 31000,
        "density": 786,
        "desc": "Nitrila volátil. Solvente polar. Queima formando HCN e NOx tóxicos. Chama azulada."
    },
    "Clorofórmio": {
        "burn_rate": 0.025,
        "H_c": 8500,
        "density": 1489,
        "desc": "Solvente clorado. Baixo poder calorífico, mas gera HCl tóxico ao queimar. Carcinogênico."
    },
    "Tetracloroetileno (PCE)": {
        "burn_rate": 0.020,
        "H_c": 8000,
        "density": 1622,
        "desc": "Solvente clorado. Não inflamável em condições normais, mas pode queimar em altas temperaturas gerando gases tóxicos."
    },
    "Óleo de Motor Usado": {
        "burn_rate": 0.035,
        "H_c": 40000,
        "density": 900,
        "desc": "Óleo lubrificante usado. Queima lenta mas persistente. Fumaça densa e tóxica. Risco de boilover."
    },
    "Óleo Vegetal (Cozinha)": {
        "burn_rate": 0.030,
        "H_c": 37000,
        "density": 920,
        "desc": "Óleo de cozinha. Queima lenta mas muito quente. Fumaça densa. Não usar água para extinguir."
    },
    "Nafta": {
        "burn_rate": 0.060,
        "H_c": 44000,
        "density": 750,
        "desc": "Fração leve de petróleo. Similar à gasolina. Usada como solvente e matéria-prima petroquímica."
    },
    "Querosene Doméstico": {
        "burn_rate": 0.043,
        "H_c": 44200,
        "density": 820,
        "desc": "Querosene para uso doméstico. Queima mais lenta que gasolina, mas com alta radiação térmica."
    },
    "Ácido Acético (Glacial)": {
        "burn_rate": 0.028,
        "H_c": 14500,
        "density": 1049,
        "desc": "Ácido orgânico. Queima com chama azulada. Gera vapores corrosivos e irritantes."
    },
    "Formaldeído (Formol)": {
        "burn_rate": 0.032,
        "H_c": 19000,
        "density": 815,
        "desc": "Aldeído volátil. Carcinogênico. Queima formando CO e vapores tóxicos. Chama quase invisível."
    }
}

# Limites de Radiação Térmica (kW/m²) - Fonte: CCPS Guidelines, TNO Green Book, API 521
LIMITES_TERMICOS = {
    "Zona Letal (Morte/Danos Estruturais)": {
        "fluxo": 12.5,
        "cor": "#e74c3c",
        "desc": "Morte em segundos por exposição prolongada. Ignição espontânea de madeira. "
               "Plásticos derretem. Falha estrutural de materiais não protegidos."
    },
    "Zona de Lesão (Queimaduras Graves)": {
        "fluxo": 5.0,
        "cor": "#f39c12",
        "desc": "Queimaduras de segundo grau em aproximadamente 45 segundos de exposição. "
               "Dor intensa e incapacitação. Limite máximo para operação de bombeiros com equipamento de proteção térmica."
    },
    "Zona de Alerta (Segurança Pública)": {
        "fluxo": 1.5,
        "cor": "#f1c40f",
        "desc": "Limite para evacuação segura do público geral. Desconforto térmico significativo, "
               "mas possível evacuação sem lesões graves em tempo limitado. Equivalente a radiação solar intensa."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (MUDAN & CROCE SIMPLIFICADO)
# =============================================================================
def calcular_pool_fire(area_poca, material):
    """
    Calcula a radiação térmica de um pool fire usando o modelo de Fonte Pontual (Point Source Model).
    Este modelo é adequado para distâncias de segurança (> 2 diâmetros da poça).
    
    Parâmetros:
        area_poca: Área da poça de líquido em chamas (m²)
        material: Dicionário com propriedades do combustível (burn_rate, H_c, density)
    
    Retorna:
        Tupla: (raios, altura_chama, diametro, Q_total)
        - raios: Dicionário com raios de cada zona de radiação térmica
        - altura_chama: Altura da chama em metros
        - diametro: Diâmetro da poça em metros
        - Q_total: Potência térmica total irradiada em kW
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
    Estima a área de uma poça formada por derramamento livre de líquido.
    Assume solo plano não permeável com espessura média de 1 cm (0.01 m).
    
    Parâmetros:
        massa_kg: Massa do líquido derramado (kg)
        densidade: Densidade do líquido (kg/m³)
    
    Retorna:
        Área estimada da poça em metros quadrados (m²)
    """
    if densidade <= 0:
        return 0.0
    
    volume = massa_kg / densidade  # m³
    espessura_media = 0.01  # 1 cm (valor típico para derramamento livre)
    area = volume / espessura_media
    
    return area

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Incêndio em Poça")
    st.markdown("**Modelagem de Pool Fire: Análise de Radiação Térmica de Líquidos Inflamáveis**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de Pool Fire", expanded=True):
        st.markdown("""
        **O que é um Pool Fire?**
        
        Um Pool Fire (incêndio em poça) ocorre quando um líquido inflamável derrama e é inflamado, 
        formando uma poça de fogo na superfície. O principal mecanismo de transferência de calor é a 
        radiação térmica, que se propaga em todas as direções a partir da chama.
        
        **Fatores Críticos:**
        
        1. **Confinamento:**
           - **Poça Confinada (Dique/Bacia):** O líquido fica contido em uma área fixa. O fogo é mais 
             concentrado e duradouro, mas a área é limitada pela contenção.
           - **Derramamento Livre:** O líquido se espalha até atingir uma espessura mínima (tipicamente 
             ~1 cm em solo não permeável). A poça pode ser muito grande, gerando um incêndio extenso, 
             mas o combustível se esgota mais rapidamente.
        
        2. **Radiação Térmica (kW/m²):**
           - Diferente da temperatura do ar, a radiação térmica é energia eletromagnética que se propaga 
             em linha reta, similar ao calor do sol, mas muito mais intensa.
           - **12.5 kW/m²:** Morte em segundos. Ignição espontânea de materiais combustíveis. 
             Falha estrutural de materiais não protegidos.
           - **5.0 kW/m²:** Limite para operação de bombeiros com equipamento de proteção térmica 
             (Bunker Gear). Queimaduras de segundo grau em ~45 segundos.
           - **1.5 kW/m²:** Limite para evacuação segura do público. Desconforto térmico, mas possível 
             evacuação sem lesões graves.
        
        3. **Taxa de Queima:**
           - Cada líquido tem uma taxa de queima característica (kg/m²/s), que determina a velocidade 
             de consumo do combustível e a intensidade do fogo.
           - Líquidos mais voláteis (gasolina, acetona) queimam mais rápido que líquidos pesados 
             (diesel, óleos).
        
        **Metodologia de Cálculo:**
        
        Este módulo utiliza o Modelo de Fonte Pontual (Point Source Model), adequado para distâncias 
        maiores que 2 diâmetros da poça:
        
        1. **Taxa de Liberação de Calor (HRR):** Calculada a partir da taxa de queima, área da poça e 
           calor de combustão, com fator de eficiência radiativa (~35% para hidrocarbonetos).
        
        2. **Altura da Chama:** Estimada usando correlação de Thomas, baseada na taxa de queima e 
           diâmetro da poça.
        
        3. **Radiação Térmica:** Calculada usando a lei do inverso do quadrado, assumindo que toda 
           a energia radiante emana do centro da chama.
        
        **Limitações do Modelo:**
        
        Este modelo assume condições ideais e não considera:
        - Efeitos de vento na forma e direção da chama
        - Obstruções que podem bloquear ou redirecionar a radiação
        - Variações na fração de radiação com a distância
        - Efeitos de múltiplas poças ou interações complexas
        - Boilover (expulsão violenta) em tanques com água no fundo
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros do Combustível")
        
        tipo_combustivel = st.selectbox("Líquido Inflamável", list(COMBUSTIVEIS.keys()))
        dados_comb = COMBUSTIVEIS[tipo_combustivel]
        
        st.info(f"**{tipo_combustivel}**\n\n**Descrição:** {dados_comb['desc']}\n\n"
               f"**Taxa de Queima:** {dados_comb['burn_rate']} kg/m²/s\n"
               f"**Calor de Combustão:** {dados_comb['H_c']} kJ/kg\n"
               f"**Densidade:** {dados_comb['density']} kg/m³")
        
        st.subheader("Georreferenciamento")
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f")

    with col2:
        st.subheader("Configuração do Vazamento")
        
        modo_calculo = st.radio("Tipo de Cenário:", 
                                ["Derramamento Livre (Chão Aberto)", "Poça Confinada (Dique/Bacia)"],
                                help="Derramamento livre: líquido se espalha até ~1 cm de espessura. "
                                    "Poça confinada: líquido contido em área fixa.")
        
        area_calc = 0.0
        
        if modo_calculo == "Derramamento Livre (Chão Aberto)":
            massa = st.number_input("Massa do Líquido Vazado (kg)", value=1000.0, min_value=1.0, step=100.0, 
                                   help="Quantidade total de líquido derramado.")
            # Cálculo automático da área
            area_calc = estimar_area_poca(massa, dados_comb['density'])
            st.metric("Área Estimada da Poça", f"{area_calc:.1f} m²", 
                     f"Espessura média: ~1 cm", 
                     help="Área calculada assumindo derramamento livre em solo não permeável com espessura média de 1 cm.")
            
        else:
            area_calc = st.number_input("Área do Dique/Bacia (m²)", value=20.0, min_value=0.1, step=5.0, 
                                       help="Área da bacia de contenção ou dique onde o líquido está confinado.")
            st.caption("Em poças confinadas, a área é fixa e a profundidade aumenta com a quantidade de líquido.")

    # Estado
    if 'fire_calc' not in st.session_state:
        st.session_state['fire_calc'] = False
    
    if st.button("Calcular Pool Fire", type="primary", use_container_width=True):
        st.session_state['fire_calc'] = True

    if st.session_state['fire_calc']:
        # Cálculos
        raios, altura, diametro, potencia = calcular_pool_fire(area_calc, dados_comb)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        k1, k2, k3 = st.columns(3)
        k1.metric("Altura da Chama", f"{altura:.1f} m", "Altura do jato de fogo", 
                 help="Altura estimada da chama usando correlação de Thomas")
        k2.metric("Diâmetro da Poça", f"{diametro:.1f} m", "Diâmetro da base", 
                 help="Diâmetro equivalente da poça de líquido em chamas")
        k3.metric("Potência Irradiada", f"{potencia/1000:.2f} MW", f"{potencia:.0f} kW", 
                 help="Potência térmica total irradiada pela chama")

        st.markdown("---")
        st.markdown("#### Zonas de Radiação Térmica")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Letal (12.5 kW/m²)", 
                 f"{raios['Zona Letal (Morte/Danos Estruturais)']:.1f} m", 
                 "Morte em segundos", delta_color="inverse")
        c2.metric("Zona de Lesão (5.0 kW/m²)", 
                 f"{raios['Zona de Lesão (Queimaduras Graves)']:.1f} m", 
                 "Limite para bombeiros", delta_color="off")
        c3.metric("Zona de Alerta (1.5 kW/m²)", 
                 f"{raios['Zona de Alerta (Segurança Pública)']:.1f} m", 
                 "Evacuação do público")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
        
        # Marcador do Fogo
        folium.Marker(
            [lat, lon],
            popup=f"<b>Pool Fire</b><br>Combustível: {tipo_combustivel}<br>Área: {area_calc:.1f} m²<br>Potência: {potencia/1000:.2f} MW",
            tooltip="Ponto de Origem",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)
        
        # Círculo representando a poça
        raio_poca = diametro / 2
        folium.Circle(
            [lat, lon],
            radius=raio_poca,
            popup=f"<b>Poça de Líquido</b><br>Diâmetro: {diametro:.1f} m<br>Área: {area_calc:.1f} m²",
            tooltip=f"Poça: {diametro:.1f} m",
            color="#8B0000",
            fill=True,
            fillColor="#FF0000",
            fillOpacity=0.5,
            weight=2
        ).add_to(m)
        
        # Desenhar Zonas de Radiação (Do maior para o menor)
        zonas_ordem = [
            ("Zona de Alerta (Segurança Pública)", LIMITES_TERMICOS["Zona de Alerta (Segurança Pública)"]),
            ("Zona de Lesão (Queimaduras Graves)", LIMITES_TERMICOS["Zona de Lesão (Queimaduras Graves)"]),
            ("Zona Letal (Morte/Danos Estruturais)", LIMITES_TERMICOS["Zona Letal (Morte/Danos Estruturais)"])
        ]
        
        for nome, dados in zonas_ordem:
            r = raios[nome]
            if r > raio_poca:  # Só desenhar se a zona estiver além da poça
                folium.Circle(
                    [lat, lon],
                    radius=r,
                    popup=f"<b>{nome}</b><br>Raio: {r:.1f} m<br>Fluxo: {dados['fluxo']} kW/m²<br><br>{dados['desc']}",
                    tooltip=f"{nome}: {r:.1f} m ({dados['fluxo']} kW/m²)",
                    color=dados['cor'],
                    fill=True,
                    fillColor=dados['cor'],
                    fillOpacity=0.25,
                    weight=2
                ).add_to(m)
            
        st_folium(m, width=700, height=500)
        
        # Tabela de resultados
        st.markdown("#### Tabela de Zonas de Radiação Térmica")
        
        df_resultados = pd.DataFrame({
            'Zona de Risco': list(raios.keys()),
            'Fluxo Térmico (kW/m²)': [LIMITES_TERMICOS[nome]['fluxo'] for nome in raios.keys()],
            'Raio (m)': [raios[nome] for nome in raios.keys()],
            'Descrição': [LIMITES_TERMICOS[nome]['desc'] for nome in raios.keys()]
        })
        
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)
        
        # Interpretação e recomendações
        with st.expander("Interpretação dos Resultados e Recomendações Operacionais", expanded=False):
            st.markdown(f"""
            **Análise do Cenário:**
            
            - **Combustível:** {tipo_combustivel}
            - **Área da Poça:** {area_calc:.1f} m²
            - **Diâmetro:** {diametro:.1f} m
            - **Altura da Chama:** {altura:.1f} m
            - **Potência Irradiada:** {potencia:.0f} kW ({potencia/1000:.2f} MW)
            """)
            
            st.markdown("""
            **Zonas de Risco:**
            """)
            
            for nome, dados in zonas_ordem:
                r = raios[nome]
                st.markdown(f"- **{nome}:** Raio de {r:.1f} m ({dados['fluxo']} kW/m²)")
                st.markdown(f"  - {dados['desc']}")
            
            st.markdown("""
            
            **Recomendações Operacionais:**
            
            1. **Evacuação Imediata:** Todas as pessoas dentro da zona de 1.5 kW/m² devem ser evacuadas 
               imediatamente. A zona letal (12.5 kW/m²) representa morte quase certa em segundos.
            
            2. **Zona de Exclusão:** Estabelecer perímetro de segurança mínimo igual ao maior raio calculado, 
               considerando que o vento pode inclinar a chama e aumentar a radiação em certas direções.
            
            3. **Proteção de Estruturas Críticas:** Identificar estruturas críticas (hospitais, escolas, 
               tanques adjacentes) dentro das zonas de radiação. O calor intenso pode causar falhas estruturais 
               e potencialmente desencadear eventos secundários (BLEVE, explosões).
            
            4. **Operação de Combate:** Bombeiros podem operar dentro da zona de 5.0 kW/m² apenas com 
               equipamento de proteção térmica adequado (Bunker Gear) e tempo de exposição limitado. 
               Aplicar água em estruturas críticas próximas para prevenir falhas por aquecimento.
            
            5. **Resfriamento Preventivo:** Aplicar água ou espuma em tanques e estruturas adjacentes para 
               prevenir aquecimento e potenciais falhas. Evitar direcionar água diretamente na poça de 
               líquidos imiscíveis com água (pode espalhar o fogo).
            
            6. **Controle do Combustível:** Priorizar o fechamento de válvulas ou isolamento da fonte de 
               vazamento. Enquanto o vazamento continuar, o fogo persistirá.
            
            7. **Monitoramento:** Estabelecer pontos de observação seguros para monitorar mudanças na 
               intensidade ou direção do fogo.
            
            **Aviso Importante:** Este modelo assume radiação isotrópica (uniforme em todas as direções). 
            Na realidade, o vento pode inclinar a chama, aumentando a radiação na direção do vento e 
            reduzindo na direção oposta. Fatores como obstruções, múltiplas poças e geometria complexa 
            podem alterar significativamente os resultados. Sempre valide com observações de campo e 
            considere múltiplos cenários.
            """)

