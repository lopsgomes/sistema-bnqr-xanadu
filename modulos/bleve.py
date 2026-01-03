import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np

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
    }
}

# Limites de Dano (Térmico e Sobrepressão)
# Fonte: CCPS / TNO
LIMITES_BLEVE = {
    "Bola de Fogo (Raio Máximo)": {
        "tipo": "Fogo",
        "cor": "#8B0000", # Vermelho Escuro
        "desc": "Onde a bola de fogo toca fisicamente. Incineração total."
    },
    "Radiação Térmica Fatal (12.5 kW/m²)": {
        "tipo": "Térmico",
        "cor": "#FF4500", # Laranja avermelhado
        "desc": "Morte em segundos. Ignição espontânea de madeira."
    },
    "Queimaduras de 2º Grau (5.0 kW/m²)": {
        "tipo": "Térmico",
        "cor": "#FFA500", # Laranja
        "desc": "Pele queima em 45 segundos. Dor insuportável."
    },
    "Dano Estrutural Leve (0.03 bar / 3 psi)": {
        "tipo": "Explosão",
        "cor": "#000000", # Preto/Cinza
        "desc": "Onda de choque (Blast). Quebra vidros num raio grande e derruba estruturas leves."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (CCPS / TNO YELLOW BOOK)
# =============================================================================
def calcular_bleve(massa_kg, substancia):
    """
    Calcula os efeitos físicos do BLEVE.
    """
    # 1. Diâmetro da Bola de Fogo (Fireball)
    # Correlação CCPS: D = 5.8 * M^(1/3)
    diametro_fogo = 5.8 * (massa_kg ** (1/3))
    raio_fogo = diametro_fogo / 2
    
    # 2. Duração da Bola de Fogo (segundos)
    # T = 0.45 * M^(1/3) para M < 30.000 kg
    tempo_fogo = 0.45 * (massa_kg ** (1/3))
    
    # 3. Radiação Térmica (Point Source Model simplificado para BLEVE)
    # A emissividade de um BLEVE é altíssima (~350 kW/m2 na superfície)
    # SEP (Surface Emissive Power) médio ≈ 270 kW/m2
    SEP = 270.0 
    
    # Fração de calor radiado (Transmissividade atmosférica assumida 0.7 média)
    tau = 0.7 
    
    raios_impacto = {}
    raios_impacto["Bola de Fogo (Raio Máximo)"] = raio_fogo

    # Cálculo reverso para distâncias térmicas:
    # I = tau * SEP * ViewFactor
    # Simplificação geométrica para campo distante: I = (tau * Q_total) / (4 * pi * r^2)
    # Mas para BLEVE, usamos correlação direta do raio da bola:
    # r = D * sqrt((tau * SEP) / I_alvo) / 2
    
    for nome, dados in LIMITES_BLEVE.items():
        if dados['tipo'] == "Térmico":
            limite_kw = 12.5 if "Fatal" in nome else 5.0
            
            # Fórmula prática CCPS
            try:
                r = (diametro_fogo / 2) * math.sqrt((tau * SEP) / limite_kw)
                raios_impacto[nome] = r
            except:
                raios_impacto[nome] = 0

    # 4. Onda de Choque (Blast) - Equivalência TNT
    # Energia = Massa * Hc * Fator_Eficiencia
    # 1 kg TNT ≈ 4680 kJ
    energia_total_kj = massa_kg * substancia['Hc'] * substancia['fator_tnt']
    kg_tnt = energia_total_kj / 4680.0
    
    # Estimativa de raio de dano (Sobrepressão 0.03 bar - quebra vidros/danos leves)
    # Hopkinson-Cranz Scaling Law simplificada: Z = R / (W^(1/3))
    # Para 0.03 bar (aprox 0.5 psi), Z é aprox 20 a 30. Usaremos 25 (conservador).
    raio_blast = 25 * (kg_tnt ** (1/3))
    
    raios_impacto["Dano Estrutural Leve (0.03 bar / 3 psi)"] = raio_blast

    return raios_impacto, diametro_fogo, tempo_fogo, kg_tnt

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 💥 BLEVE (Explosão de Vapor em Expansão)")
    st.markdown("Modelagem de ruptura catastrófica de tanques pressurizados (Bolas de Fogo).")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O que é um BLEVE? (Leia antes)", expanded=True):
        st.markdown("""
        **O Fenômeno:** Imagine uma panela de pressão industrial que falha.
        O líquido lá dentro está muito quente, mas líquido por causa da pressão. Quando o tanque rasga, a pressão some e o líquido vira vapor INSTANTANEAMENTE.
        
        **O Resultado (Combo Duplo):**
        1.  🔥 **Bola de Fogo (Fireball):** O vapor expandido encontra uma faísca e cria um "cogumelo" de fogo gigante que sobe aos céus. O calor cozinha tudo ao redor.
        2.  💨 **Onda de Choque (Blast):** A expansão física empurra o ar com violência, quebrando vidros e derrubando paredes, igual a uma bomba.
        
        **Cenário Típico:** Acidente rodoviário onde fogo externo aquece o tanque até ele não aguentar mais.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Local e Substância")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        subs_nome = st.selectbox("Carga do Tanque", list(SUBSTANCIAS_BLEVE.keys()))
        dados_subs = SUBSTANCIAS_BLEVE[subs_nome]
        st.caption(f"ℹ️ {dados_subs['desc']}")

    with col2:
        st.subheader("⚙️ Configuração do Tanque")
        cap_total = st.number_input("Capacidade Total do Tanque (kg)", value=15000.0, step=1000.0, help="Carreta rodoviária comum ~20 a 30 toneladas.")
        percent = st.slider("Nível de Enchimento (%)", 10, 100, 70, help="Tanques cheios (70-80%) geram BLEVEs piores que tanques vazios.")
        
        massa_real = cap_total * (percent / 100.0)
        st.info(f"💣 Massa Envolvida: **{massa_real/1000:.1f} toneladas**")

    # Botão de Ação
    if 'bleve_calc' not in st.session_state: st.session_state['bleve_calc'] = False
    
    if st.button("💥 Simular Explosão", type="primary", use_container_width=True):
        st.session_state['bleve_calc'] = True

    if st.session_state['bleve_calc']:
        # Calcular
        raios, diametro, duracao, tnt_eq = calcular_bleve(massa_real, dados_subs)
        
        st.markdown("#### 📊 Relatório do Desastre")
        
        # Métricas Chocantes
        k1, k2, k3 = st.columns(3)
        k1.metric("Diâmetro da Bola de Fogo", f"{diametro:.1f} m", "Altura de um prédio", delta_color="inverse")
        k2.metric("Duração do Fogo", f"{duracao:.1f} s", "Tempo de queima")
        k3.metric("Equivalência TNT", f"{tnt_eq/1000:.1f} Ton", "Dinamite", delta_color="inverse")
        
        st.write("---")
        
        # Resultados de Segurança
        c1, c2, c3 = st.columns(3)
        c1.metric("Raio Letal (Térmico)", f"{raios['Radiação Térmica Fatal (12.5 kW/m²)']:.0f} m", "Morte")
        c2.metric("Queimaduras Graves", f"{raios['Queimaduras de 2º Grau (5.0 kW/m²)']:.0f} m", "Feridos")
        c3.metric("Dano Estrutural (Vidros)", f"{raios['Dano Estrutural Leve (0.03 bar / 3 psi)']:.0f} m", "Blast Wave")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
        
        # Marcador do Epicentro
        folium.Marker(
            [lat, lon], 
            tooltip=f"BLEVE: {subs_nome}",
            icon=folium.Icon(color="black", icon="bomb", prefix="fa")
        ).add_to(m)
        
        # Desenhar Círculos (Prioridade Visual: Blast > Térmico Leve > Térmico Fatal > Bola Fogo)
        # Vamos ordenar pelo raio para o maior ficar por baixo
        lista_ordenada = sorted(raios.items(), key=lambda x: x[1], reverse=True)
        
        for nome, raio in lista_ordenada:
            cor = LIMITES_BLEVE[nome]['cor']
            desc = LIMITES_BLEVE[nome]['desc']
            
            # Círculo de Blast geralmente é uma linha preta fina para diferenciar do calor
            if "Dano Estrutural" in nome:
                folium.Circle(
                    [lat, lon], radius=raio, color="black", weight=2, fill=False,
                    tooltip=f"Onda de Choque: {raio:.0f}m ({desc})"
                ).add_to(m)
            else:
                folium.Circle(
                    [lat, lon], radius=raio, color=cor, fill=True, fill_opacity=0.4,
                    tooltip=f"{nome}: {raio:.0f}m"
                ).add_to(m)
        
        st_folium(m, width=None, height=600)
