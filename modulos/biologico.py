import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from streamlit_folium import st_folium
import math

# =============================================================================
# 1. BANCO DE DADOS DE AGENTES BIOLÓGICOS
# =============================================================================
# Agentes biológicos de interesse para defesa e saúde pública
# Fonte: CDC Select Agents List, WHO Risk Group Classification, USAMRIID
# R0 = Número Reprodutivo Básico (quantas pessoas um infectado contamina em média)
# decaimento_uv = Fator de inativação por luz UV (0.0 = resistente, 1.0 = muito sensível)
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
    },
    "Bacillus cereus": {
        "tipo": "Bactéria (Esporo)",
        "transmissivel": False,
        "incubacao_dias": 0.5,
        "letalidade": 0.001,
        "R0": 0,
        "decaimento_uv": 0.2,
        "desc": "Esporos resistentes. Causa intoxicação alimentar rápida. Pode ser usado como simulação de antraz."
    },
    "Clostridium botulinum (Esporos)": {
        "tipo": "Bactéria (Esporo)",
        "transmissivel": False,
        "incubacao_dias": 1,
        "letalidade": 0.60,
        "R0": 0,
        "decaimento_uv": 0.1,
        "desc": "Esporos extremamente resistentes. Produz toxina botulínica. Pode persistir no ambiente por décadas."
    },
    "Coxsackievírus": {
        "tipo": "Vírus (Enterovírus)",
        "transmissivel": True,
        "incubacao_dias": 3,
        "letalidade": 0.001,
        "R0": 2.5,
        "decaimento_uv": 0.7,
        "desc": "Causa doença mão-pé-boca. Altamente contagioso. Pode causar meningite e miocardite em casos graves."
    },
    "Crimeia-Congo (CCHF)": {
        "tipo": "Vírus (Nairovírus)",
        "transmissivel": True,
        "incubacao_dias": 3,
        "letalidade": 0.30,
        "R0": 1.2,
        "decaimento_uv": 0.8,
        "desc": "Febre hemorrágica transmitida por carrapatos. Transmissão pessoa-pessoa em contato próximo. Alta letalidade."
    },
    "Cryptosporidium parvum": {
        "tipo": "Protozoário (Oocisto)",
        "transmissivel": True,
        "incubacao_dias": 7,
        "letalidade": 0.01,
        "R0": 1.5,
        "decaimento_uv": 0.3,
        "desc": "Parasita resistente ao cloro. Contaminação de água potável. Diarreia severa e prolongada."
    },
    "E. coli O157:H7": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 3,
        "letalidade": 0.05,
        "R0": 1.2,
        "decaimento_uv": 0.5,
        "desc": "Contaminação de alimentos e água. Causa síndrome hemolítico-urêmica. Risco de contaminação intencional."
    },
    "Giardia lamblia": {
        "tipo": "Protozoário (Cisto)",
        "transmissivel": True,
        "incubacao_dias": 7,
        "letalidade": 0.001,
        "R0": 1.8,
        "decaimento_uv": 0.4,
        "desc": "Parasita intestinal. Contaminação de água. Cistos resistentes ao cloro. Diarreia crônica."
    },
    "Hantavírus (Febre Hemorrágica)": {
        "tipo": "Vírus",
        "transmissivel": False,
        "incubacao_dias": 14,
        "letalidade": 0.15,
        "R0": 0,
        "decaimento_uv": 0.7,
        "desc": "Transmitido por aerossóis de urina de roedores. Febre hemorrágica com síndrome renal."
    },
    "Hepatite A (HAV)": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 28,
        "letalidade": 0.001,
        "R0": 2.0,
        "decaimento_uv": 0.6,
        "desc": "Contaminação fecal-oral. Risco de contaminação intencional de água e alimentos. Vacina disponível."
    },
    "Influenza A (H1N1)": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 2,
        "letalidade": 0.01,
        "R0": 1.8,
        "decaimento_uv": 0.8,
        "desc": "Gripe pandêmica. Alta transmissibilidade. Pode causar colapso do sistema de saúde pelo volume de casos."
    },
    "MERS-CoV": {
        "tipo": "Vírus (Coronavírus)",
        "transmissivel": True,
        "incubacao_dias": 5,
        "letalidade": 0.35,
        "R0": 0.7,
        "decaimento_uv": 0.7,
        "desc": "Síndrome Respiratória do Oriente Médio. Alta letalidade. Transmissão limitada pessoa-pessoa."
    },
    "Norovírus": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 1,
        "letalidade": 0.001,
        "R0": 4.0,
        "decaimento_uv": 0.6,
        "desc": "Altamente contagioso. Causa gastroenterite severa. Resistente a desinfetantes. Contaminação de alimentos."
    },
    "Peste Bubônica (Yersinia pestis)": {
        "tipo": "Bactéria",
        "transmissivel": False,
        "incubacao_dias": 3,
        "letalidade": 0.60,
        "R0": 0,
        "decaimento_uv": 0.5,
        "desc": "Transmitida por pulgas de roedores. Forma bubônica não é contagiosa pessoa-pessoa. Alta letalidade sem tratamento."
    },
    "Rotavírus": {
        "tipo": "Vírus",
        "transmissivel": True,
        "incubacao_dias": 2,
        "letalidade": 0.001,
        "R0": 3.5,
        "decaimento_uv": 0.7,
        "desc": "Causa gastroenterite severa em crianças. Altamente contagioso. Resistente a desinfetantes comuns."
    },
    "Shigella dysenteriae": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 2,
        "letalidade": 0.10,
        "R0": 2.5,
        "decaimento_uv": 0.5,
        "desc": "Disenteria bacilar. Contaminação fecal-oral. Requer poucas bactérias para infectar. Risco de contaminação de água."
    },
    "Vírus da Raiva": {
        "tipo": "Vírus",
        "transmissivel": False,
        "incubacao_dias": 30,
        "letalidade": 1.00,
        "R0": 0,
        "decaimento_uv": 0.9,
        "desc": "Transmitido por mordida de animal. Letalidade de 100% após sintomas. Vacina pós-exposição disponível."
    },
    "Vírus do Nilo Ocidental": {
        "tipo": "Vírus (Arbovírus)",
        "transmissivel": False,
        "incubacao_dias": 5,
        "letalidade": 0.10,
        "R0": 0,
        "decaimento_uv": 0.8,
        "desc": "Transmitido por mosquitos. Causa encefalite. Não é contagioso pessoa-pessoa, mas pode causar surtos vetoriais."
    },
    "Yersinia enterocolitica": {
        "tipo": "Bactéria",
        "transmissivel": True,
        "incubacao_dias": 3,
        "letalidade": 0.001,
        "R0": 1.5,
        "decaimento_uv": 0.4,
        "desc": "Contaminação de alimentos. Causa gastroenterite. Pode causar artrite reativa. Risco de contaminação intencional."
    }
}

