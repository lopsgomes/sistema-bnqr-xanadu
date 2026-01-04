import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# =============================================================================
# 1. BANCO DE DADOS (SUBSTÂNCIAS QUÍMICAS PARA AMBIENTES CONFINADOS)
# =============================================================================
# Propriedades químicas para modelagem de contaminação em ambientes fechados
# Fonte: NIOSH Pocket Guide, FISPQ (Ficha de Informação de Segurança de Produtos Químicos)
# IDLH = Immediately Dangerous to Life or Health (ppm)
# LEL = Lower Explosive Limit (% em volume)
# Volatilidade: Fator 0.0-1.0 (1.0 = muito volátil, 0.0 = não volátil)
SUBSTANCIAS_INDOOR = {
    "2-Mercaptoetanol (Beta)": {
        "mw": 78.13, "idlh": 150, "lel": 2.3, "volatilidade": 0.1, 
        "desc": "Cheiro de peixe podre. Fatal se inalado em alta dose. Evapora devagar, mas satura o ar."
    },
    "Acetato de Etila": {
        "mw": 88.11, "idlh": 2000, "lel": 2.0, "volatilidade": 0.8, 
        "desc": "Solvente comum (cheiro de removedor de esmalte). Muito inflamável, vapores viajam pelo chão."
    },
    "Acetona": {
        "mw": 58.08, "idlh": 2500, "lel": 2.5, "volatilidade": 0.6, 
        "desc": "Solvente padrão. Risco de incêndio alto, toxicidade aguda moderada."
    },
    "Acetonitrila": {
        "mw": 41.05, "idlh": 500, "lel": 3.0, "volatilidade": 0.7, 
        "desc": "Solvente de HPLC. Metaboliza-se em CIANETO no corpo horas após exposição."
    },
    "Ácido Acético (Solução)": {
        "mw": 60.05, "idlh": 50, "lel": 4.0, "volatilidade": 0.2, 
        "desc": "Vinagre concentrado. Vapores irritantes para olhos e nariz. Corrosivo."
    },
    "Ácido Acético Glacial": {
        "mw": 60.05, "idlh": 50, "lel": 4.0, "volatilidade": 0.4, 
        "desc": "Puro (>99%). Vapores sufocantes e inflamáveis acima de 39°C. Queimaduras severas."
    },
    "Ácido Clorídrico (Vapores HCl)": {
        "mw": 36.46, "idlh": 50, "lel": 0.0, "volatilidade": 0.8, 
        "desc": "Vapores brancos corrosivos. Destrói tecido pulmonar e corrói metais/eletrônicos."
    },
    "Ácido Nítrico (Fumegante)": {
        "mw": 63.01, "idlh": 25, "lel": 0.0, "volatilidade": 0.6, 
        "desc": "Oxidante enérgico. Inicia fogo em madeira/pano. Vapores vermelhos (NOx) causam edema pulmonar."
    },
    "Ácido Sulfúrico": {
        "mw": 98.08, "idlh": 15, "lel": 0.0, "volatilidade": 0.01, 
        "desc": "Não volátil. O perigo é contato direto ou névoa (spray). Gera calor violento com água."
    },
    "Acroleína": {
        "mw": 56.06, "idlh": 2, "lel": 2.8, "volatilidade": 0.9, 
        "desc": "Subproduto de incêndios. Lacrimogêneo potente e letal em dose ínfima."
    },
    "Amônia (25% ou Gás)": {
        "mw": 17.03, "idlh": 300, "lel": 15.0, "volatilidade": 0.9, 
        "desc": "Gás corrosivo. Perigo respiratório imediato (sufocamento). LEL alto, mas possível em espaços pequenos."
    },
    "Benzeno": {
        "mw": 78.11, "idlh": 500, "lel": 1.2, "volatilidade": 0.3, 
        "desc": "Carcinogênico Classe 1. Risco de explosão mesmo em vazamentos pequenos."
    },
    "Bromo (Líquido)": {
        "mw": 159.80, "idlh": 3, "lel": 0.0, "volatilidade": 0.7, 
        "desc": "Líquido vermelho fumegante. Queimaduras químicas graves. Toxidez aguda altíssima."
    },
    "Cianeto de Hidrogênio (HCN)": {
        "mw": 27.03, "idlh": 50, "lel": 5.6, "volatilidade": 1.0, 
        "desc": "EXTREMAMENTE TÓXICO. Cheiro de amêndoas. Ação fulminante (asfixia química)."
    },
    "Cloro Gás (Cl2)": {
        "mw": 70.90, "idlh": 10, "lel": 0.0, "volatilidade": 1.0, 
        "desc": "Oxidante forte. Corroi vias aéreas instantaneamente. Vapores verdes/amarelos."
    },
    "Clorofórmio": {
        "mw": 119.38, "idlh": 500, "lel": 0.0, "volatilidade": 0.5, 
        "desc": "Narcótico perigoso. Não explode, mas causa desmaio e morte silenciosa."
    },
    "Diclorometano (DCM)": {
        "mw": 84.93, "idlh": 2300, "lel": 13.0, "volatilidade": 0.9, 
        "desc": "Removedor de tintas. Metaboliza em Monóxido de Carbono no sangue. Narcótico."
    },
    "Disulfeto de Carbono": {
        "mw": 76.14, "idlh": 500, "lel": 1.3, "volatilidade": 1.0, 
        "desc": "PERIGO EXTREMO DE FOGO. Inflama a 90°C (lâmpada quente). Neurotóxico."
    },
    "Etanol (Álcool Etílico)": {
        "mw": 46.07, "idlh": 3300, "lel": 3.3, "volatilidade": 0.7, 
        "desc": "Inflamável comum. Risco principal é incêndio."
    },
    "Éter Etílico": {
        "mw": 74.12, "idlh": 1900, "lel": 1.9, "volatilidade": 1.0, 
        "desc": "Referência de evaporação. Vapores pesados descem para o chão e buscam tomadas."
    },
    "Formaldeído (Formol 37%)": {
        "mw": 30.03, "idlh": 20, "lel": 7.0, "volatilidade": 0.5, 
        "desc": "Fixador de tecidos. Irritante severo, sensibilizante e carcinogênico."
    },
    "Hidrazina": {
        "mw": 32.05, "idlh": 50, "lel": 4.7, "volatilidade": 0.2, 
        "desc": "Combustível de foguete. Hepatotóxico, carcinogênico e absorvido pela pele."
    },
    "Hidróxido de Sódio (Solução)": {
        "mw": 40.00, "idlh": 10, "lel": 0.0, "volatilidade": 0.01, 
        "desc": "Não volátil. Perigo é contato direto/respingo (Corrosivo). Não gera gás tóxico na sala."
    },
    "Isopropanol (IPA)": {
        "mw": 60.10, "idlh": 2000, "lel": 2.0, "volatilidade": 0.7, 
        "desc": "Álcool isopropílico. Vapores mais densos que o etanol."
    },
    "Mercúrio (Vapor)": {
        "mw": 200.59, "idlh": 1.2, "lel": 0.0, "volatilidade": 0.1, 
        "desc": "Metal líquido. Vapores invisíveis e inodoros causam danos neurológicos permanentes."
    },
    "Metanol": {
        "mw": 32.04, "idlh": 6000, "lel": 6.0, "volatilidade": 0.9, 
        "desc": "Chama invisível. Tóxico (cegueira) e absorvido pela pele."
    },
    "Metil Etil Cetona (MEK)": {
        "mw": 72.11, "idlh": 3000, "lel": 1.4, "volatilidade": 0.6, 
        "desc": "Similar à acetona, mas mais irritante. Vapores explosivos."
    },
    "Metil Isocianato (MIC)": {
        "mw": 57.05, "idlh": 3, "lel": 5.3, "volatilidade": 1.0, 
        "desc": "EXTREMO (Bhopal). Reage violentamente com água. Edema pulmonar em minutos."
    },
    "n-Hexano": {
        "mw": 86.18, "idlh": 1100, "lel": 1.1, "volatilidade": 0.9, 
        "desc": "Extremamente volátil. Vapores 'rastejam' longas distâncias (Flashback)."
    },
    "Óxido de Etileno": {
        "mw": 44.05, "idlh": 800, "lel": 3.0, "volatilidade": 1.0, 
        "desc": "Gás esterilizante. Cancerígeno, mutagênico e explosivo."
    },
    "Piridina": {
        "mw": 79.10, "idlh": 1000, "lel": 1.8, "volatilidade": 0.3, 
        "desc": "Odor nauseante. Afeta fígado e sistema nervoso. Inflamável."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "mw": 34.08, "idlh": 100, "lel": 4.0, "volatilidade": 1.0, 
        "desc": "Gás de esgoto. Cheiro de ovo podre que desaparece (anestesia olfativa) antes de matar."
    },
    "Tetrahidrofurano (THF)": {
        "mw": 72.11, "idlh": 2000, "lel": 2.0, "volatilidade": 0.9, 
        "desc": "Solvente de polímeros. Altamente inflamável. Forma peróxidos explosivos se seco."
    },
    "Tolueno": {
        "mw": 92.14, "idlh": 500, "lel": 1.1, "volatilidade": 0.5, 
        "desc": "Solvente de tintas. Narcótico forte, causa confusão mental rápida."
    },
    "Xileno": {
        "mw": 106.16, "idlh": 900, "lel": 1.1, "volatilidade": 0.4, 
        "desc": "Solvente aromático. Inflamável e neurotóxico."
    },
    "Acetato de Butila": {
        "mw": 116.16, "idlh": 1700, "lel": 1.2, "volatilidade": 0.5, 
        "desc": "Solvente de tintas e vernizes. Vapores pesados que se acumulam no chão. Irritante moderado."
    },
    "Acrilonitrila": {
        "mw": 53.06, "idlh": 85, "lel": 3.0, "volatilidade": 0.8, 
        "desc": "Monômero para plásticos. Carcinogênico. Metaboliza em cianeto no corpo (efeito retardado). Extremamente inflamável."
    },
    "Cloreto de Metileno": {
        "mw": 84.93, "idlh": 2300, "lel": 13.0, "volatilidade": 0.9, 
        "desc": "Removedor de tintas e desengraxante. Metaboliza em monóxido de carbono no sangue. Narcótico e hepatotóxico."
    },
    "Éter de Petróleo": {
        "mw": 100.20, "idlh": 1400, "lel": 1.1, "volatilidade": 1.0, 
        "desc": "Mistura de hidrocarbonetos leves. Extremamente volátil e inflamável. Vapores viajam longas distâncias."
    },
    "Fenol": {
        "mw": 94.11, "idlh": 250, "lel": 1.8, "volatilidade": 0.3, 
        "desc": "Desinfetante e precursor químico. Corrosivo, tóxico e absorvido pela pele. Vapores irritantes."
    },
    "Formamida": {
        "mw": 45.04, "idlh": 200, "lel": 0.0, "volatilidade": 0.2, 
        "desc": "Solvente polar. Teratogênico (causa malformações fetais). Absorvido pela pele. Baixa volatilidade."
    },
    "Glicol de Etileno": {
        "mw": 62.07, "idlh": 0, "lel": 3.2, "volatilidade": 0.1, 
        "desc": "Anticongelante. Baixa volatilidade, mas vapores podem se acumular em ambientes quentes. Tóxico se ingerido."
    },
    "Hidroquinona": {
        "mw": 110.11, "idlh": 50, "lel": 0.0, "volatilidade": 0.05, 
        "desc": "Revelador fotográfico. Pó fino que pode formar aerossol. Tóxico, sensibilizante e pode causar despigmentação."
    },
    "Metil Acrilato": {
        "mw": 86.09, "idlh": 250, "lel": 2.8, "volatilidade": 0.7, 
        "desc": "Monômero para resinas acrílicas. Irritante severo para olhos e pulmões. Inflamável."
    },
    "N,N-Dimetilformamida (DMF)": {
        "mw": 73.09, "idlh": 500, "lel": 2.2, "volatilidade": 0.3, 
        "desc": "Solvente polar aprotônico. Hepatotóxico e teratogênico. Absorvido pela pele. Vapores moderadamente voláteis."
    },
    "Percloroetileno (PCE)": {
        "mw": 165.83, "idlh": 150, "lel": 10.8, "volatilidade": 0.6, 
        "desc": "Lavagem a seco. Vapores pesados. Carcinogênico provável. Neurotóxico e hepatotóxico."
    },
    "Propilenoglicol": {
        "mw": 76.10, "idlh": 0, "lel": 2.6, "volatilidade": 0.05, 
        "desc": "Umectante e solvente. Baixíssima volatilidade. Baixa toxicidade aguda, mas pode causar irritação."
    },
    "Tetracloroetileno": {
        "mw": 165.83, "idlh": 150, "lel": 10.8, "volatilidade": 0.6, 
        "desc": "Lavagem a seco. Vapores pesados que se acumulam. Carcinogênico provável. Neurotóxico."
    },
    "Trimetilamina": {
        "mw": 59.11, "idlh": 200, "lel": 2.0, "volatilidade": 0.9, 
        "desc": "Gás com cheiro de peixe podre. Irritante severo para olhos e vias respiratórias. Inflamável."
    }
}


    


