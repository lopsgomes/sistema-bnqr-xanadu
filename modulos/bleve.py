import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS: SUBSTÂNCIAS INFLAMÁVEIS PRESSURIZADAS
# =============================================================================
# Propriedades para cálculo de BLEVE
# Hc: Calor de Combustão (kJ/kg)
# Fator TNT: Equivalência aproximada de energia explosiva (mecânica + química)
SUBSTANCIAS_BLEVE = {
    "Acetileno": {
        "Hc": 48200, 
        "fator_tnt": 0.6, # Quimicamente instável, explosão violenta
        "desc": "Gás de solda instável. Pode detonar mesmo sem oxigênio. Bola de fogo muito fuliginosa e quente."
    },
    "Amônia Anidra (Inflamável)": {
        "Hc": 18600, 
        "fator_tnt": 0.15, 
        "desc": "Embora tóxica, queima se houver fonte de ignição forte. BLEVE menos energético, mas dispersa nuvem tóxica."
    },
    "Butadieno (1,3)": {
        "Hc": 45500, 
        "fator_tnt": 0.45, 
        "desc": "Matéria-prima de borracha sintética. Pode polimerizar violentamente dentro do tanque se aquecido."
    },
    "Butano (GLP Doméstico)": {
        "Hc": 45750, 
        "fator_tnt": 0.35, 
        "desc": "Gás de isqueiro/fogão. Pressão menor que o Propano, mas gera bola de fogo intensa e duradoura."
    },
    "Cloreto de Metila": {
        "Hc": 13200, 
        "fator_tnt": 0.15, 
        "desc": "Refrigerante antigo. Queima difícil, mas sob BLEVE gera bola de fogo e gases clorados tóxicos."
    },
    "Cloreto de Vinila": {
        "Hc": 19000, 
        "fator_tnt": 0.25, 
        "desc": "Monômero de PVC (Acidente de Ohio). Bola de fogo tóxica que gera Fosgênio e HCl."
    },
    "Dimetil Éter (DME)": {
        "Hc": 28900, 
        "fator_tnt": 0.3, 
        "desc": "Combustível alternativo ao Diesel. Comportamento similar ao GLP, chama azulada."
    },
    "Etano": {
        "Hc": 47500, 
        "fator_tnt": 0.4, 
        "desc": "Gás comum em plantas petroquímicas. Pressão de vapor alta, ruptura do tanque é muito violenta."
    },
    "Etileno": {
        "Hc": 47100, 
        "fator_tnt": 0.5, 
        "desc": "Matéria-prima de plásticos. Explosão extremamente rápida, reativa e violenta."
    },
    "Gás Natural (Metano/GNV)": {
        "Hc": 50000, 
        "fator_tnt": 0.3, 
        "desc": "GNV ou GNL. Tende a subir rápido, mas se confinado ou liquefeito (LNG), o BLEVE é catastrófico."
    },
    "Hidrogênio": {
        "Hc": 120000, 
        "fator_tnt": 0.2, # Massa muito leve, dissipa rápido
        "desc": "Energia por kg altíssima, mas bola de fogo sobe muito rápido (efeito balão). Chama invisível de dia."
    },
    "Isobutano": {
        "Hc": 45600, 
        "fator_tnt": 0.35, 
        "desc": "Gás refrigerante (R600a). Comum em geladeiras modernas. Inflamabilidade extrema."
    },
    "Óxido de Etileno": {
        "Hc": 29000, 
        "fator_tnt": 0.8, # Decompõe explosivamente
        "desc": "Esterilizante hospitalar. Altamente reativo. O BLEVE envolve decomposição química interna (muito forte)."
    },
    "Propano (GLP Industrial)": {
        "Hc": 46350, 
        "fator_tnt": 0.4, 
        "desc": "Gás de cozinha/empilhadeira. Tanques prateados. O cenário padrão de BLEVE rodoviário."
    },
    "Propileno": {
        "Hc": 45800, 
        "fator_tnt": 0.45, 
        "desc": "Similar ao Propano, mas com dupla ligação química. Queima mais quente e instável."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "Hc": 15200, 
        "fator_tnt": 0.15, 
        "desc": "Gás ácido/tóxico. O BLEVE espalha uma nuvem letal de SO2 (queima) e gás tóxico não queimado."
    },
    "Metanol": {
        "Hc": 19900,
        "fator_tnt": 0.25,
        "desc": "Álcool metílico. Combustível alternativo. BLEVE gera bola de fogo com chama quase invisível. Tóxico por inalação."
    },
    "Etanol": {
        "Hc": 26800,
        "fator_tnt": 0.30,
        "desc": "Álcool etílico. Combustível e solvente. BLEVE produz bola de fogo intensa. Usado em indústria e como biocombustível."
    },
    "Pentano": {
        "Hc": 45000,
        "fator_tnt": 0.35,
        "desc": "Hidrocarboneto alifático. Componente de gasolina. Pressão de vapor alta, BLEVE muito energético."
    },
    "Hexano": {
        "Hc": 44700,
        "fator_tnt": 0.35,
        "desc": "Hidrocarboneto alifático. Solvente industrial comum. BLEVE gera bola de fogo grande e duradoura."
    },
    "Heptano": {
        "Hc": 44600,
        "fator_tnt": 0.35,
        "desc": "Hidrocarboneto alifático. Componente de gasolina. BLEVE similar ao hexano, mas com maior massa por volume."
    },
    "Octano": {
        "Hc": 44400,
        "fator_tnt": 0.35,
        "desc": "Hidrocarboneto alifático. Componente principal de gasolina. BLEVE muito energético devido à alta densidade."
    },
    "Benzeno": {
        "Hc": 40000,
        "fator_tnt": 0.30,
        "desc": "Hidrocarboneto aromático. Carcinogênico. BLEVE gera bola de fogo e nuvem tóxica. Muito usado em petroquímica."
    },
    "Tolueno": {
        "Hc": 40500,
        "fator_tnt": 0.30,
        "desc": "Hidrocarboneto aromático. Solvente comum. BLEVE similar ao benzeno, mas menos tóxico."
    },
    "Xileno": {
        "Hc": 40800,
        "fator_tnt": 0.30,
        "desc": "Hidrocarboneto aromático. Solvente industrial. BLEVE gera bola de fogo e vapores tóxicos."
    },
    "Acetona": {
        "Hc": 29000,
        "fator_tnt": 0.25,
        "desc": "Cetona volátil. Solvente muito comum. BLEVE gera bola de fogo moderada. Vapor mais pesado que o ar."
    },
    "Metil Etil Cetona (MEK)": {
        "Hc": 31000,
        "fator_tnt": 0.25,
        "desc": "Cetona industrial. Solvente polar. BLEVE similar à acetona, mas com maior poder calorífico."
    },
    "Éter Dietílico": {
        "Hc": 33900,
        "fator_tnt": 0.40,
        "desc": "Éter volátil. Extremamente inflamável. BLEVE muito perigoso devido à baixa temperatura de ignição e alta volatilidade."
    },
    "Clorofórmio": {
        "Hc": 0,
        "fator_tnt": 0.10,
        "desc": "Solvente clorado não inflamável. BLEVE sem chama, mas expansão violenta e nuvem tóxica. Carcinogênico."
    },
    "Tetracloroetileno (PCE)": {
        "Hc": 0,
        "fator_tnt": 0.10,
        "desc": "Solvente clorado não inflamável. BLEVE sem chama, mas expansão violenta. Carcinogênico provável."
    },
    "Metil Mercaptano": {
        "Hc": 28000,
        "fator_tnt": 0.20,
        "desc": "Tiol volátil. Odor extremamente forte. BLEVE gera bola de fogo e SO2 tóxico. Usado como odorizante de gás."
    }
}

