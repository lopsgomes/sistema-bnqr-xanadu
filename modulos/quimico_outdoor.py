import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS QUÍMICO (PROPRIEDADES E LIMITES TÓXICOS)
# =============================================================================
# AEGL (Acute Exposure Guideline Levels) - Níveis de Exposição Aguda
# Fonte: EPA Acute Exposure Guideline Levels (AEGL) Program
# Unidade: ppm (partes por milhão em volume)
# Tempo de Exposição: AEGL-1 (10 min), AEGL-2 (10 min), AEGL-3 (10 min)
# Densidade Relativa ao Ar: < 1.0 (Leve, sobe) | > 1.0 (Pesado, rasteja no chão)
SUBSTANCIAS = {
    "Ácido Clorídrico (HCl - Gás)": {
        "mw": 36.46, "densidade": 1.3,
        "aegl1": 1.8, "aegl2": 22, "aegl3": 100,
        "desc": "Névoa ácida branca. Irritante severo. Comum em acidentes rodoviários com carretas."
    },
    "Ácido Nítrico (Fumegante)": {
        "mw": 63.01, "densidade": 2.2, # Vapores NOx associados
        "aegl1": 0.5, "aegl2": 24, "aegl3": 86,
        "desc": "Líquido que fumega ar laranja/vermelho (NO2). Oxidante forte. Causa edema pulmonar tardio."
    },
    "Acroleína": {
        "mw": 56.06, "densidade": 1.9,
        "aegl1": 0.03, "aegl2": 0.10, "aegl3": 1.4,
        "desc": "Vapor de incêndios ou industrial. Lacrimogêneo extremamente potente. Letal em dose baixíssima."
    },
    "Amônia (Anidra)": {
        "mw": 17.03, "densidade": 0.6,
        "aegl1": 30, "aegl2": 160, "aegl3": 1100,
        "desc": "Gás leve (sobe), a menos que seja vazamento líquido (névoa fria). Risco de sufocamento."
    },
    "Arsina (SA)": {
        "mw": 77.95, "densidade": 2.7,
        "aegl1": 0.0, "aegl2": 0.12, "aegl3": 0.86, # Extremamente tóxico
        "desc": "Gás incolor (cheiro de alho). Usado em semicondutores. Destrói hemácias (sangue) rapidamente."
    },
    "Boro Trifluoreto": {
        "mw": 67.81, "densidade": 2.4,
        "aegl1": 2.5, "aegl2": 18, "aegl3": 100,
        "desc": "Gás incolor que fumega no ar. Corrosivo para pele e pulmões. Reage com água."
    },
    "Bromo (Vapor)": {
        "mw": 159.80, "densidade": 5.5, # Muito Pesado
        "aegl1": 0.33, "aegl2": 2.2, "aegl3": 8.5,
        "desc": "Vapores vermelhos pesados. Destrói tecidos por oxidação. Viaja muito rente ao chão."
    },
    "Cianeto de Hidrogênio (HCN)": {
        "mw": 27.03, "densidade": 0.94,
        "aegl1": 2.5, "aegl2": 7.1, "aegl3": 15,
        "desc": "Gás leve. Dispersão rápida e letal (asfixiante químico). Cheiro de amêndoas."
    },
    "Cloreto de Vinila": {
        "mw": 62.50, "densidade": 2.15,
        "aegl1": 250, "aegl2": 1200, "aegl3": 4800,
        "desc": "Gás inflamável e carcinogênico (plásticos). Risco de explosão é maior que o tóxico agudo."
    },
    "Cloro Gás (Cl2)": {
        "mw": 70.90, "densidade": 2.5,
        "aegl1": 0.5, "aegl2": 2.0, "aegl3": 20.0,
        "desc": "Gás verde-amarelo, muito pesado. Rasteja pelo chão, entra em porões e metrôs."
    },
    "Diborano": {
        "mw": 27.67, "densidade": 0.96,
        "aegl1": 0.0, "aegl2": 2.0, "aegl3": 7.3,
        "desc": "Combustível de foguete. Pirofórico (pode pegar fogo espontaneamente no ar). Toxicidade pulmonar."
    },
    "Dióxido de Cloro": {
        "mw": 67.45, "densidade": 2.3,
        "aegl1": 0.15, "aegl2": 0.63, "aegl3": 1.8,
        "desc": "Gás amarelo-avermelhado. Tratamento de água. Instável e explosivo em altas concentrações."
    },
    "Dióxido de Enxofre (SO2)": {
        "mw": 64.06, "densidade": 2.2,
        "aegl1": 0.2, "aegl2": 0.75, "aegl3": 30,
        "desc": "Subproduto industrial. Pesado e invisível. Causa espasmo de glote imediato."
    },
    "Dióxido de Nitrogênio (NO2)": {
        "mw": 46.00, "densidade": 1.6,
        "aegl1": 0.5, "aegl2": 12, "aegl3": 20,
        "desc": "Fumaça vermelha/marrom. Típico de explosões ou ataques ácidos."
    },
    "Dissulfeto de Carbono": {
        "mw": 76.14, "densidade": 2.6,
        "aegl1": 13, "aegl2": 160, "aegl3": 480,
        "desc": "Líquido que vira vapor muito inflamável e neurotóxico. Vapores pesados."
    },
    "Flúor (Gás)": {
        "mw": 38.00, "densidade": 1.3,
        "aegl1": 1.7, "aegl2": 5.0, "aegl3": 13,
        "desc": "O oxidante mais forte que existe. Reage com tudo. Causa queimaduras profundas."
    },
    "Fluoreto de Hidrogênio (HF)": {
        "mw": 20.01, "densidade": 0.92, 
        "aegl1": 1.0, "aegl2": 24, "aegl3": 44,
        "desc": "EXTREMO. Corrói vidro e ossos. Forma nuvem branca densa que viaja baixo, apesar do MW leve."
    },
    "Formaldeído (Gás)": {
        "mw": 30.03, "densidade": 1.0,
        "aegl1": 0.9, "aegl2": 14, "aegl3": 35,
        "desc": "Gás irritante e sensibilizante. Nuvem invisível próxima à densidade do ar."
    },
    "Fosfina (PH3)": {
        "mw": 34.00, "densidade": 1.17,
        "aegl1": 0.0, "aegl2": 0.5, "aegl3": 3.6, # Muito baixo
        "desc": "Fumigante agrícola ou subproduto de laboratório. Cheiro de alho/peixe. Mata por falha metabólica."
    },
    "Fosgênio (CG)": {
        "mw": 98.92, "densidade": 3.4,
        "aegl1": 0.0, "aegl2": 0.1, "aegl3": 1.5,
        "desc": "Agente de guerra (WWI). Cheiro de feno mofado. Efeitos letais tardios (edema)."
    },
    "Hidrazina": {
        "mw": 32.05, "densidade": 1.1,
        "aegl1": 0.1, "aegl2": 4.6, "aegl3": 35,
        "desc": "Combustível de foguete/caça. Ataca fígado e rins. Absorvido pela pele."
    },
    "Metil Brometo": {
        "mw": 94.94, "densidade": 3.3,
        "aegl1": 0.0, "aegl2": 210, "aegl3": 850,
        "desc": "Fumigante pesado. Neurotóxico cumulativo. Inodoro em concentrações perigosas."
    },
    "Metil Isocianato (MIC)": {
        "mw": 57.05, "densidade": 1.4,
        "aegl1": 0.0, "aegl2": 0.17, "aegl3": 0.5,
        "desc": "Químico de Bhopal. Reage com água do corpo. Nuvem mortal rasteira."
    },
    "Metil Mercaptana": {
        "mw": 48.11, "densidade": 1.66,
        "aegl1": 0.005, "aegl2": 37, "aegl3": 120,
        "desc": "Cheiro de repolho podre. Depressor do sistema nervoso central. Inflamável."
    },
    "Monóxido de Carbono (CO)": {
        "mw": 28.01, "densidade": 0.97,
        "aegl1": 0, "aegl2": 83, "aegl3": 330,
        "desc": "Assassino silencioso. Mistura-se perfeitamente ao ar e viaja longas distâncias."
    },
    "Óxido de Etileno": {
        "mw": 44.05, "densidade": 1.5,
        "aegl1": 0.0, "aegl2": 45, "aegl3": 200,
        "desc": "Gás esterilizante. Inflamável em ampla faixa. Causa danos neurológicos."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "mw": 34.08, "densidade": 1.2,
        "aegl1": 0.5, "aegl2": 27, "aegl3": 50,
        "desc": "Gás de esgoto. Cheiro de ovo podre some em altas doses (anestesia olfativa)."
    },
    "Tolueno 2,4-Diisocianato (TDI)": {
        "mw": 174.16, "densidade": 6.0, # Pesadíssimo
        "aegl1": 0.02, "aegl2": 0.17, "aegl3": 0.55,
        "desc": "Vapores de espumas industriais. Asma severa e danos pulmonares imediatos."
    },
    "Acetileno": {
        "mw": 26.04, "densidade": 0.9,
        "aegl1": 0, "aegl2": 0, "aegl3": 0,  # Inflamável, não tóxico agudo
        "desc": "Gás altamente inflamável usado em solda. Risco principal é explosão, não toxicidade aguda. Muito instável."
    },
    "Acrilonitrila": {
        "mw": 53.06, "densidade": 1.8,
        "aegl1": 0.5, "aegl2": 17, "aegl3": 40,
        "desc": "Monômero para plásticos. Carcinogênico e neurotóxico. Metaboliza em cianeto no corpo."
    },
    "Cloreto de Cianogênio (CNCl)": {
        "mw": 61.47, "densidade": 2.1,
        "aegl1": 0.0, "aegl2": 0.2, "aegl3": 0.5,
        "desc": "Agente de guerra química. Combina toxicidade do cianeto com irritação do cloro. Extremamente letal."
    },
    "Dimetil Sulfato": {
        "mw": 126.13, "densidade": 4.3,
        "aegl1": 0.0, "aegl2": 0.1, "aegl3": 0.5,
        "desc": "Vapor pesado e invisível. Carcinogênico e mutagênico. Causa queimaduras químicas severas."
    },
    "Éter Dietílico": {
        "mw": 74.12, "densidade": 2.6,
        "aegl1": 200, "aegl2": 1900, "aegl3": 10000,
        "desc": "Solvente altamente inflamável. Vapores pesados. Depressor do sistema nervoso central. Risco de explosão."
    },
    "Fosfina (PH3)": {
        "mw": 34.00, "densidade": 1.17,
        "aegl1": 0.0, "aegl2": 0.5, "aegl3": 3.6,
        "desc": "Fumigante agrícola. Cheiro de alho/peixe podre. Causa falha metabólica e danos ao fígado. Extremamente tóxico."
    },
    "Metilamina": {
        "mw": 31.06, "densidade": 1.1,
        "aegl1": 10, "aegl2": 100, "aegl3": 500,
        "desc": "Gás básico com cheiro de peixe. Irritante severo para olhos e pulmões. Inflamável."
    },
    "Óxido de Nitrogênio (NO)": {
        "mw": 30.01, "densidade": 1.0,
        "aegl1": 0, "aegl2": 25, "aegl3": 50,
        "desc": "Gás incolor que oxida rapidamente a NO2 no ar. Irritante pulmonar. Produto de combustão."
    },
    "Óxido Nitroso (N2O)": {
        "mw": 44.01, "densidade": 1.5,
        "aegl1": 0, "aegl2": 0, "aegl3": 0,  # Anestésico, não tóxico agudo
        "desc": "Gás anestésico (gás do riso). Em altas concentrações, desloca oxigênio causando asfixia."
    },
    "Peróxido de Hidrogênio (Vapor)": {
        "mw": 34.01, "densidade": 1.2,
        "aegl1": 10, "aegl2": 50, "aegl3": 100,
        "desc": "Vapores de peróxido concentrado. Oxidante forte. Pode causar queimaduras químicas e irritação severa."
    },
    "Sarin (GB)": {
        "mw": 140.10, "densidade": 4.9,
        "aegl1": 0.0, "aegl2": 0.0003, "aegl3": 0.001,
        "desc": "Agente neurotóxico de guerra química. Extremamente letal em doses mínimas. Inibe colinesterase."
    },
    "Tetracloreto de Carbono": {
        "mw": 153.82, "densidade": 5.3,
        "aegl1": 5, "aegl2": 20, "aegl3": 200,
        "desc": "Vapores pesados de solvente clorado. Tóxico para fígado e rins. Carcinogênico. Não inflamável."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (MODELO GAUSSIANO DE PLUMA)
# =============================================================================
# Baseado em: Gaussian Plume Model (Pasquill-Gifford), Briggs Dispersion Coefficients
# Referências: EPA SCREEN3, ALOHA (Areal Locations of Hazardous Atmospheres)
# O modelo assume: fonte pontual contínua, condições meteorológicas estáveis,
# terreno plano, sem obstáculos significativos
def estimar_dispersao_gaussiana(taxa_kg_s, vento_ms, condicao_tempo, substancia_info):
    """
    Calcula o comprimento da pluma tóxica usando o Modelo Gaussiano de Pluma.
    
    Parâmetros:
    - taxa_kg_s: Taxa de liberação da substância em kg/s
    - vento_ms: Velocidade do vento em m/s
    - condicao_tempo: Condição meteorológica (determina classe de estabilidade)
    - substancia_info: Dicionário com propriedades da substância (MW, densidade, AEGLs)
    
    Retorna:
    - distancias: Dicionário com distâncias para cada nível AEGL (m)
    - classe_pasquill: Classe de estabilidade atmosférica (A, D, F)
    - df_detalhado: DataFrame com informações detalhadas por zona
    """
    # 1. Definição da Classe de Estabilidade de Pasquill-Gifford (A-F)
    # Baseado em condições meteorológicas e radiação solar
    # A = Extremamente Instável (melhor dispersão)
    # B = Moderadamente Instável
    # C = Ligeiramente Instável
    # D = Neutro (condições padrão)
    # E = Ligeiramente Estável
    # F = Moderadamente Estável (pior dispersão - gás viaja longe sem diluir)
    mapa_estabilidade = {
        "Dia: Sol Forte (Instável)": "A",      # O gás sobe e dispersa rápido
        "Dia: Nublado / Sol Fraco": "D",       # Neutro
        "Noite: Nublado / Vento Forte": "D",   # Neutro
        "Noite: Clara / Vento Calmo": "F"      # Estável (PIOR CENÁRIO: O gás não sobe, viaja longe rente ao chão)
    }
    classe_pasquill = mapa_estabilidade[condicao_tempo]
    
    # 2. Conversão de Limites AEGL (ppm -> mg/m³)
    # Fórmula: mg/m³ = (ppm * MW) / 24.45
    # Onde: MW = massa molecular (g/mol), 24.45 = volume molar a 25°C e 1 atm
    mw = substancia_info['mw']
    limites_mgm3 = {}
    limites_ppm = {}
    for nivel in ['aegl3', 'aegl2', 'aegl1']:
        ppm = substancia_info[nivel]
        limites_ppm[nivel] = ppm
        if ppm > 0:
            limites_mgm3[nivel] = (ppm * mw) / 24.45
        else:
            limites_mgm3[nivel] = None

    # 3. Cálculo de Alcance da Pluma (Modelo Gaussiano Simplificado)
    # O modelo gaussiano assume que a concentração diminui com a distância
    # seguindo uma distribuição gaussiana (normal) em três dimensões.
    # Para simplificação computacional, usamos uma aproximação heurística
    # baseada em modelos como ALOHA e SCREEN3.
    
    distancias = {}
    dados_detalhados = []
    
    # Fator de dispersão baseado na classe de estabilidade
    # Classes instáveis (A) dispersam mais rápido (nuvem curta e larga)
    # Classes estáveis (F) dispersam pouco (nuvem longa e estreita - mais perigosa)
    fator_dispersao = {
        "A": 0.2,  # Dispersa muito (nuvem curta e gorda)
        "D": 1.0,  # Padrão neutro
        "F": 3.0   # Dispersa pouco (nuvem longa e fina - Perigo!)
    }[classe_pasquill]
    
    # Ajuste por densidade relativa ao ar
    # Gases pesados (densidade > 1) tendem a rastejar no chão e viajar mais longe
    # Gases leves (densidade < 1) tendem a subir e dispersar mais rápido
    densidade = substancia_info['densidade']
    if densidade > 1.5:
        fator_densidade = 1.5  # Muito pesado - viaja muito longe baixo
    elif densidade > 1.0:
        fator_densidade = 1.2  # Pesado - viaja mais longe
    else:
        fator_densidade = 1.0  # Leve - dispersa mais rápido

    # Cálculo do alcance para cada nível AEGL
    for nivel, conc_limite in limites_mgm3.items():
        if conc_limite:
            # Equação simplificada de alcance
            # Baseada em: Alcance ∝ sqrt(Q / (u * C)) * Fatores
            # Onde: Q = taxa de liberação (mg/s), u = velocidade do vento (m/s),
            #       C = concentração limite (mg/m³)
            termo_fonte = (taxa_kg_s * 1000000)  # Conversão kg/s -> mg/s
            
            # Evitar divisão por zero no vento (mínimo 0.5 m/s)
            u = max(vento_ms, 0.5)
            
            # Modelo heurístico calibrado para ALOHA (aproximação)
            # O fator 15 é um coeficiente empírico de calibração
            alcance_m = math.sqrt(termo_fonte / (u * conc_limite * 0.5)) * 15 * fator_dispersao * fator_densidade
            
            # Limites físicos do modelo (validação)
            alcance_m = min(alcance_m, 20000)  # Máximo: 20 km
            alcance_m = max(alcance_m, 30)     # Mínimo: 30 m
            
            distancias[nivel] = alcance_m
            
            # Área aproximada da zona (cone com abertura baseada na estabilidade)
            abertura_graus = {"A": 50, "D": 30, "F": 15}[classe_pasquill]
            area_m2 = math.pi * (alcance_m ** 2) * (abertura_graus / 360)
            
            dados_detalhados.append({
                "Zona": {"aegl3": "AEGL-3 (Morte)", "aegl2": "AEGL-2 (Incapacitação)", "aegl1": "AEGL-1 (Desconforto)"}[nivel],
                "Alcance (m)": alcance_m,
                "Alcance (km)": alcance_m / 1000,
                "Área (m²)": area_m2,
                "Área (km²)": area_m2 / 1e6,
                "Limite (ppm)": limites_ppm[nivel],
                "Limite (mg/m³)": conc_limite
            })
        else:
            distancias[nivel] = 0
    
    df_detalhado = pd.DataFrame(dados_detalhados)

    return distancias, classe_pasquill, df_detalhado

def gerar_poligono_direcional(lat, lon, distancia, direcao_vento_graus, abertura_graus=30):
    """
    Gera um triângulo/cone representando a pluma na direção do vento.
    """
    # Vento vem de X, pluma vai para X + 180
    angulo_eixo = (direcao_vento_graus + 180) % 360
    
    coords = []
    r_terra = 6378137
    
    # Ponto de Origem
    coords.append([lat, lon])
    
    # Calcular arco do cone
    num_pontos = 10
    inicio_ang = angulo_eixo - (abertura_graus / 2)
    fim_ang = angulo_eixo + (abertura_graus / 2)
    
    for i in range(num_pontos + 1):
        ang_atual_deg = inicio_ang + (i * (fim_ang - inicio_ang) / num_pontos)
        ang_rad = math.radians(90 - ang_atual_deg) # Ajuste norte geográfico
        
        # Projetar ponto
        dx = distancia * math.cos(ang_rad)
        dy = distancia * math.sin(ang_rad)
        
        d_lat = (dy / r_terra) * (180 / math.pi)
        d_lon = (dx / r_terra) * (180 / math.pi) / math.cos(math.radians(lat))
        
        coords.append([lat + d_lat, lon + d_lon])
        
    # Fechar polígono voltando à origem
    coords.append([lat, lon])
    
    return coords

# =============================================================================
# 3. INTERFACE VISUAL (FRONT-END)
# =============================================================================
def renderizar():
    st.title("Dispersão Atmosférica de Gases Tóxicos")
    st.markdown("**Modelagem de dispersão atmosférica de gases tóxicos utilizando Modelo Gaussiano de Pluma (Pasquill-Gifford)**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos Teóricos e Conceitos Operacionais", expanded=True):
        st.markdown("""
        #### O que é Dispersão Atmosférica?
        
        Quando um gás tóxico é liberado na atmosfera, ele não permanece estacionário. O vento e as condições meteorológicas criam uma "pluma" (formato de cone) que se estende por quilômetros, transportando o contaminante e diluindo-o gradualmente. O Modelo Gaussiano de Pluma é uma ferramenta matemática que prediz como essa nuvem se comporta.
        
        #### Fatores Críticos que Influenciam a Dispersão
        
        **1. Densidade Relativa ao Ar:**
        A densidade do gás em relação ao ar determina seu comportamento:
        * **Gases Pesados (densidade > 1.0):** Como Cloro (2.5x mais pesado), Bromo (5.5x), ou Dióxido de Enxofre (2.2x). Estes gases **rastejam no chão**, entram em porões, bueiros, áreas baixas e podem viajar longas distâncias sem se diluir significativamente. São extremamente perigosos em terrenos acidentados ou áreas urbanas com estruturas baixas.
        * **Gases Leves (densidade < 1.0):** Como Amônia (0.6x), Hidrogênio (0.07x), ou Metano (0.55x). Estes gases **sobem rapidamente** e tendem a se dispersar mais rápido na atmosfera. São menos perigosos no nível do solo, a menos que estejam em condições muito frias ou em grandes quantidades.
        
        **2. Velocidade do Vento:**
        * **Vento Forte (> 5 m/s):** Dilui o gás rapidamente (reduz concentração), mas transporta a nuvem para distâncias maiores. A área afetada pode ser maior, mas com concentrações menores.
        * **Vento Fraco (< 1 m/s):** O gás fica concentrado próximo à fonte, criando uma zona de alta concentração letal. Em condições de calmaria, a nuvem pode ficar praticamente estacionária sobre o local do vazamento.
        
        **3. Estabilidade Atmosférica (Dia vs Noite):**
        A estabilidade atmosférica é determinada pela relação entre temperatura do ar e temperatura do solo:
        * **Dia com Sol Forte (Classe A - Instável):** O calor do solo aquece o ar próximo à superfície, criando correntes de convecção que fazem o ar subir. A nuvem tóxica se dispersa rapidamente na vertical, reduzindo a concentração no nível do solo. **É o melhor cenário para dispersão.**
        * **Dia Nublado ou Sol Fraco (Classe D - Neutro):** Condições neutras. Dispersão moderada.
        * **Noite Clara com Vento Calmo (Classe F - Estável):** Ocorre **Inversão Térmica**. O solo perde calor rapidamente, resfriando o ar próximo à superfície. O ar frio fica "preso" próximo ao chão, sem subir. A nuvem tóxica viaja longas distâncias sem se diluir significativamente, mantendo concentrações perigosas. **É o pior cenário possível.**
        
        #### Níveis AEGL (Acute Exposure Guideline Levels)
        
        Os AEGLs são níveis de concentração desenvolvidos pela EPA para exposição aguda (10 minutos a 8 horas):
        * **AEGL-1:** Nível de desconforto. Efeitos notáveis, mas reversíveis após exposição.
        * **AEGL-2:** Nível de incapacitação. Efeitos irreversíveis ou outros efeitos sérios que podem prejudicar a capacidade de evacuação.
        * **AEGL-3:** Nível de morte. Concentração acima da qual é esperado que ocorram efeitos fatais ou risco de vida.
        
        #### Limitações do Modelo
        
        Este modelo utiliza simplificações para fins didáticos e operacionais:
        * Assume terreno plano e sem obstáculos significativos
        * Não considera topografia complexa (montanhas, vales, edifícios)
        * Assume condições meteorológicas estáveis (sem mudanças de vento ou estabilidade)
        * Não modela reações químicas na atmosfera
        * Não considera chuvas ou outras condições que afetam deposição
        * Assume fonte pontual contínua (vazamento constante)
        
        Para análises detalhadas, utilize modelos atmosféricos avançados (ALOHA, AERMOD, CALPUFF, HYSPLIT).
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Localização e Condições Meteorológicas")
        st.markdown("**Coordenadas Geográficas do Ponto de Liberação**")
        lat = st.number_input("Latitude (graus decimais)", value=-22.8625, format="%.5f",
                             help="Coordenada geográfica do local do vazamento. Use o Google Maps para obter coordenadas precisas.")
        lon = st.number_input("Longitude (graus decimais)", value=-43.2245, format="%.5f",
                             help="Coordenada geográfica do local do vazamento.")
        
        st.markdown("---")
        st.markdown("**Condições Meteorológicas**")
        st.caption("As condições meteorológicas são críticas para determinar o comportamento da pluma tóxica.")
        vento_ms = st.number_input("Velocidade do Vento (m/s)", value=3.0, min_value=0.5, step=0.5, 
                                   help="Velocidade do vento em metros por segundo. Use anemômetro se disponível. Referência: 1 m/s = fumaça sobe quase reta; 3 m/s = leve brisa; 5 m/s = bandeiras esticadas; 10 m/s = vento forte.")
        direcao_vento = st.number_input("Direção do Vento (graus)", value=90, min_value=0, max_value=360, 
                                        help="Direção DE ONDE vem o vento (direção de origem). 0° = Norte, 90° = Leste, 180° = Sul, 270° = Oeste. A pluma se desloca na direção oposta.")
        
        tempo = st.selectbox(
            "Condição do Tempo (Estabilidade Atmosférica)",
            ["Dia: Sol Forte (Instável)", "Dia: Nublado / Sol Fraco", "Noite: Nublado / Vento Forte", "Noite: Clara / Vento Calmo"],
            index=1,
            help="A estabilidade atmosférica determina a classe de Pasquill-Gifford. Noite Clara com vento calmo (Classe F) é o pior cenário - gás viaja longe sem diluir."
        )

    with col2:
        st.subheader("Características da Ameaça Química")
        quimico = st.selectbox("Substância Química", list(SUBSTANCIAS.keys()),
                              help="Selecione a substância química envolvida no vazamento. Consulte a ficha de segurança ou utilize detectores de gás para identificação.")
        dados_quim = SUBSTANCIAS[quimico]
        
        st.info(f"**Descrição:** {dados_quim['desc']}")
        
        # Informações técnicas da substância
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"**Massa Molecular:** {dados_quim['mw']:.2f} g/mol")
            st.caption(f"**Densidade Relativa:** {dados_quim['densidade']:.2f} (ar = 1.0)")
        with col_info2:
            st.caption(f"**AEGL-1:** {dados_quim['aegl1']:.2f} ppm")
            st.caption(f"**AEGL-2:** {dados_quim['aegl2']:.2f} ppm")
            st.caption(f"**AEGL-3:** {dados_quim['aegl3']:.2f} ppm")
        
        # Alerta para gases pesados
        if dados_quim['densidade'] > 1.5:
            st.error("**GÁS MUITO PESADO:** Tende a rastejar no chão e acumular em baixadas, porões e bueiros. Extremamente perigoso em áreas urbanas.")
        elif dados_quim['densidade'] > 1.0:
            st.warning("**GÁS PESADO:** Tende a rastejar no chão. Pode entrar em estruturas baixas e viajar longas distâncias sem se diluir significativamente.")
        else:
            st.success("**GÁS LEVE:** Tende a subir e se dispersar mais rapidamente. Menos perigoso no nível do solo.")
        
        st.markdown("---")
        taxa = st.number_input("Taxa de Vazamento (kg/s)", value=1.0, min_value=0.1, step=0.1, 
                              help="Taxa de liberação da substância em quilogramas por segundo. Exemplos: Vazamento pequeno de tanque: 0.5-2 kg/s; Tanque rasgado: 10-50 kg/s; Vazamento de duto: 5-20 kg/s.")

    # Estado
    if 'pluma_calc' not in st.session_state:
        st.session_state['pluma_calc'] = False

    st.markdown("---")
    
    if st.button("SIMULAR DISPERSÃO DA PLUMA TÓXICA", type="primary", use_container_width=True):
        st.session_state['pluma_calc'] = True

    if st.session_state['pluma_calc']:
        
        distancias, classe_p, df_detalhado = estimar_dispersao_gaussiana(taxa, vento_ms, tempo, dados_quim)
        
        st.success(f"**SIMULAÇÃO CONCLUÍDA** | Classe de Estabilidade Pasquill-Gifford: **{classe_p}**")
        
        # Métricas principais
        st.markdown("### Resultados da Simulação")
        
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
            st.metric("Classe Pasquill", classe_p, 
                     help="Classe de estabilidade atmosférica (A=Instável, D=Neutro, F=Estável)")
        with col_met2:
            st.metric("Zona Vermelha (AEGL-3)", f"{distancias['aegl3']:.0f} m", 
                     delta="Risco de Morte", delta_color="inverse",
                     help="Zona de risco de morte - concentração letal")
        with col_met3:
            st.metric("Zona Laranja (AEGL-2)", f"{distancias['aegl2']:.0f} m", 
                     delta="Incapacitação", delta_color="off",
                     help="Zona de incapacitação - efeitos irreversíveis")
        with col_met4:
            st.metric("Zona Amarela (AEGL-1)", f"{distancias['aegl1']:.0f} m", 
                     delta="Desconforto",
                     help="Zona de desconforto - efeitos notáveis mas reversíveis")
        
        # Tabela detalhada
        if len(df_detalhado) > 0:
            st.markdown("### Detalhamento das Zonas de Exposição")
            st.dataframe(df_detalhado, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma zona de exposição calculada. Verifique se os valores AEGL da substância são válidos.")
        
        # Informações técnicas
        st.markdown("---")
        st.markdown("### Informações Técnicas")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"""
            **Substância:** {quimico}  
            **Taxa de Vazamento:** {taxa:.1f} kg/s  
            **Velocidade do Vento:** {vento_ms:.1f} m/s  
            **Direção do Vento:** {direcao_vento}° (origem)  
            **Condição Meteorológica:** {tempo}
            """)
        with col_info2:
            area_total = df_detalhado.iloc[0]['Área (km²)'] if len(df_detalhado) > 0 else 0.0
            st.markdown(f"""
            **Massa Molecular:** {dados_quim['mw']:.2f} g/mol  
            **Densidade Relativa:** {dados_quim['densidade']:.2f}  
            **Classe de Estabilidade:** {classe_p}  
            **Área Total Afetada (AEGL-1):** {area_total:.2f} km²
            """)

        # MAPA
        st.markdown("---")
        st.markdown("### Mapa de Dispersão da Pluma Tóxica")
        
        m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
        
        # Marcador do ponto de liberação
        folium.Marker(
            [lat, lon],
            tooltip=f"<b>PONTO DE LIBERAÇÃO</b><br>Substância: {quimico}<br>Taxa: {taxa:.1f} kg/s<br>Classe Pasquill: {classe_p}",
            popup=f"<b>Local do Vazamento</b><br>Substância: {quimico}<br>Taxa de Vazamento: {taxa:.1f} kg/s<br>Velocidade do Vento: {vento_ms:.1f} m/s<br>Direção: {direcao_vento}°",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)

        # Desenhar Plumas (Ordem: Amarelo > Laranja > Vermelho, para o menor ficar em cima)
        cores = {'aegl1': '#FFD700', 'aegl2': '#FF8C00', 'aegl3': '#FF0000'}
        nomes = {
            'aegl1': 'AEGL-1 (Desconforto)', 
            'aegl2': 'AEGL-2 (Incapacitação)', 
            'aegl3': 'AEGL-3 (Risco de Morte)'
        }
        
        # Abertura do cone baseada na estabilidade
        # Classe A (instável) = cone largo (dispersa mais)
        # Classe F (estável) = cone fino (viaja longe sem diluir)
        abertura = {"A": 50, "D": 30, "F": 15}[classe_p]

        for nivel in ['aegl1', 'aegl2', 'aegl3']:
            d = distancias[nivel]
            if d > 0:
                poly = gerar_poligono_direcional(lat, lon, d, direcao_vento, abertura_graus=abertura)
                
                # Área da zona e limite
                if len(df_detalhado) > 0:
                    zona_df = df_detalhado[df_detalhado['Zona'] == nomes[nivel]]
                    if len(zona_df) > 0:
                        area_km2 = zona_df['Área (km²)'].values[0]
                        limite_ppm = zona_df['Limite (ppm)'].values[0]
                    else:
                        area_km2 = 0.0
                        limite_ppm = dados_quim[nivel]
                else:
                    area_km2 = 0.0
                    limite_ppm = dados_quim[nivel]
                
                folium.Polygon(
                    locations=poly,
                    color=cores[nivel],
                    fill=True,
                    fill_opacity=0.4,
                    weight=3,
                    tooltip=f"<b>{nomes[nivel]}</b><br>Alcance: {d:.0f} m<br>Área: {area_km2:.2f} km²<br>Limite: {limite_ppm:.2f} ppm",
                    popup=f"<b>{nomes[nivel]}</b><br>Alcance: {d:.0f} m ({d/1000:.2f} km)<br>Área: {area_km2:.2f} km²<br>Limite AEGL: {limite_ppm:.2f} ppm"
                ).add_to(m)

        # Adicionar legenda
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 220px; height: 140px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <b>Legenda das Zonas</b><br>
        <span style="color: #FF0000;">●</span> Vermelho: AEGL-3 (Risco de Morte)<br>
        <span style="color: #FF8C00;">●</span> Laranja: AEGL-2 (Incapacitação)<br>
        <span style="color: #FFD700;">●</span> Amarelo: AEGL-1 (Desconforto)
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        st_folium(m, width=None, height=600)
        
        # Recomendações Operacionais
        st.markdown("---")
        st.markdown("### Recomendações Operacionais")
        
        st.warning("""
        **AÇÕES IMEDIATAS:**
        1. Estabelecer perímetro de segurança baseado na Zona Vermelha (AEGL-3)
        2. Evacuar imediatamente todas as pessoas dentro da Zona Vermelha (sentido contrário ao vento)
        3. Implementar abrigo no local para pessoas na Zona Amarela (fechar janelas, desligar sistemas de ventilação)
        4. Estabelecer pontos de controle de acesso (checkpoints) nas bordas das zonas
        5. Monitorar continuamente as condições meteorológicas (mudanças podem alterar as zonas)
        6. Coordenar com autoridades de saúde pública e defesa civil
        7. Considerar evacuação preventiva da Zona Laranja se condições meteorológicas piorarem
        """)
        
        st.info("""
        **CONSIDERAÇÕES TÉCNICAS:**
        - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
        - Gases pesados podem se acumular em baixadas, porões e estruturas baixas mesmo além das zonas calculadas.
        - Mudanças nas condições meteorológicas (velocidade/direção do vento, estabilidade) alteram drasticamente o comportamento da pluma.
        - Topografia complexa (montanhas, vales, edifícios) pode criar zonas de concentração não previstas pelo modelo.
        - Consulte modelos atmosféricos avançados (ALOHA, AERMOD) para análises detalhadas.
        - Utilize detectores de gás para monitoramento em tempo real das concentrações reais.
        """)