# =============================================================================
# 2. MOTOR DE CÁLCULO (BOX MODEL / EQUAÇÃO DIFERENCIAL ORDINÁRIA)
# =============================================================================
# Baseado em: Box Model (Well-Mixed Room Model), Balanço de Massa
# Referências: EPA Indoor Air Quality Models, ASHRAE Standards
# O modelo assume: sala bem misturada (concentração uniforme), ventilação constante,
# evaporação contínua da poça, sem reações químicas
def simular_vazamento_indoor(vol_sala, ach, massa_derramada_kg, area_poca, volat_fator):
    """
    Simula a evolução temporal da concentração de vapor em ambiente confinado.
    
    Utiliza o modelo de Box (Well-Mixed Room Model) com balanço de massa:
    dC/dt = (Geração - Remoção) / Volume
    
    Onde:
    - Geração = Taxa de evaporação da poça (g/s)
    - Remoção = Taxa de remoção por ventilação (g/s)
    - Volume = Volume da sala (m³)
    
    Parâmetros:
    - vol_sala: Volume da sala em m³
    - ach: Air Changes per Hour (trocas de ar por hora)
    - massa_derramada_kg: Massa total derramada em kg
    - area_poca: Área da poça de líquido em m²
    - volat_fator: Fator de volatilidade (0.0 a 1.0)
    
    Retorna:
    - tempo: Array de tempos em segundos
    - concentracao: Array de concentrações em g/m³
    - dados_detalhados: DataFrame com informações detalhadas
    """
    massa_total_g = massa_derramada_kg * 1000.0  # Conversão kg -> g
    
    # Estimativa de Taxa de Evaporação (Modelo Kawamura simplificado)
    # Taxa base: 5.0 g/s/m² para produtos muito voláteis (fator 1.0)
    # A taxa real é proporcional ao fator de volatilidade
    taxa_evap_base = 5.0 * volat_fator  # g/s/m²
    
    # Vazão de ventilação (m³/s)
    # ACH = trocas de ar por hora
    # Vazão = (ACH * Volume) / 3600 s/h
    q_vent = (ach * vol_sala) / 3600.0  # m³/s
    
    # Configuração do tempo de simulação
    dt = 1.0        # Passo de tempo: 1 segundo
    t_max = 1800    # Tempo máximo: 30 minutos (1800 segundos)
    tempo = np.arange(0, t_max, dt)
    
    concentracao_hist = [] 
    massa_evaporada_hist = []
    conc_atual = 0.0  # Concentração inicial: 0 g/m³
    massa_restante = massa_total_g
    
    # Integração numérica (Método de Euler)
    for t in tempo:
        # 1. Geração (Evaporação da poça)
        if massa_restante > 0:
            geracao = taxa_evap_base * area_poca * dt  # g
            # Limitar geração à massa restante
            if geracao > massa_restante: 
                geracao = massa_restante
            massa_restante -= geracao
        else:
            geracao = 0.0  # Poça totalmente evaporada
            
        # 2. Remoção (Ventilação)
        # Taxa de remoção = Concentração × Vazão de ventilação
        remocao = conc_atual * q_vent * dt  # g
        
        # 3. Atualização do estado (Balanço de Massa)
        # dC/dt = (Geração - Remoção) / Volume
        conc_atual += (geracao - remocao) / vol_sala
        if conc_atual < 0: 
            conc_atual = 0  # Não pode ser negativo
        
        concentracao_hist.append(conc_atual)
        massa_evaporada_hist.append(massa_total_g - massa_restante)
    
    # Criar DataFrame com dados detalhados
    dados_detalhados = pd.DataFrame({
        'Tempo (s)': tempo,
        'Tempo (min)': tempo / 60.0,
        'Concentração (g/m³)': concentracao_hist,
        'Massa Evaporada (g)': massa_evaporada_hist,
        'Massa Restante (g)': [massa_total_g - m for m in massa_evaporada_hist]
    })
    
    return tempo, np.array(concentracao_hist), dados_detalhados

