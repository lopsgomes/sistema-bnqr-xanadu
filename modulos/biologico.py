import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from streamlit_folium import st_folium
import math

# =============================================================================
# 1. BANCO DE DADOS DE AGENTES BIOLÓGICOS (CDC/USAMRIID)
# =============================================================================
AGENTES_BIO = {
    "Antraz (Bacillus anthracis)": {
        "tipo": "Bactéria (Esporo)",
        "transmissivel": False,
        "incubacao_dias": 7,
        "letalidade": 0.80,
        "R0": 0,
        "decaimento_uv": 0.1,
        "desc": "Esporos ultra-resistentes. O ataque é via nuvem de pó. Não é contagioso, mas é letal se inalado."
    },
    "Brucelose (Brucella spp.)": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 20,
        "letalidade": 0.05,
        "R0": 0,
        "decaimento_uv": 0.4,
        "desc": "Agente incapacitante. Raramente mata, mas causa febres recorrentes e fadiga extrema por meses."
    },
    "Cólera (Vibrio cholerae)": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 2,
        "letalidade": 0.50,
        "R0": 2.5,
        "decaimento_uv": 0.3,
        "desc": "Ameaça à água potável. Diarreia severa leva à morte por desidratação em horas. Contágio fecal-oral."
    },
    "Dengue (Vírus DENV)": {
        "tipo": "Vírus (Arbovírus)",
        "transmissivel": False, # Vetor Mosquito
        "incubacao_dias": 7,
        "letalidade": 0.01, # Baixa, exceto hemorrágica
        "R0": 0, # Depende do mosquito, não pessoa-pessoa direto
        "decaimento_uv": 0.9,
        "desc": "Incapacitante massivo. Colapso do sistema de saúde pelo volume de casos. Transmissão vetorial (Aedes)."
    },
    "Ebola (Zaire)": {
        "tipo": "Vírus (Filovírus)",
        "transmissivel": True,
        "incubacao_dias": 8,
        "letalidade": 0.50,
        "R0": 2.0,
        "decaimento_uv": 0.9,
        "desc": "Febre Hemorrágica. Contágio por fluidos corporais. Causa pânico social extremo e colapso sanitário."
    },
    "Enterotoxina Estafilocócica B (SEB)": {
        "tipo": "Toxina",
        "transmissivel": False,
        "incubacao_dias": 0.25,
        "letalidade": 0.01,
        "R0": 0,
        "decaimento_uv": 0.5,
        "desc": "Incapacitante rápido. Causa vômitos e febre intensa em horas. Usada para inutilizar tropas sem matar."
    },
    "Febre Amarela": {
        "tipo": "Vírus",
        "transmissivel": False, # Vetor Mosquito
        "incubacao_dias": 6,
        "letalidade": 0.15,
        "R0": 0,
        "decaimento_uv": 0.9,
        "desc": "Icterícia e falência hepática/renal. Vacina disponível, mas estoques podem acabar em surtos urbanos."
    },
    "Febre de Lassa": {
        "tipo": "Vírus (Arenavírus)",
        "transmissivel": True,
        "incubacao_dias": 10,
        "letalidade": 0.15,
        "R0": 1.2,
        "decaimento_uv": 0.8,
        "desc": "Febre hemorrágica transmitida por roedores, mas sustentável pessoa-pessoa em hospitais."
    },
    "Febre de Marburg": {
        "tipo": "Vírus (Filovírus)",
        "transmissivel": True,
        "incubacao_dias": 7,
        "letalidade": 0.88,
        "R0": 1.8,
        "decaimento_uv": 0.9,
        "desc": "Primo do Ebola, porém mais letal. Transmissão por contato direto. Sangramento múltiplo de órgãos."
    },
    "Febre Q (Coxiella burnetii)": {
        "tipo": "Bactéria (Rickettsia)",
        "transmissivel": False,
        "incubacao_dias": 15,
        "letalidade": 0.02,
        "R0": 0,
        "decaimento_uv": 0.1,
        "desc": "Extremamente infecciosa: 1 única bactéria pode causar a doença. Esporos muito resistentes no ambiente."
    },
    "Gripe Aviária H5N1": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 3,
        "letalidade": 0.60,
        "R0": 1.5,
        "decaimento_uv": 0.8,
        "desc": "Se mutar para transmissão humana eficiente, seria catastrófico. Alta mortalidade viral."
    },
    "Hantavírus (Síndrome Pulmonar)": {
        "tipo": "Vírus",
        "transmissivel": False,
        "incubacao_dias": 14,
        "letalidade": 0.35,
        "R0": 0,
        "decaimento_uv": 0.7,
        "desc": "Transmitido por aerossóis de urina de roedores. Causa falência pulmonar rápida."
    },
    "Legionella pneumophila": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 5,
        "letalidade": 0.10,
        "R0": 0,
        "decaimento_uv": 0.6,
        "desc": "Doença dos Legionários. Dispersada por ar-condicionado e torres de resfriamento contaminadas."
    },
    "Machupo (Febre Boliviana)": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 14,
        "letalidade": 0.20,
        "R0": 1.1,
        "decaimento_uv": 0.8,
        "desc": "Transmitido por roedores (vetor Calomys). Hemorragia e tremores neurológicos."
    },
    "Melioidose (Burkholderia pseudomallei)": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 9,
        "letalidade": 0.40,
        "R0": 0,
        "decaimento_uv": 0.2,
        "desc": "O 'Imitador'. Pode ficar latente por anos e surgir como pneumonia fulminante. Resistente a antibióticos."
    },
    "Mormo (Burkholderia mallei)": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 10,
        "letalidade": 0.95,
        "R0": 0,
        "decaimento_uv": 0.3,
        "desc": "Doença de cavalos. Aerossol letal para humanos. Abscessos pulmonares múltiplos."
    },
    "Nipah Vírus": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 10,
        "letalidade": 0.75,
        "R0": 0.5,
        "decaimento_uv": 0.9,
        "desc": "Transmitido por morcegos/porcos. Causa encefalite severa e coma. Altíssima letalidade."
    },
    "Peste Pneumônica (Yersinia pestis)": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 2,
        "letalidade": 1.00,
        "R0": 1.5,
        "decaimento_uv": 0.5,
        "desc": "A Peste Negra pulmonar. Mata em 48h sem antibiótico. Transmissão por tosse."
    },
    "Ricina (Ricinus communis)": {
        "tipo": "Toxina",
        "transmissivel": False,
        "incubacao_dias": 0.5,
        "letalidade": 1.00,
        "R0": 0,
        "decaimento_uv": 0.2,
        "desc": "Extraída da mamona. Não contagiosa. Mata por falência celular. Sem antídoto."
    },
    "Salmonella Typhi (Tifo)": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 10,
        "letalidade": 0.15,
        "R0": 2.8,
        "decaimento_uv": 0.4,
        "desc": "Febre Tifoide. Risco de contaminação intencional de reservatórios de água e alimentos."
    },
    "Saxitoxina": {
        "tipo": "Toxina",
        "transmissivel": False,
        "incubacao_dias": 0.05,
        "letalidade": 0.15,
        "R0": 0,
        "decaimento_uv": 0.1,
        "desc": "Neurotoxina marinha. 1000x mais potente que cianeto. Parada respiratória imediata."
    },
    "Toxina Botulínica (Botox)": {
        "tipo": "Toxina",
        "transmissivel": False,
        "incubacao_dias": 1,
        "letalidade": 0.60,
        "R0": 0,
        "decaimento_uv": 0.8,
        "desc": "A substância mais tóxica conhecida. Paralisia flácida e parada respiratória. Não contagiosa."
    },
    "Tularemia (Francisella tularensis)": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 3,
        "letalidade": 0.30,
        "R0": 0,
        "decaimento_uv": 0.3,
        "desc": "Febre do Coelho. Requer apenas 10 bactérias para infectar. Pneumonia severa."
    },
    "Varíola (Smallpox)": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 12,
        "letalidade": 0.30,
        "R0": 5.0,
        "decaimento_uv": 0.9,
        "desc": "Erradicada, mas estocada como arma. Altamente contagiosa. O cenário de pesadelo biológico."
    },
    "Vírus Zika": {
        "tipo": "Vírus (Arbovírus)",
        "transmissivel": True, # Sexual/Vetor
        "incubacao_dias": 7,
        "letalidade": 0.001,
        "R0": 3.0, # Em surtos com vetor ativo
        "decaimento_uv": 0.8,
        "desc": "Baixa letalidade aguda, mas causa microcefalia em fetos e Guillain-Barré. Impacto social a longo prazo."
    }
}