# =============================================================================
# 2. MOTORES DE CÁLCULO
# =============================================================================

# --- MOTOR 1: MODELO SIR (Susceptible-Infectious-Recovered) para Epidemias ---
# Baseado em: Kermack-McKendrick Model (1927), Epidemiologia Matemática
# O modelo SIR divide a população em três compartimentos:
# - S (Susceptible): Pessoas suscetíveis à infecção
# - I (Infectious): Pessoas infectadas e capazes de transmitir
# - R (Recovered): Pessoas recuperadas (ou mortas) - não podem mais ser infectadas
def simular_epidemia_sir(populacao_total, infectados_iniciais, R0, periodo_infeccioso_dias):
    """
    Simula a evolução temporal de uma epidemia usando o modelo SIR.
    
    O modelo assume:
    - População fechada (sem nascimentos/mortes não relacionadas à doença)
    - Mistura homogênea (todos têm a mesma probabilidade de contato)
    - Recuperação confere imunidade permanente
    
    Parâmetros:
    - populacao_total: Tamanho total da população
    - infectados_iniciais: Número inicial de infectados
    - R0: Número reprodutivo básico (quantas pessoas um infectado contamina em média)
    - periodo_infeccioso_dias: Duração média do período infeccioso (dias)
    
    Retorna:
    - DataFrame com evolução temporal de S, I, R ao longo dos dias
    """
    if R0 == 0: 
        return None  # Agente não contagioso - modelo SIR não se aplica

    # Parâmetros do modelo
    dias = 200  # Período de simulação estendido
    dt = 1  # Passo de 1 dia
    
    # Taxa de recuperação (γ): inverso do período infeccioso
    gamma = 1.0 / periodo_infeccioso_dias
    
    # Taxa de transmissão (β): relacionada ao R0
    # R0 = β / γ  =>  β = R0 × γ
    beta = R0 * gamma
    
    # Arrays de estado inicial
    S = [populacao_total - infectados_iniciais]  # Suscetíveis
    I = [infectados_iniciais]                    # Infectados (Doentes)
    R = [0]                                      # Recuperados (ou Mortos)
    T = [0]

    # Integração numérica (Método de Euler)
    for t in range(1, dias):
        s_prev = S[-1]
        i_prev = I[-1]
        r_prev = R[-1]
        
        # Equações Diferenciais SIR:
        # dS/dt = -β × S × I / N
        # dI/dt = β × S × I / N - γ × I
        # dR/dt = γ × I
        
        novos_infectados = (beta * s_prev * i_prev) / populacao_total
        novos_recuperados = gamma * i_prev
        
        s_next = s_prev - novos_infectados
        i_next = i_prev + novos_infectados - novos_recuperados
        r_next = r_prev + novos_recuperados
        
        # Validação: valores não podem ser negativos
        s_next = max(0, s_next)
        i_next = max(0, i_next)
        r_next = max(0, r_next)
        
        S.append(s_next)
        I.append(i_next)
        R.append(r_next)
        T.append(t)
        
        # Critério de parada: epidemia acabou (menos de 0.5 infectados)
        if i_next < 0.5: 
            break

    # Criar DataFrame com resultados
    df = pd.DataFrame({
        'Dias': T,
        'Suscetíveis': S,
        'Infectados (Ativos)': I,
        'Recuperados/Mortos': R,
        'Total Infectados (Acumulado)': [i + r for i, r in zip(I, R)]
    })
    return df