def converter_limites(mw, idlh_ppm, lel_perc):
    """
    Converte limites de concentração da FISPQ para unidades consistentes.
    
    Conversões:
    - IDLH: ppm (partes por milhão) -> g/m³
    - LEL: % (porcentagem em volume) -> g/m³
    
    Fórmulas:
    - g/m³ = (ppm × MW) / 24.45 (a 25°C e 1 atm)
    - 1% = 10,000 ppm
    
    Parâmetros:
    - mw: Massa molecular (g/mol)
    - idlh_ppm: IDLH em ppm
    - lel_perc: LEL em porcentagem
    
    Retorna:
    - limite_idlh_gm3: IDLH em g/m³ (ou None se não aplicável)
    - limite_lel_gm3: LEL em g/m³ (ou None se não aplicável)
    """
    # Conversão IDLH (ppm -> g/m³)
    # Fórmula: g/m³ = (ppm × MW) / 24.45
    # Onde 24.45 = volume molar a 25°C e 1 atm (L/mol)
    limite_idlh_gm3 = (idlh_ppm * mw) / 24.45 if idlh_ppm > 0 else None
    
    # Conversão LEL (% -> g/m³)
    # 1% = 10,000 ppm
    # g/m³ = (ppm × MW) / 24.45 = ((% × 10,000) × MW) / 24.45
    limite_lel_gm3 = (lel_perc * 10000.0 * mw) / 24.45 if lel_perc > 0 else None
    
    return limite_idlh_gm3, limite_lel_gm3