# =============================================================================
# 2. MOTORES DE CÁLCULO
# =============================================================================

# --- MOTOR 1: MODELO SIR (Susceptible-Infectious-Recovered) para Epidemias ---
def simular_epidemia_sir(populacao_total, infectados_iniciais, R0, periodo_infeccioso_dias):
    """
    Simula a curva de contágio ao longo do tempo.
    Beta: Taxa de transmissão
    Gamma: Taxa de recuperação (1 / dias doente)
    """
    if R0 == 0: return None # Agente não contagioso

    # Parâmetros
    dias = 100
    dt = 1 # Passo de 1 dia
    gamma = 1.0 / periodo_infeccioso_dias
    beta = R0 * gamma
    
    # Arrays de estado
    S = [populacao_total - infectados_iniciais] # Suscetíveis
    I = [infectados_iniciais]                   # Infectados (Doentes)
    R = [0]                                     # Recuperados (ou Mortos)
    T = [0]

    # Loop de Euler
    for t in range(1, dias):
        s_prev = S[-1]
        i_prev = I[-1]
        r_prev = R[-1]
        
        # Equações Diferenciais SIR
        novos_infectados = (beta * s_prev * i_prev) / populacao_total
        novos_recuperados = gamma * i_prev
        
        s_next = s_prev - novos_infectados
        i_next = i_prev + novos_infectados - novos_recuperados
        r_next = r_prev + novos_recuperados
        
        S.append(s_next)
        I.append(i_next)
        R.append(r_next)
        T.append(t)
        
        if i_next < 0.5: break # Epidemia acabou

    df = pd.DataFrame({
        'Dias': T,
        'Suscetíveis': S,
        'Infectados (Ativos)': I,
        'Recuperados/Mortos': R
    })
    return df