# --- MOTOR 2: PLUMA GAUSSIANA BIOLÓGICA (Dispersão de Aerossol) ---
# Baseado em: Gaussian Plume Model adaptado para agentes biológicos
# Considera decaimento por luz UV e fatores ambientais
def calcular_pluma_bio(massa_kg, vento_ms, decaimento_uv):
    """
    Calcula o alcance de dispersão de aerossol biológico.
    
    Diferente de agentes químicos, agentes biológicos:
    - Decaem por exposição à luz UV (radiação solar)
    - Podem ser inativados por fatores ambientais (temperatura, umidade)
    - Têm tempo de sobrevivência limitado no ambiente
    
    Parâmetros:
    - massa_kg: Massa de agente biológico liberado (kg)
    - vento_ms: Velocidade do vento (m/s)
    - decaimento_uv: Fator de inativação por UV (0.0 = resistente, 1.0 = muito sensível)
    
    Retorna:
    - alcance: Alcance estimado da zona de risco em metros
    """
    # Conversão de massa para "potência" da fonte
    # Assumindo dispersão eficiente (aerossolização adequada)
    potencia_fonte = massa_kg * 1e9  # Fator de escala para visualização
    
    # Fator de sobrevivência do agente ao ambiente
    # Agentes com decaimento_uv alto morrem rápido na luz solar
    # Agentes com decaimento_uv baixo são mais resistentes
    fator_sobrevivencia = 1.0 - decaimento_uv
    
    # Velocidade do vento (diluição)
    # Mínimo de 0.5 m/s para evitar divisão por zero
    u = max(vento_ms, 0.5)
    
    # Alcance aproximado (Zona de Risco)
    # Quanto mais vento, mais longe vai, mas mais diluído fica
    # No biológico, vento fraco é pior (concentração alta, menos diluição)
    # O fator de sobrevivência reduz o alcance efetivo
    alcance = math.sqrt(potencia_fonte / u) * fator_sobrevivencia * 0.5
    
    # Limites físicos do modelo
    alcance = min(alcance, 10000)  # Máximo: 10 km
    alcance = max(alcance, 100)    # Mínimo: 100 m
    
    return alcance