# =============================================================================
# 3. INTERFACE VISUAL (FRONT-END)
# =============================================================================
def renderizar():
    st.title("Contaminação de Ambientes Confinados")
    st.markdown("**Modelagem de saturação de ambientes confinados utilizando Box Model (Well-Mixed Room Model)**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos Teóricos e Conceitos Operacionais", expanded=True):
        st.markdown("""
        #### O Conceito: Balanço de Massa em Ambiente Confinado
        
        Quando um líquido volátil é derramado em um ambiente fechado, ele evapora continuamente, gerando vapores que se misturam com o ar. Simultaneamente, a ventilação remove parte desses vapores. O modelo de Box (Well-Mixed Room Model) descreve essa dinâmica através de um balanço de massa:
        
        **dC/dt = (Geração - Remoção) / Volume**
        
        Onde:
        - **Geração:** Taxa de evaporação da poça (g/s)
        - **Remoção:** Taxa de remoção por ventilação (g/s)
        - **Volume:** Volume da sala (m³)
        
        É uma "corrida contra o tempo": se a geração superar a remoção, a concentração aumenta até atingir níveis perigosos.
        
        #### Parâmetros Críticos
        
        **1. ACH (Air Changes per Hour - Trocas de Ar por Hora):**
        Mede a eficiência da ventilação. Valores típicos:
        * **0.5 ACH:** Sala fechada com ar condicionado split. Ventilação muito baixa. Gases ficam presos e se acumulam rapidamente.
        * **2.0 a 4.0 ACH:** Escritório com janelas abertas ou sistema de ar central comum. Ventilação moderada.
        * **10.0 a 20.0 ACH:** Laboratório químico com exaustão profissional ativa. Padrão de segurança para manipulação de produtos químicos.
        * **> 20.0 ACH:** Salas de processamento químico ou áreas com risco extremo. Ventilação muito alta.
        
        **2. LEL (Lower Explosive Limit - Limite Inferior de Explosão):**
        Concentração mínima de vapor no ar (em % em volume) necessária para formar uma mistura explosiva. Se a concentração atingir o LEL:
        * Qualquer fonte de ignição (luz, interruptor, equipamento elétrico) pode causar explosão
        * A sala inteira pode explodir instantaneamente
        * É um risco crítico que requer evacuação imediata
        
        **3. IDLH (Immediately Dangerous to Life or Health):**
        Concentração (em ppm) acima da qual a exposição pode causar:
        * Morte ou efeitos irreversíveis à saúde
        * Incapacitação que impede a fuga
        * Entrada proibida sem Equipamento de Respiração Autônoma (ERA)
        
        **4. Volatilidade:**
        Fator que determina a velocidade de evaporação:
        * **1.0:** Muito volátil (éter, acetona) - evapora rapidamente
        * **0.5:** Moderadamente volátil (álcool, tolueno)
        * **0.1:** Pouco volátil (óleos, diesel) - evapora lentamente
        
        #### Como Usar Dados da FISPQ (Modo Personalizado)
        
        Se a substância não está na lista, selecione **"Outro (Personalizado)"** e consulte a Ficha de Informação de Segurança de Produtos Químicos (FISPQ):
        * **Peso Molecular (MW):** Seção 9 - Propriedades Físicas e Químicas
        * **LEL (%):** Seção 9 - Propriedades de Inflamabilidade. Se "Não Aplicável" ou "Não Inflamável", coloque 0.
        * **IDLH (ppm):** Seção 11 - Informações Toxicológicas. Se não disponível, consulte NIOSH Pocket Guide.
        * **Volatilidade:** Estime baseado na pressão de vapor ou compare com substâncias similares.
        
        #### Limitações do Modelo
        
        Este modelo utiliza simplificações para fins didáticos e operacionais:
        * Assume sala bem misturada (concentração uniforme em todo o espaço)
        * Não considera estratificação térmica ou diferenças de densidade
        * Assume ventilação constante e uniforme
        * Não modela reações químicas ou decomposição
        * Não considera adsorção em superfícies ou materiais porosos
        * Assume evaporação contínua (não considera mudanças de temperatura)
        
        Para análises detalhadas, utilize modelos CFD (Computational Fluid Dynamics) ou software especializado.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Geometria e Ventilação do Ambiente")
        vol = st.number_input("Volume da Sala (m³)", value=40.0, min_value=1.0, 
                              help="Volume total do ambiente confinado. Calcule: Largura × Comprimento × Altura. Exemplo: 4 m × 4 m × 2.5 m = 40 m³.")
        ach = st.number_input("Ventilação (ACH - Trocas de Ar por Hora)", value=2.0, min_value=0.0, step=0.5, 
                             help="Número de vezes que o ar é completamente renovado por hora. Valores típicos: 0.5 (ruim), 2-4 (moderado), 10-20 (bom para laboratórios).")
        
        # Seleção Híbrida (Lista ou Manual)
        lista_opcoes = list(SUBSTANCIAS_INDOOR.keys()) + ["Outro (Personalizado)"]
        selecao = st.selectbox("Substância Química Vazada", lista_opcoes, 
                              help="Selecione da lista ou escolha 'Personalizado' para inserir dados da FISPQ.")

    with col2:
        st.subheader("Características do Vazamento")
        massa_kg = st.number_input("Massa Derramada (kg)", value=1.0, min_value=0.1, step=0.1, 
                                   help="Quantidade total de líquido derramado. Para líquidos, 1 litro ≈ 1 kg (densidade próxima de 1).")
        area = st.number_input("Área da Poça (m²)", value=2.0, min_value=0.1, step=0.5, 
                              help="Área ocupada pela poça de líquido no chão. Poças espalhadas (área grande) evaporam mais rápido que poças contidas (área pequena).")

    # --- LÓGICA DE INPUT MANUAL VS AUTOMÁTICO ---
    if selecao == "Outro (Personalizado)":
        st.info("**Modo Manual:** Insira os dados da Seção 9 e 11 da FISPQ do produto.")
        c_a, c_b, c_c, c_d = st.columns(4)
        mw_in = c_a.number_input("Peso Molecular (g/mol)", value=100.0, min_value=1.0,
                                help="Massa molecular da substância. Seção 9 da FISPQ.")
        lel_in = c_b.number_input("LEL (%)", value=0.0, step=0.1, 
                                  help="Limite Inferior de Explosão em porcentagem. Coloque 0 se não for inflamável.")
        idlh_in = c_c.number_input("IDLH (ppm)", value=500.0, step=50.0,
                                   help="Concentração imediatamente perigosa à vida ou saúde. Seção 11 da FISPQ ou NIOSH Pocket Guide.")
        volat_in = c_d.slider("Volatilidade (Fator)", 0.1, 1.0, 0.5, 
                             help="Fator de volatilidade: 1.0 = muito volátil (éter, acetona); 0.1 = pouco volátil (óleos, diesel).")
        
        # Consolida dados manuais
        dados_ativos = {"mw": mw_in, "lel": lel_in, "idlh": idlh_in, "volatilidade": volat_in, "nome": "Substância Personalizada"}
    else:
        # Busca dados do dicionário
        d = SUBSTANCIAS_INDOOR[selecao]
        dados_ativos = {"mw": d['mw'], "lel": d['lel'] if d['lel'] else 0, "idlh": d['idlh'], "volatilidade": d['volatilidade'], "nome": selecao}
        st.info(f"**Descrição:** {d['desc']}")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"**Massa Molecular:** {d['mw']:.2f} g/mol")
            st.caption(f"**LEL:** {d['lel']:.1f}%")
        with col_info2:
            st.caption(f"**IDLH:** {d['idlh']:.0f} ppm")
            st.caption(f"**Volatilidade:** {d['volatilidade']:.1f}")

    st.markdown("---")
    
    # Botão de Execução
    if 'indoor_calc' not in st.session_state: 
        st.session_state['indoor_calc'] = False
    if st.button("SIMULAR EVOLUÇÃO DA ATMOSFERA", type="primary", use_container_width=True):
        st.session_state['indoor_calc'] = True

    # =========================================================================
    # 4. RESULTADOS E DIAGNÓSTICO
    # =========================================================================
    if st.session_state['indoor_calc']:
        # Extrair dados para cálculo
        fator_volat = dados_ativos['volatilidade']
        mw_val = dados_ativos['mw']
        lel_val = dados_ativos['lel']
        idlh_val = dados_ativos['idlh']
        nome_display = dados_ativos['nome']

        # Rodar Simulação
        t_seg, conc_gm3, df_detalhado = simular_vazamento_indoor(vol, ach, massa_kg, area, fator_volat)
        lim_idlh, lim_lel = converter_limites(mw_val, idlh_val, lel_val)
        
        t_min = t_seg / 60.0
        max_conc = np.max(conc_gm3)
        
        # Encontrar tempos de cruzamento dos limites
        tempo_lel = None
        tempo_idlh = None
        if lim_lel and np.any(conc_gm3 > lim_lel):
            tempo_lel = t_min[np.argmax(conc_gm3 > lim_lel)]
        if lim_idlh and np.any(conc_gm3 > lim_idlh):
            tempo_idlh = t_min[np.argmax(conc_gm3 > lim_idlh)]

        # --- A. DIAGNÓSTICO ---
        st.markdown("### Diagnóstico Operacional")
        
        cruzou_lel = lim_lel and max_conc > lim_lel
        cruzou_idlh = lim_idlh and max_conc > lim_idlh
        
        # Métricas principais
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
            st.metric("Concentração Máxima", f"{max_conc:.2f} g/m³",
                     help="Concentração máxima atingida durante a simulação")
        with col_met2:
            tempo_max = t_min[np.argmax(conc_gm3)]
            st.metric("Tempo até Máximo", f"{tempo_max:.1f} min",
                     help="Tempo necessário para atingir a concentração máxima")
        with col_met3:
            if lim_lel:
                st.metric("LEL", f"{lim_lel:.2f} g/m³",
                         help="Limite Inferior de Explosão")
            else:
                st.metric("LEL", "N/A", help="Substância não inflamável")
        with col_met4:
            if lim_idlh:
                st.metric("IDLH", f"{lim_idlh:.2f} g/m³",
                         help="Concentração imediatamente perigosa à vida ou saúde")
            else:
                st.metric("IDLH", "N/A", help="IDLH não disponível")
        
        st.markdown("---")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("#### Risco de Explosão (LEL)")
            if cruzou_lel:
                st.error(f"**CRÍTICO: AMBIENTE EXPLOSIVO**\n\nO ambiente atinge o limite de explosão em **{tempo_lel:.1f} minutos**.\n\n**AÇÕES IMEDIATAS:**\n- Evacuar imediatamente todas as pessoas\n- Não acionar interruptores, equipamentos elétricos ou fontes de ignição\n- Ventilação insuficiente - aumentar ACH ou usar ventilação forçada\n- Área deve ser considerada zona de risco de explosão")
            elif lim_lel:
                if max_conc > (lim_lel * 0.5):
                    st.warning(f"**ALERTA:** Concentração elevada ({max_conc/lim_lel*100:.0f}% do LEL). Risco de explosão se concentração continuar aumentando.")
                else:
                    st.success(f"**SEGURO:** Concentração não atinge o LEL (máximo: {max_conc/lim_lel*100:.0f}% do LEL)")
            else:
                st.info("**Substância não inflamável:** Não há risco de explosão por esta substância.")

        with col_d2:
            st.markdown("#### Risco Toxicológico (IDLH)")
            if cruzou_idlh:
                st.error(f"**LETAL: AMBIENTE MORTAL**\n\nO ambiente atinge concentração letal em **{tempo_idlh:.1f} minutos**.\n\n**AÇÕES IMEDIATAS:**\n- Evacuar imediatamente todas as pessoas\n- Entrada proibida sem Equipamento de Respiração Autônoma (ERA)\n- Área deve ser considerada zona quente (Hot Zone)\n- Ventilação insuficiente - aumentar ACH drasticamente")
            elif lim_idlh and max_conc > (lim_idlh * 0.1):
                percentual = (max_conc / lim_idlh) * 100
                st.warning(f"**ALERTA TÓXICO:** Concentração elevada ({percentual:.0f}% do IDLH). Uso obrigatório de proteção respiratória adequada.")
            elif lim_idlh:
                st.success(f"**RESPIRÁVEL:** Concentração abaixo de níveis perigosos (máximo: {max_conc/lim_idlh*100:.0f}% do IDLH)")
            else:
                st.info("**IDLH não disponível:** Consulte FISPQ ou NIOSH Pocket Guide para limites de exposição.")

        # --- B. GRÁFICO ---
        st.markdown("---")
        st.markdown("### Evolução Temporal da Concentração")
        
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(t_min, conc_gm3, color='#000080', linewidth=3, label="Concentração na Sala (g/m³)")
        ax.fill_between(t_min, conc_gm3, alpha=0.15, color='#000080')
        
        # Linha LEL
        if lim_lel:
            ax.axhline(lim_lel, color='red', linestyle='--', linewidth=2.5, label=f'LEL: {lim_lel:.2f} g/m³')
            ax.text(0.5, lim_lel*1.02, f' Limite de Explosão (LEL): {lim_lel:.2f} g/m³', 
                   color='red', fontweight='bold', fontsize=10, 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
        # Linha IDLH
        if lim_idlh:
            ax.axhline(lim_idlh, color='orange', linestyle='--', linewidth=2.5, label=f'IDLH: {lim_idlh:.2f} g/m³')
            offset = 1.02 if not lim_lel or abs(lim_lel - lim_idlh) > (lim_lel*0.1) else 0.95
            ax.text(0.5, lim_idlh*offset, f' Perigo à Vida (IDLH): {lim_idlh:.2f} g/m³', 
                   color='#CC7000', fontweight='bold', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        ax.set_xlabel('Tempo (minutos)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Concentração (g/m³)', fontsize=12, fontweight='bold')
        ax.set_title(f'Evolução da Concentração: {nome_display}\nVolume: {vol} m³ | Ventilação: {ach} ACH', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='upper right', fontsize=10)
        
        # Ajuste de escala Y para não cortar os textos
        max_y = max(max_conc, lim_lel if lim_lel else 0, lim_idlh if lim_idlh else 0)
        ax.set_ylim(0, max_y * 1.3)

        st.pyplot(fig)
        
        # Tabela detalhada (amostra)
        st.markdown("---")
        st.markdown("### Dados Detalhados da Simulação")
        st.caption("Tabela com evolução temporal da concentração e massa evaporada")
        st.dataframe(df_detalhado[['Tempo (min)', 'Concentração (g/m³)', 'Massa Evaporada (g)', 'Massa Restante (g)']].head(20), 
                    use_container_width=True, hide_index=True)
        
        # Informações técnicas
        st.markdown("---")
        st.markdown("### Informações Técnicas")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"""
            **Substância:** {nome_display}  
            **Massa Molecular:** {mw_val:.2f} g/mol  
            **Massa Derramada:** {massa_kg:.2f} kg  
            **Área da Poça:** {area:.2f} m²  
            **Fator de Volatilidade:** {fator_volat:.2f}
            """)
        with col_info2:
            taxa_evap = 5.0 * fator_volat * area
            vazao_vent = (ach * vol) / 3600.0
            st.markdown(f"""
            **Volume da Sala:** {vol:.1f} m³  
            **Ventilação (ACH):** {ach:.1f} trocas/hora  
            **Taxa de Evaporação:** {taxa_evap:.2f} g/s  
            **Vazão de Ventilação:** {vazao_vent:.3f} m³/s
            """)
        
        # Recomendações Operacionais
        st.markdown("---")
        st.markdown("### Recomendações Operacionais")
        
        if cruzou_lel or cruzou_idlh:
            st.error("""
            **AÇÕES IMEDIATAS CRÍTICAS:**
            1. Evacuar imediatamente todas as pessoas do ambiente
            2. Isolar a área e estabelecer perímetro de segurança
            3. Não acionar interruptores, equipamentos elétricos ou fontes de ignição
            4. Aumentar ventilação drasticamente (abrir portas, janelas, ativar exaustores)
            5. Entrada permitida apenas com Equipamento de Respiração Autônoma (ERA) e traje de proteção química
            6. Monitorar continuamente a concentração com detectores de gás
            7. Coordenar com equipes de emergência química
            """)
        else:
            st.warning("""
            **AÇÕES PREVENTIVAS:**
            1. Monitorar continuamente a concentração com detectores de gás
            2. Manter ventilação adequada (considerar aumentar ACH se próximo dos limites)
            3. Usar proteção respiratória adequada se concentração estiver elevada
            4. Limitar tempo de permanência no ambiente
            5. Considerar evacuação preventiva se condições piorarem
            """)
        
        st.info("""
        **CONSIDERAÇÕES TÉCNICAS:**
        - Este modelo é uma aproximação simplificada. Condições reais podem variar significativamente.
        - Concentrações podem variar espacialmente (estratificação, correntes de ar).
        - Mudanças de temperatura afetam a taxa de evaporação.
        - Reações químicas ou decomposição podem alterar a composição dos vapores.
        - Consulte especialistas em segurança química para análises detalhadas.
        - Utilize detectores de gás para monitoramento em tempo real.
        """)