# --- MOTOR 2: PLUMA GAUSSIANA BIOLÓGICA (Dispersão de Aerossol) ---
def calcular_pluma_bio(massa_kg, vento_ms, decaimento_uv):
    """
    Similar ao químico, mas com fator de decaimento biológico (luz solar mata bactérias).
    Retorna alcance em metros.
    """
    # Conversão grosseira de massa para "Doses Infectivas" (simplificação tática)
    # Assumindo dispersão eficiente (weaponized)
    potencia_fonte = massa_kg * 1e9 # Fator arbitrário de escala para visualização
    
    # Fator de sobrevivência do agente ao sol/ar
    fator_sobrevivencia = 1.0 - decaimento_uv
    
    # Velocidade do vento (diluição)
    u = max(vento_ms, 0.5)
    
    # Alcance aproximado (Zona de Risco)
    # Quanto mais vento, mais longe vai, mas mais diluído fica.
    # No biológico, vento fraco é pior (concentração alta).
    alcance = math.sqrt(potencia_fonte / u) * fator_sobrevivencia * 0.5
    
    # Travas
    alcance = min(alcance, 10000) # Max 10km
    alcance = max(alcance, 100)
    
    return alcance

def gerar_cone_bio(lat, lon, distancia, direcao_vento):
    # Cone mais estreito e longo (aerossol invisível)
    largura_graus = 20 
    azimute = (direcao_vento + 180) % 360
    coords = [[lat, lon]]
    r_terra = 6378137
    steps = 8
    
    for i in range(steps + 1):
        delta = -largura_graus/2 + (i * largura_graus/steps)
        theta = math.radians(90 - (azimute + delta))
        dx = distancia * math.cos(theta)
        dy = distancia * math.sin(theta)
        dlat = (dy/r_terra)*(180/math.pi)
        dlon = (dx/r_terra)*(180/math.pi)/math.cos(math.radians(lat))
        coords.append([lat+dlat, lon+dlon])
        
    coords.append([lat, lon])
    return coords