def gerar_cone_bio(lat, lon, distancia, direcao_vento):
    """
    Gera polígono geográfico representando a zona de dispersão biológica.
    
    A zona é representada como um cone estreito (aerossol invisível) que se estende
    na direção do vento a partir do ponto de liberação.
    
    Parâmetros:
    - lat: Latitude do ponto de liberação (graus decimais)
    - lon: Longitude do ponto de liberação (graus decimais)
    - distancia: Distância do alcance em metros
    - direcao_vento: Direção de onde vem o vento (graus, 0° = Norte)
    
    Retorna:
    - coords: Lista de coordenadas [lat, lon] para desenhar o polígono
    """
    # Cone mais estreito e longo (aerossol invisível)
    largura_graus = 20  # Abertura do cone em graus
    azimute = (direcao_vento + 180) % 360  # Direção oposta ao vento
    coords = [[lat, lon]]  # Ponto de origem
    r_terra = 6378137  # Raio da Terra em metros (WGS84)
    steps = 8  # Número de pontos para criar o arco
    
    for i in range(steps + 1):
        delta = -largura_graus/2 + (i * largura_graus/steps)
        theta = math.radians(90 - (azimute + delta))
        dx = distancia * math.cos(theta)
        dy = distancia * math.sin(theta)
        dlat = (dy/r_terra)*(180/math.pi)
        dlon = (dx/r_terra)*(180/math.pi)/math.cos(math.radians(lat))
        coords.append([lat+dlat, lon+dlon])
        
    coords.append([lat, lon])  # Fechar polígono
    return coords

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Simulador Epidemiológico e Dispersão Biológica")
    st.markdown("**Análise de cenários de defesa biológica: dispersão de aerossol e modelagem epidemiológica**")
    st.markdown("---")

    # Seleção do Agente (Global)
    agente_nome = st.selectbox("Selecione o Agente Biológico", list(AGENTES_BIO.keys()),
                               help="Escolha o agente biológico para análise. Consulte classificações CDC/WHO para identificação.")
    dados = AGENTES_BIO[agente_nome]
    
    # Info Card do Agente
    with st.expander(f"Ficha Técnica: {agente_nome}", expanded=True):
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        col_i1.metric("Tipo", dados['tipo'],
                     help="Classificação do agente (bactéria, vírus, toxina, protozoário)")
        col_i2.metric("Período de Incubação", f"{dados['incubacao_dias']:.1f} dias", 
                     help="Tempo médio entre exposição e aparecimento de sintomas")
        col_i3.metric("Letalidade Estimada", f"{dados['letalidade']*100:.0f}%", 
                     help="Taxa de letalidade sem tratamento adequado")
        col_i4.metric("Resistência UV", f"{(1-dados['decaimento_uv'])*100:.0f}%",
                     help="Fator de sobrevivência à radiação UV (0% = muito sensível, 100% = muito resistente)")
        
        st.markdown(f"**Descrição:** {dados['desc']}")
        
        st.markdown("---")
        
        if dados['transmissivel']:
            st.error(f"**CONTAGIOSO:** R0 = {dados['R0']:.2f} - Cada pessoa infectada contamina em média {dados['R0']:.2f} outras pessoas. "
                    f"Risco de propagação epidêmica.")
        else:
            st.success(f"**NÃO CONTAGIOSO:** R0 = 0 - Risco restrito à área de liberação direta. Não há transmissão pessoa-pessoa.")

    # --- SISTEMA DE ABAS (TABS) ---
    tab1, tab2 = st.tabs(["Dispersão de Aerossol (Ataque Direto)", "Modelagem Epidemiológica (Surto)"])

    # --- ABA 1: ATAQUE COM AEROSSOL ---
    with tab1:
        st.subheader("Simulação de Dispersão de Aerossol Biológico")
        st.caption("Cenário: Liberação intencional ou acidental de agente biológico na atmosfera (drone, spray, dispositivo).")
        
        with st.expander("Fundamentos da Dispersão Biológica", expanded=False):
            st.markdown("""
            #### Características da Dispersão Biológica
            
            Diferente de agentes químicos, agentes biológicos apresentam características únicas:
            
            **1. Decaimento Ambiental:**
            - **Luz UV:** A radiação solar inativa muitos agentes biológicos (especialmente vírus e bactérias não esporuladas)
            - **Temperatura:** Temperaturas extremas podem inativar agentes
            - **Umidade:** Alguns agentes sobrevivem melhor em condições específicas de umidade
            
            **2. Formas de Resistência:**
            - **Esporos:** Formas de resistência extremamente duráveis (antraz, botulismo). Podem persistir por décadas.
            - **Cistos/Oocistos:** Formas de resistência de protozoários. Resistentes a desinfetantes.
            - **Vírus:** Geralmente mais sensíveis ao ambiente, exceto em condições ideais.
            
            **3. Fatores que Influenciam o Alcance:**
            - **Massa liberada:** Quanto maior, maior o alcance potencial
            - **Velocidade do vento:** Ventos fortes dispersam mais, mas diluem mais rápido
            - **Resistência UV:** Agentes resistentes viajam mais longe
            - **Hora do dia:** Ataques noturnos são mais eficazes para agentes sensíveis a UV
            
            **4. Limitações do Modelo:**
            - Assume dispersão gaussiana simplificada
            - Não considera topografia complexa
            - Não modela decaimento temporal detalhado
            - Assume condições meteorológicas estáveis
            """)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Localização do Incidente**")
            lat = st.number_input("Latitude (graus decimais)", value=-22.8625, format="%.5f",
                                 help="Coordenada geográfica do local da liberação")
            lon = st.number_input("Longitude (graus decimais)", value=-43.2245, format="%.5f",
                                 help="Coordenada geográfica do local da liberação")
        with c2:
            st.markdown("**Parâmetros de Liberação**")
            massa = st.number_input("Quantidade Liberada (kg)", value=0.5, step=0.1, 
                                   help="Massa de agente biológico liberado. Pode ser pó seco, líquido nebulizado ou aerossol.")
            vento = st.number_input("Velocidade do Vento (m/s)", value=2.0, min_value=0.5,
                                   help="Velocidade do vento na direção predominante")
            direcao = st.number_input("Direção do Vento (graus)", value=90,
                                      help="Direção DE ONDE vem o vento. 0° = Norte, 90° = Leste, 180° = Sul, 270° = Oeste")

        # Inicializa estado se não existir
        if 'bio_map_calc' not in st.session_state: 
            st.session_state['bio_map_calc'] = False

        st.markdown("---")
        
        # Botão apenas ativa o estado
        if st.button("CALCULAR ZONA DE RISCO BIOLÓGICO", type="primary", use_container_width=True):
            st.session_state['bio_map_calc'] = True

        # Renderização persistente
        if st.session_state['bio_map_calc']:
            alcance = calcular_pluma_bio(massa, vento, dados['decaimento_uv'])
            
            # Métricas principais
            st.markdown("### Resultados da Simulação")
            
            col_met1, col_met2, col_met3 = st.columns(3)
            col_met1.metric("Alcance da Zona de Risco", f"{alcance:.0f} m", f"{alcance/1000:.2f} km",
                           help="Distância máxima estimada de dispersão do agente")
            col_met2.metric("Fator de Sobrevivência", f"{(1-dados['decaimento_uv'])*100:.0f}%",
                           help="Resistência do agente ao ambiente")
            col_met3.metric("Sensibilidade UV", f"{dados['decaimento_uv']*100:.0f}%",
                           help="Quanto maior, mais sensível à radiação solar")
            
            st.markdown("---")
            
            if dados['decaimento_uv'] > 0.5:
                st.warning(f"**AGENTE SENSÍVEL A UV:** Este agente é inativado rapidamente pela luz solar (sensibilidade: {dados['decaimento_uv']*100:.0f}%). "
                          f"Ataques noturnos ou em condições de baixa luminosidade são significativamente mais eficazes.")
            else:
                st.error(f"**AGENTE RESISTENTE:** Este agente é resistente ao ambiente (sensibilidade UV: {dados['decaimento_uv']*100:.0f}%). "
                        f"A área pode permanecer contaminada por longos períodos. Requer descontaminação ativa.")
            
            # Área aproximada
            area_aproximada = math.pi * (alcance ** 2) * (20 / 360)  # Cone com 20° de abertura
            st.info(f"**Área Aproximada da Zona de Risco:** {area_aproximada/1e6:.2f} km²")

            # Mapa
            st.markdown("---")
            st.markdown("### Mapa de Dispersão Biológica")
            
            m = folium.Map([lat, lon], zoom_start=15, tiles="OpenStreetMap")
            folium.Marker([lat, lon], 
                         icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"), 
                         tooltip=f"<b>PONTO DE LIBERAÇÃO</b><br>Agente: {agente_nome}<br>Massa: {massa:.2f} kg",
                         popup=f"<b>Local da Liberação</b><br>Agente: {agente_nome}<br>Massa Liberada: {massa:.2f} kg<br>Alcance: {alcance:.0f} m").add_to(m)
            
            poly = gerar_cone_bio(lat, lon, alcance, direcao)
            folium.Polygon(poly, color="red", fill=True, fill_opacity=0.4, weight=3,
                          tooltip=f"<b>Zona de Risco Biológico</b><br>Alcance: {alcance:.0f} m<br>Área: {area_aproximada/1e6:.2f} km²",
                          popup=f"<b>Zona de Risco</b><br>Agente: {agente_nome}<br>Alcance: {alcance:.0f} m ({alcance/1000:.2f} km)<br>Área: {area_aproximada/1e6:.2f} km²").add_to(m)
            
            st_folium(m, width=None, height=600)
            
            # Recomendações
            st.markdown("---")
            st.markdown("### Recomendações Operacionais")
            
            st.warning("""
            **AÇÕES IMEDIATAS:**
            1. Estabelecer perímetro de segurança baseado na zona de risco calculada
            2. Evacuar imediatamente todas as pessoas dentro da zona de risco
            3. Implementar abrigo no local para pessoas próximas (fechar janelas, desligar sistemas de ventilação)
            4. Estabelecer pontos de controle de acesso (checkpoints)
            5. Ativar equipes de descontaminação e monitoramento biológico
            6. Coordenar com autoridades de saúde pública e defesa civil
            7. Considerar fatores ambientais (hora do dia, condições meteorológicas) para avaliação de risco
            """)
            
            st.info("""
            **CONSIDERAÇÕES TÉCNICAS:**
            - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
            - Agentes biológicos podem persistir no ambiente dependendo de sua resistência.
            - Mudanças nas condições meteorológicas alteram o comportamento da dispersão.
            - Topografia complexa pode criar zonas de concentração não previstas.
            - Consulte especialistas em defesa biológica para análises detalhadas.
            - Utilize detectores biológicos para monitoramento em tempo real quando disponíveis.
            """)

    # --- ABA 2: SURTO EPIDÊMICO ---
    with tab2:
        st.subheader("Modelagem Epidemiológica - Modelo SIR")
        
        with st.expander("Fundamentos do Modelo SIR", expanded=False):
            st.markdown("""
            #### O que é o Modelo SIR?
            
            O Modelo SIR (Susceptible-Infectious-Recovered) é um modelo matemático fundamental em epidemiologia que divide a população em três compartimentos:
            
            - **S (Susceptible - Suscetíveis):** Pessoas que podem ser infectadas
            - **I (Infectious - Infectados):** Pessoas atualmente infectadas e capazes de transmitir
            - **R (Recovered - Recuperados):** Pessoas que se recuperaram (ou morreram) e não podem mais ser infectadas
            
            #### Parâmetros do Modelo
            
            **R0 (Número Reprodutivo Básico):**
            - R0 > 1: Epidemia cresce (cada infectado contamina mais de 1 pessoa)
            - R0 = 1: Epidemia estável (cada infectado contamina exatamente 1 pessoa)
            - R0 < 1: Epidemia declina (cada infectado contamina menos de 1 pessoa)
            
            **Período Infeccioso:**
            Tempo médio que uma pessoa permanece infectada e capaz de transmitir.
            
            #### Limitações do Modelo
            
            - Assume população fechada (sem nascimentos/mortes não relacionadas)
            - Assume mistura homogênea (todos têm mesma probabilidade de contato)
            - Assume recuperação confere imunidade permanente
            - Não considera variações individuais ou grupos de risco
            - Não modela medidas de controle (quarentena, isolamento) diretamente
            
            #### Interpretação dos Resultados
            
            O modelo ajuda a entender:
            - Quando a epidemia atinge o pico
            - Quantas pessoas serão afetadas
            - Se o sistema de saúde será sobrecarregado
            - Efeito de medidas de controle (redução do R0)
            """)
        
        if not dados['transmissivel']:
            st.warning("**AGENTE NÃO CONTAGIOSO:** Este agente (como Antraz ou Botulismo) **NÃO** causa epidemia contágiosa. "
                      "O modelo SIR não se aplica, pois não há transmissão pessoa-pessoa. O risco é restrito à área de liberação direta.")
        else:
            c_sir1, c_sir2 = st.columns(2)
            with c_sir1:
                st.markdown("**Parâmetros da População**")
                populacao = st.number_input("População Total", value=10000, step=1000,
                                           help="Tamanho da população suscetível na área afetada")
                inicial = st.number_input("Infectados Iniciais", value=5, min_value=1,
                                        help="Número inicial de pessoas infectadas (casos index)")
            with c_sir2:
                st.markdown("**Parâmetros Epidemiológicos**")
                # Permite ao usuário ajustar o R0 para simular medidas de controle
                r0_ajuste = st.slider(f"Taxa de Contágio (R0) - Padrão: {dados['R0']:.2f}", 0.5, 10.0, float(dados['R0']), step=0.1,
                                    help="R0 efetivo considerando medidas de controle. Quarentena, isolamento e distanciamento reduzem o R0.")
                periodo_infeccioso = st.number_input("Período Infeccioso (dias)", value=14, min_value=1, step=1,
                                                    help="Duração média do período em que uma pessoa permanece infectada e capaz de transmitir")
            
            st.markdown("---")
            
            # Inicializa estado se não existir
            if 'bio_sir_calc' not in st.session_state: 
                st.session_state['bio_sir_calc'] = False

            if st.button("SIMULAR EVOLUÇÃO EPIDÊMICA", type="primary", use_container_width=True):
                st.session_state['bio_sir_calc'] = True

            # Renderização persistente
            if st.session_state['bio_sir_calc']:
                df_sir = simular_epidemia_sir(populacao, inicial, r0_ajuste, periodo_infeccioso)
                
                if df_sir is not None:
                    # Encontrar o Pico
                    pico = df_sir['Infectados (Ativos)'].max()
                    dia_pico = df_sir.loc[df_sir['Infectados (Ativos)'] == pico, 'Dias'].values[0]
                    
                    # Calcular totais
                    total_infectados = df_sir['Total Infectados (Acumulado)'].max()
                    total_mortos = total_infectados * dados['letalidade']
                    total_recuperados = total_infectados - total_mortos
                    
                    st.markdown("### Resultados da Simulação")
                    
                    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                    col_res1.metric("Pico de Infectados", f"{int(pico)} pessoas", f"Dia {dia_pico}",
                                   help="Número máximo de pessoas doentes simultaneamente")
                    col_res2.metric("Total de Infectados", f"{int(total_infectados)} pessoas",
                                   help="Total acumulado de pessoas que serão infectadas")
                    col_res3.metric("Total de Mortos", f"{int(total_mortos)} pessoas",
                                   help=f"Estimativa baseada em letalidade de {dados['letalidade']*100:.0f}%")
                    col_res4.metric("Total de Recuperados", f"{int(total_recuperados)} pessoas",
                                   help="Pessoas que se recuperam da infecção")

                    # Análise de capacidade hospitalar
                    st.markdown("---")
                    st.markdown("### Análise de Capacidade do Sistema de Saúde")
                    
                    # Estimativas de necessidade de leitos
                    # Assumindo que 20% dos infectados precisam de hospitalização
                    # E 5% precisam de UTI
                    percentual_hospitalizacao = 0.20
                    percentual_uti = 0.05
                    
                    leitos_necessarios = pico * percentual_hospitalizacao
                    leitos_uti_necessarios = pico * percentual_uti
                    
                    # Capacidade típica (5% da população tem leitos disponíveis)
                    leitos_disponiveis = populacao * 0.05
                    leitos_uti_disponiveis = populacao * 0.01  # 1% da população tem leitos de UTI
                    
                    col_cap1, col_cap2, col_cap3 = st.columns(3)
                    col_cap1.metric("Leitos Necessários (Pico)", f"{int(leitos_necessarios)}", 
                                   f"vs {int(leitos_disponiveis)} disponíveis",
                                   help="Leitos de enfermaria necessários no pico da epidemia")
                    col_cap2.metric("Leitos de UTI Necessários", f"{int(leitos_uti_necessarios)}",
                                   f"vs {int(leitos_uti_disponiveis)} disponíveis",
                                   help="Leitos de UTI necessários no pico da epidemia")
                    col_cap3.metric("Taxa de Ocupação", f"{(leitos_necessarios/leitos_disponiveis)*100:.0f}%",
                                   help="Percentual de ocupação dos leitos disponíveis")

                    # Alerta de Colapso
                    if leitos_necessarios > leitos_disponiveis:
                        st.error(f"**COLAPSO DO SISTEMA DE SAÚDE:** O pico de infectados ({int(pico)}) requer {int(leitos_necessarios)} leitos, "
                                f"mas apenas {int(leitos_disponiveis)} estão disponíveis. O sistema será sobrecarregado.")
                    elif leitos_uti_necessarios > leitos_uti_disponiveis:
                        st.warning(f"**SOBRECARGA DE UTI:** O pico requer {int(leitos_uti_necessarios)} leitos de UTI, "
                                  f"mas apenas {int(leitos_uti_disponiveis)} estão disponíveis. UTI será sobrecarregada.")
                    else:
                        st.success(f"**SISTEMA SUPORTA O SURTO:** A capacidade hospitalar é suficiente para atender o pico de infectados. "
                                  f"Medidas de controle (R0 reduzido) podem manter o sistema operacional.")

                    # Gráfico Altair
                    st.markdown("---")
                    st.markdown("### Evolução Temporal da Epidemia")
                    
                    df_melt = df_sir.melt('Dias', var_name='Categoria', value_name='Pessoas')
                    
                    chart = alt.Chart(df_melt).mark_line(strokeWidth=3).encode(
                        x=alt.X('Dias:Q', title='Dias desde o início'),
                        y=alt.Y('Pessoas:Q', title='Número de Pessoas'),
                        color=alt.Color('Categoria:N', 
                                      scale=alt.Scale(domain=['Suscetíveis', 'Infectados (Ativos)', 'Recuperados/Mortos', 'Total Infectados (Acumulado)'], 
                                                     range=['blue', 'red', 'green', 'orange'])),
                        tooltip=['Dias:Q', 'Categoria:N', 'Pessoas:Q']
                    ).properties(
                        title=f"Curva SIR: {agente_nome} (R0 = {r0_ajuste:.2f})",
                        width=700,
                        height=400
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Tabela de dados
                    st.markdown("---")
                    st.markdown("### Dados Detalhados da Simulação")
                    st.dataframe(df_sir, use_container_width=True, hide_index=True)
                    
                    # Recomendações
                    st.markdown("---")
                    st.markdown("### Recomendações Operacionais")
                    
                    if r0_ajuste > 1.0:
                        st.warning("""
                        **MEDIDAS DE CONTROLE URGENTES:**
                        1. Implementar quarentena e isolamento de casos
                        2. Estabelecer distanciamento social
                        3. Usar equipamentos de proteção individual (EPI)
                        4. Implementar rastreamento de contatos
                        5. Considerar medidas de distanciamento social
                        6. Preparar sistema de saúde para sobrecarga
                        7. Estabelecer centros de tratamento temporários se necessário
                        """)
                    else:
                        st.info("""
                        **SITUAÇÃO CONTROLADA:**
                        1. R0 < 1 indica que a epidemia está em declínio
                        2. Manter medidas de controle para evitar recrudescimento
                        3. Continuar monitoramento e vigilância epidemiológica
                        4. Manter capacidade de resposta rápida se situação mudar
                        """)
                    
                    st.info("""
                    **CONSIDERAÇÕES TÉCNICAS:**
                    - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
                    - O modelo assume população homogênea e não considera grupos de risco.
                    - Medidas de controle (quarentena, isolamento) reduzem o R0 efetivo.
                    - Capacidade hospitalar pode variar significativamente entre regiões.
                    - Consulte epidemiologistas para análises detalhadas e estratégias de controle.
                    - Modelos mais complexos (SEIR, SEIRS) podem ser necessários para análises avançadas.
                    """)