# Limites de Dano (Térmico e Sobrepressão)
# Fonte: CCPS Guidelines, TNO Yellow Book, API 521
LIMITES_BLEVE = {
    "Bola de Fogo (Raio Máximo)": {
        "tipo": "Fogo",
        "cor": "#8B0000",
        "desc": "Raio físico da bola de fogo. Incineração total de qualquer material dentro desta zona."
    },
    "Radiação Térmica Fatal (12.5 kW/m²)": {
        "tipo": "Térmico",
        "cor": "#e74c3c",
        "desc": "Morte em segundos por exposição. Ignição espontânea de materiais combustíveis. Falha estrutural de materiais não protegidos."
    },
    "Queimaduras de 2º Grau (5.0 kW/m²)": {
        "tipo": "Térmico",
        "cor": "#f39c12",
        "desc": "Queimaduras de segundo grau em aproximadamente 45 segundos de exposição. Dor intensa e incapacitação."
    },
    "Dano Estrutural Leve (0.03 bar / 0.5 psi)": {
        "tipo": "Explosão",
        "cor": "#34495e",
        "desc": "Onda de choque (blast wave). Quebra de vidros e janelas. Danos estruturais leves em alvenaria. "
               "Pessoas podem ser derrubadas pelo vento da explosão."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (CCPS / TNO YELLOW BOOK)
# =============================================================================
def calcular_bleve(massa_kg, substancia):
    """
    Calcula os efeitos físicos do BLEVE (Boiling Liquid Expanding Vapor Explosion).
    
    Parâmetros:
        massa_kg: Massa do líquido pressurizado envolvida no BLEVE (kg)
        substancia: Dicionário com propriedades da substância (Hc, fator_tnt)
    
    Retorna:
        Tupla: (raios_impacto, diametro_fogo, tempo_fogo, kg_tnt)
        - raios_impacto: Dicionário com raios de cada zona de dano
        - diametro_fogo: Diâmetro da bola de fogo (m)
        - tempo_fogo: Duração da bola de fogo (s)
        - kg_tnt: Equivalente em TNT (kg)
    """
    # 1. Diâmetro da Bola de Fogo (Fireball)
    # Correlação CCPS baseada em estudos empíricos: D = 5.8 * M^(1/3)
    # O diâmetro é proporcional à raiz cúbica da massa (lei de escala)
    if massa_kg > 0:
        diametro_fogo = 5.8 * (massa_kg ** (1/3))
        raio_fogo = diametro_fogo / 2
    else:
        diametro_fogo = 0
        raio_fogo = 0
    
    # 2. Duração da Bola de Fogo (segundos)
    # Correlação CCPS: T = 0.45 * M^(1/3) para massas < 30.000 kg
    # Para massas maiores, a duração pode ser subestimada
    if massa_kg > 0:
        tempo_fogo = 0.45 * (massa_kg ** (1/3))
    else:
        tempo_fogo = 0
    
    # 3. Radiação Térmica (Point Source Model simplificado para BLEVE)
    # A emissividade de um BLEVE é altíssima (~350 kW/m² na superfície)
    # SEP (Surface Emissive Power) médio ≈ 270 kW/m² (CCPS Guidelines)
    SEP = 270.0 
    
    # Transmissividade atmosférica (tau): fração de radiação que atravessa a atmosfera
    # Valor médio de 0.7 assume condições atmosféricas normais
    tau = 0.7 
    
    raios_impacto = {}
    
    # Apenas calcular raios se houver massa e a substância for inflamável
    if massa_kg > 0 and substancia['Hc'] > 0:
        raios_impacto["Bola de Fogo (Raio Máximo)"] = raio_fogo

        # Cálculo de distâncias térmicas usando modelo simplificado
        # Para campo distante: I = (tau * SEP * ViewFactor)
        # Simplificação: r = (D/2) * sqrt((tau * SEP) / I_alvo)
        for nome, dados in LIMITES_BLEVE.items():
            if dados['tipo'] == "Térmico":
                limite_kw = 12.5 if "Fatal" in nome else 5.0
                
                # Fórmula prática CCPS
                if diametro_fogo > 0 and limite_kw > 0:
                    r = (diametro_fogo / 2) * math.sqrt((tau * SEP) / limite_kw)
                    raios_impacto[nome] = r
                else:
                    raios_impacto[nome] = 0
    else:
        # Para substâncias não inflamáveis, não há bola de fogo
        raios_impacto["Bola de Fogo (Raio Máximo)"] = 0
        raios_impacto["Radiação Térmica Fatal (12.5 kW/m²)"] = 0
        raios_impacto["Queimaduras de 2º Grau (5.0 kW/m²)"] = 0

    # 4. Onda de Choque (Blast) - Equivalência TNT
    # A energia explosiva inclui tanto a expansão física quanto a energia química (se inflamável)
    # Energia = Massa * Hc * Fator_Eficiencia
    # 1 kg TNT ≈ 4680 kJ
    if massa_kg > 0:
        energia_total_kj = massa_kg * substancia['Hc'] * substancia['fator_tnt']
        kg_tnt = energia_total_kj / 4680.0
        
        # Estimativa de raio de dano (Sobrepressão 0.03 bar / 0.5 psi - quebra vidros/danos leves)
        # Hopkinson-Cranz Scaling Law: Z = R / (W^(1/3))
        # Para 0.03 bar (aprox 0.5 psi), Z ≈ 20 a 30. Usaremos 25 (conservador).
        if kg_tnt > 0:
            raio_blast = 25 * (kg_tnt ** (1/3))
        else:
            raio_blast = 0
    else:
        kg_tnt = 0
        raio_blast = 0
    
    raios_impacto["Dano Estrutural Leve (0.03 bar / 0.5 psi)"] = raio_blast

    return raios_impacto, diametro_fogo, tempo_fogo, kg_tnt

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Catástrofe de Expansão (BLEVE)")
    st.markdown("**Modelagem de BLEVE: Análise de Ruptura Catastrófica de Tanques Pressurizados**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de BLEVE", expanded=True):
        st.markdown("""
        **O que é um BLEVE?**
        
        BLEVE (Boiling Liquid Expanding Vapor Explosion) é uma explosão catastrófica que ocorre quando um 
        líquido pressurizado acima de seu ponto de ebulição sofre uma falha estrutural do recipiente, 
        causando expansão violenta e instantânea do vapor.
        
        **Mecanismo Físico:**
        
        1. **Condição Inicial:** Um líquido está contido em um tanque pressurizado a uma temperatura acima 
           de seu ponto de ebulição à pressão atmosférica. A pressão interna mantém o líquido no estado líquido.
        
        2. **Falha Estrutural:** O tanque falha devido a sobrepressão, impacto, corrosão ou aquecimento 
           externo (ex: incêndio próximo). A pressão interna cai instantaneamente.
        
        3. **Expansão Instantânea:** Com a queda de pressão, o líquido superaquecido vaporiza instantaneamente 
           (flash vaporization), expandindo-se violentamente.
        
        4. **Efeitos Duplos:**
           - **Bola de Fogo (Fireball):** Se o vapor for inflamável e encontrar uma fonte de ignição, 
             forma-se uma bola de fogo gigante que sobe rapidamente. A radiação térmica é extremamente intensa.
           - **Onda de Choque (Blast Wave):** A expansão física do vapor empurra o ar circundante, 
             criando uma onda de choque que se propaga radialmente, causando danos estruturais.
        
        **Cenários Típicos:**
        
        - Acidentes rodoviários onde fogo externo aquece um tanque de GLP até a falha estrutural
        - Falhas em tanques de armazenamento industrial devido a sobrepressão ou corrosão
        - Incêndios em instalações petroquímicas que aquecem tanques adjacentes
        - Falhas em sistemas de refrigeração com fluidos pressurizados
        
        **Metodologia de Cálculo:**
        
        Este módulo utiliza correlações empíricas baseadas em CCPS Guidelines e TNO Yellow Book:
        - **Diâmetro da Bola de Fogo:** Correlação CCPS baseada na massa envolvida
        - **Duração:** Tempo de queima proporcional à raiz cúbica da massa
        - **Radiação Térmica:** Modelo de ponto fonte com SEP (Surface Emissive Power) de 270 kW/m²
        - **Onda de Choque:** Equivalência TNT usando lei de escala de Hopkinson-Cranz
        
        **Limitações do Modelo:**
        
        Este modelo assume condições ideais e não considera:
        - Efeitos de vento na forma e direção da bola de fogo
        - Obstruções que podem redirecionar a expansão
        - Variações na fração de energia convertida em radiação vs. onda de choque
        - Efeitos de múltiplas falhas simultâneas ou eventos em cascata
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros da Substância")
        
        subs_nome = st.selectbox("Substância no Tanque", list(SUBSTANCIAS_BLEVE.keys()))
        dados_subs = SUBSTANCIAS_BLEVE[subs_nome]
        
        st.info(f"**{subs_nome}**\n\n**Descrição:** {dados_subs['desc']}\n\n"
               f"**Calor de Combustão:** {dados_subs['Hc']} kJ/kg\n"
               f"**Fator TNT:** {dados_subs['fator_tnt']:.2f}")
        
        if dados_subs['Hc'] == 0:
            st.warning("**Substância Não Inflamável:** Esta substância não produzirá bola de fogo, "
                      "mas a expansão violenta do vapor ainda causará onda de choque significativa.")

    with col2:
        st.subheader("Configuração do Tanque")
        
        cap_total = st.number_input("Capacidade Total do Tanque (kg)", value=15000.0, min_value=100.0, 
                                   step=1000.0, help="Capacidade máxima do tanque. Carretas rodoviárias típicas: 20-30 toneladas.")
        percent = st.slider("Nível de Enchimento (%)", 10, 100, 70, 
                          help="Percentual da capacidade preenchido. Tanques 70-80% cheios geram BLEVEs mais severos que tanques vazios.")
        
        massa_real = cap_total * (percent / 100.0)
        st.metric("Massa Envolvida no BLEVE", f"{massa_real/1000:.2f} toneladas", f"{massa_real:.0f} kg")
        
        st.subheader("Georreferenciamento")
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f")

    # Botão de cálculo
    if 'bleve_calc' not in st.session_state:
        st.session_state['bleve_calc'] = False
    
    if st.button("Calcular BLEVE", type="primary", use_container_width=True):
        st.session_state['bleve_calc'] = True

    if st.session_state['bleve_calc']:
        # Calcular BLEVE
        raios, diametro, duracao, tnt_eq = calcular_bleve(massa_real, dados_subs)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        k1, k2, k3 = st.columns(3)
        if dados_subs['Hc'] > 0:
            k1.metric("Diâmetro da Bola de Fogo", f"{diametro:.1f} m", "Raio físico da bola de fogo", delta_color="inverse")
            k2.metric("Duração da Bola de Fogo", f"{duracao:.1f} s", "Tempo de queima")
        else:
            k1.metric("Tipo de Evento", "Expansão de Vapor", "Sem chama")
            k2.metric("Expansão Instantânea", "Violenta", "Vapor superaquecido")
        k3.metric("Equivalência TNT", f"{tnt_eq/1000:.2f} toneladas", f"{tnt_eq:.0f} kg", delta_color="inverse")
        
        st.markdown("---")
        st.markdown("#### Zonas de Impacto")
        
        # Resultados de segurança
        c1, c2, c3, c4 = st.columns(4)
        if dados_subs['Hc'] > 0:
            c1.metric("Bola de Fogo", f"{raios['Bola de Fogo (Raio Máximo)']:.0f} m", "Incineração total")
            c2.metric("Zona Letal (12.5 kW/m²)", f"{raios['Radiação Térmica Fatal (12.5 kW/m²)']:.0f} m", "Morte em segundos")
            c3.metric("Queimaduras Graves (5.0 kW/m²)", f"{raios['Queimaduras de 2º Grau (5.0 kW/m²)']:.0f} m", "Queimaduras 2º grau")
        else:
            c1.metric("Tipo", "Sem Bola de Fogo", "Substância não inflamável")
            c2.metric("Zona Letal", "N/A", "Apenas expansão")
            c3.metric("Queimaduras", "N/A", "Apenas expansão")
        c4.metric("Onda de Choque (0.5 psi)", f"{raios['Dano Estrutural Leve (0.03 bar / 0.5 psi)']:.0f} m", "Quebra de vidros")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
        
        # Marcador do Epicentro
        folium.Marker(
                [lat, lon],
                popup=f"<b>Epicentro do BLEVE</b><br>Substância: {subs_nome}<br>Massa: {massa_real/1000:.2f} toneladas<br>Equivalente TNT: {tnt_eq/1000:.2f} ton",
                tooltip="Ponto de Origem",
                icon=folium.Icon(color="black", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)
        
        # Desenhar círculos de dano (ordenados do maior para o menor)
        lista_ordenada = sorted(raios.items(), key=lambda x: x[1], reverse=True)
        
        for nome, raio in lista_ordenada:
            if raio > 0:
                dados_limite = LIMITES_BLEVE[nome]
                cor = dados_limite['cor']
                desc = dados_limite['desc']
                
                # Círculo de Blast (linha sem preenchimento para diferenciar)
                if "Dano Estrutural" in nome:
                    folium.Circle(
                        [lat, lon],
                        radius=raio,
                        popup=f"<b>{nome}</b><br>Raio: {raio:.0f} m<br><br>{desc}",
                        tooltip=f"Onda de Choque: {raio:.0f} m",
                        color="#34495e",
                        weight=3,
                        fill=False,
                        dashArray='10, 5'
                    ).add_to(m)
                else:
                    folium.Circle(
                        [lat, lon],
                        radius=raio,
                        popup=f"<b>{nome}</b><br>Raio: {raio:.0f} m<br><br>{desc}",
                        tooltip=f"{nome}: {raio:.0f} m",
                        color=cor,
                        fill=True,
                        fillColor=cor,
                        fillOpacity=0.3,
                        weight=2
                    ).add_to(m)
        
        st_folium(m, width=700, height=500)
        
        # Tabela de resultados
        st.markdown("#### Tabela de Zonas de Impacto")
        
        df_resultados = pd.DataFrame({
            'Zona de Impacto': list(raios.keys()),
            'Tipo': [LIMITES_BLEVE[nome]['tipo'] for nome in raios.keys()],
            'Raio (m)': [raios[nome] for nome in raios.keys()],
            'Descrição': [LIMITES_BLEVE[nome]['desc'] for nome in raios.keys()]
        })
        
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)
        
        # Interpretação e recomendações
        with st.expander("Interpretação dos Resultados e Recomendações Operacionais", expanded=False):
                st.markdown(f"""
                **Análise do Cenário:**
                
                - **Substância:** {subs_nome}
                - **Massa Envolvida:** {massa_real/1000:.2f} toneladas ({massa_real:.0f} kg)
                - **Nível de Enchimento:** {percent}% da capacidade total
                """)
                
                if dados_subs['Hc'] > 0:
                    st.markdown(f"""
                    - **Diâmetro da Bola de Fogo:** {diametro:.1f} m
                    - **Duração:** {duracao:.1f} segundos
                    - **Equivalência TNT:** {tnt_eq/1000:.2f} toneladas ({tnt_eq:.0f} kg)
                    """)
                else:
                    st.markdown(f"""
                    - **Tipo de Evento:** Expansão de vapor não inflamável (sem bola de fogo)
                    - **Equivalência TNT:** {tnt_eq/1000:.2f} toneladas ({tnt_eq:.0f} kg) - apenas expansão física
                    """)
                
                st.markdown("""
                **Zonas de Risco:**
                """)
                
                for nome in lista_ordenada:
                    nome_zona = nome[0]
                    r = raios[nome_zona]
                    dados_limite = LIMITES_BLEVE[nome_zona]
                    if r > 0:
                        st.markdown(f"- **{nome_zona}:** Raio de {r:.0f} m")
                        st.markdown(f"  - {dados_limite['desc']}")
                
                st.markdown("""
                
                **Recomendações Operacionais:**
                
                1. **Evacuação Imediata:** Todas as pessoas dentro da zona de 5.0 kW/m² devem ser evacuadas 
                   imediatamente. A zona letal (12.5 kW/m²) representa morte quase certa em segundos.
                
                2. **Zona de Exclusão:** Estabelecer perímetro de segurança mínimo igual ao maior raio calculado, 
                   considerando tanto efeitos térmicos quanto a onda de choque.
                
                3. **Proteção de Estruturas Críticas:** Identificar estruturas críticas (hospitais, escolas, 
                   usinas, tanques adjacentes) dentro das zonas de impacto. O calor intenso pode causar falhas 
                   em cascata (efeito dominó).
                
                4. **Resfriamento Preventivo:** Se possível, aplicar água em tanques adjacentes para prevenir 
                   aquecimento e potenciais BLEVEs secundários. Evitar direcionar água diretamente na bola de 
                   fogo (ineficaz e perigoso).
                
                5. **Operação de Combate:** Bombeiros devem manter distância mínima da zona letal. Operações 
                   de combate só são viáveis após a bola de fogo se extinguir (duração limitada).
                
                6. **Monitoramento de Estruturas:**** Após o evento, avaliar estruturas dentro da zona de onda 
                   de choque para danos estruturais que possam causar colapso.
                
                7. **Planejamento de Resposta:** Coordenar com equipes de emergência para estabelecer rotas de 
                   fuga que evitem todas as zonas de impacto identificadas.
                
                **Aviso Importante:** Este modelo assume condições ideais. Em cenários reais, fatores como vento, 
                topografia, presença de obstáculos e múltiplas falhas simultâneas podem alterar significativamente 
                os resultados. A duração da bola de fogo é limitada, mas a onda de choque se propaga instantaneamente. 
                Sempre valide com observações de campo e considere múltiplos cenários.
                """)