# =============================================================================
# 3. INTERFACE VISUAL (CORRIGIDA COM SESSION STATE)
# =============================================================================
def renderizar():
    st.markdown("### ☣️ Biológico (Epidemia & Dispersão)")
    st.markdown("Análise de cenários de defesa biológica: Contágio vs. Ataque Direto.")
    st.markdown("---")

    # Seleção do Agente (Global)
    agente_nome = st.selectbox("Selecione o Agente Biológico", list(AGENTES_BIO.keys()))
    dados = AGENTES_BIO[agente_nome]
    
    # Info Card do Agente
    with st.expander(f"📖 Ficha Técnica: {agente_nome}", expanded=True):
        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("Tipo", dados['tipo'])
        col_i2.metric("Incubação", f"{dados['incubacao_dias']} dias", help="Tempo entre contato e sintomas.")
        col_i3.metric("Letalidade Estimada", f"{dados['letalidade']*100:.0f}%", help="Sem tratamento adequado.")
        
        st.markdown(f"**Descrição:** {dados['desc']}")
        if dados['transmissivel']:
            st.error(f"⚠️ **CONTAGIOSO:** R0 = {dados['R0']} (Cada doente infecta {dados['R0']} pessoas).")
        else:
            st.success("✅ **NÃO CONTAGIOSO:** Risco restrito à área de liberação.")

    # --- SISTEMA DE ABAS (TABS) ---
    tab1, tab2 = st.tabs(["🗺️ Nuvem de Esporos (Ataque)", "📈 Curva Epidemiológica (Surto)"])

    # --- ABA 1: ATAQUE COM AEROSSOL ---
    with tab1:
        st.subheader("Simulação de Dispersão (Bio-Terrorismo)")
        st.caption("Cenário: Um drone ou spray libera o agente no ar.")
        
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", value=-22.8625, format="%.5f")
            lon = st.number_input("Lon", value=-43.2245, format="%.5f")
        with c2:
            massa = st.number_input("Quantidade Liberada (kg)", value=0.5, step=0.1, help="Pó ou Líquido nebulizado.")
            vento = st.number_input("Vento (m/s)", value=2.0, min_value=0.5)
            direcao = st.number_input("Direção Vento (Graus)", value=90)

        # Inicializa estado se não existir
        if 'bio_map_calc' not in st.session_state: st.session_state['bio_map_calc'] = False

        # Botão apenas ativa o estado
        if st.button("🌫️ Projetar Zona de Risco Biológico"):
            st.session_state['bio_map_calc'] = True

        # Renderização persistente
        if st.session_state['bio_map_calc']:
            alcance = calcular_pluma_bio(massa, vento, dados['decaimento_uv'])
            
            st.warning(f"🚨 **Zona de Infecção:** O agente pode atingir até **{alcance:.0f} metros** a favor do vento.")
            if dados['decaimento_uv'] > 0.5:
                st.info("💡 Este agente morre rápido na luz solar (UV). Ataques noturnos são mais letais.")
            else:
                st.error("💀 Este agente é resistente ao ambiente (Esporos). A área ficará contaminada por anos.")

            # Mapa
            m = folium.Map([lat, lon], zoom_start=15)
            folium.Marker([lat, lon], icon=folium.Icon(color="green", icon="biohazard", prefix="fa"), tooltip="Ponto de Liberação").add_to(m)
            
            poly = gerar_cone_bio(lat, lon, alcance, direcao)
            folium.Polygon(poly, color="red", fill=True, fill_opacity=0.4, tooltip="Zona de Risco Biológico").add_to(m)
            
            st_folium(m, width=None, height=500)

    # --- ABA 2: SURTO EPIDÊMICO ---
    with tab2:
        st.subheader("Simulação de Surto (Hospitais)")
        
        if not dados['transmissivel']:
            st.warning("⛔ Este agente (como Antraz ou Botulismo) **NÃO** causa epidemia contágiosa. O gráfico SIR não se aplica.")
        else:
            c_sir1, c_sir2 = st.columns(2)
            with c_sir1:
                populacao = st.number_input("População da Cidade", value=10000, step=1000)
                inicial = st.number_input("Infectados Iniciais", value=5)
            with c_sir2:
                # Permite ao usuário "brincar" com o R0 para ver o efeito do isolamento
                r0_ajuste = st.slider(f"Taxa de Contágio (R0) - Padrão: {dados['R0']}", 0.5, 10.0, float(dados['R0']), help="Se aplicarmos Quarentena, o R0 diminui.")
            
            # Inicializa estado se não existir
            if 'bio_sir_calc' not in st.session_state: st.session_state['bio_sir_calc'] = False

            if st.button("📈 Projetar Colapso Hospitalar"):
                st.session_state['bio_sir_calc'] = True

            # Renderização persistente
            if st.session_state['bio_sir_calc']:
                # Tempo infeccioso estimado (duração da doença aguda)
                dias_doente = 14 
                df_sir = simular_epidemia_sir(populacao, inicial, r0_ajuste, dias_doente)
                
                if df_sir is not None:
                    # Encontrar o Pico
                    pico = df_sir['Infectados (Ativos)'].max()
                    dia_pico = df_sir.loc[df_sir['Infectados (Ativos)'] == pico, 'Dias'].values[0]
                    
                    c_res1, c_res2 = st.columns(2)
                    c_res1.metric("Pico de Infectados", f"{int(pico)} pessoas", f"Dia {dia_pico}")
                    c_res2.metric("Capacidade Hospitalar", "Estimada 5%", help="Geralmente 5% da população precisa de leito.")

                    # Alerta de Colapso
                    leitos = populacao * 0.05
                    if pico > leitos:
                        st.error(f"🚨 **COLAPSO DO SISTEMA:** O pico ({int(pico)}) excede o número estimado de leitos ({int(leitos)}).")
                    else:
                        st.success("✅ Sistema suporta o surto (Achatamento da Curva).")

                    # Gráfico Altair
                    df_melt = df_sir.melt('Dias', var_name='Categoria', value_name='Pessoas')
                    
                    chart = alt.Chart(df_melt).mark_line(strokeWidth=3).encode(
                        x='Dias',
                        y='Pessoas',
                        color=alt.Color('Categoria', scale=alt.Scale(domain=['Suscetíveis', 'Infectados (Ativos)', 'Recuperados/Mortos'], range=['blue', 'red', 'green'])),
                        tooltip=['Dias', 'Categoria', 'Pessoas']
                    ).properties(title=f"Curva SIR: {agente_nome}").interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
