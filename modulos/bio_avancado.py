import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. BANCO DE DADOS: AGENTES BIOLÓGICOS COM PARÂMETROS SEIR-A
# =============================================================================
# Modelo SEIR-A: Susceptible-Exposed-Infectious (Symptomatic)-Asymptomatic-Recovered
# Baseado em: Kermack-McKendrick Model, Epidemiologia Matemática Avançada
# Parâmetros:
# - R0: Número Reprodutivo Básico
# - sigma: Taxa de progressão de exposto para infectado (1/tempo_incubacao)
# - gamma: Taxa de recuperação (1/tempo_recuperacao)
# - alpha: Redução de infectividade de assintomáticos (0-1)
# - p_assintomatico: Proporção de infectados que permanecem assintomáticos
AGENTES_BIO_AVANCADO = {
    "COVID-19 (SARS-CoV-2)": {
        "tipo": "Vírus (Coronavírus)",
        "R0": 2.5,
        "sigma": 1/5.2,  # Inverso do tempo de incubação (dias)
        "gamma": 1/7,  # Inverso do tempo de recuperação (dias)
        "alpha": 0.5,  # Redução de infectividade de assintomáticos
        "p_assintomatico": 0.4,  # Proporção de assintomáticos
        "letalidade": 0.01,
        "desc": "Pandemia global. Transmissão por gotículas e aerossóis. Alta proporção de assintomáticos."
    },
    "Varíola (Smallpox)": {
        "tipo": "Vírus (Poxvírus)",
        "R0": 5.0,
        "sigma": 1/12,
        "gamma": 1/21,
        "alpha": 0.3,
        "p_assintomatico": 0.05,
        "letalidade": 0.30,
        "desc": "Eradicada, mas risco de bioterrorismo. Altamente contagiosa e letal. Vacina disponível."
    },
    "Sarampo (Measles)": {
        "tipo": "Vírus (Paramyxovírus)",
        "R0": 15.0,
        "sigma": 1/10,
        "gamma": 1/7,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.001,
        "desc": "Extremamente contagioso. R0 mais alto que qualquer doença conhecida. Vacina eficaz."
    },
    "Gripe Aviária (H5N1)": {
        "tipo": "Vírus (Influenza)",
        "R0": 1.5,
        "sigma": 1/3,
        "gamma": 1/7,
        "alpha": 0.4,
        "p_assintomatico": 0.3,
        "letalidade": 0.60,
        "desc": "Baixa transmissibilidade pessoa-pessoa, mas letalidade extrema se adaptar."
    },
    "Ebola (Zaire)": {
        "tipo": "Vírus (Filovírus)",
        "R0": 2.0,
        "sigma": 1/8,
        "gamma": 1/10,
        "alpha": 0.1,
        "p_assintomatico": 0.05,
        "letalidade": 0.50,
        "desc": "Febre hemorrágica. Transmissão por fluidos corporais. Alto risco em ambientes hospitalares."
    },
    "Peste Pneumônica (Yersinia pestis)": {
        "tipo": "Bactéria",
        "R0": 1.8,
        "sigma": 1/2,
        "gamma": 1/5,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.90,
        "desc": "Forma pulmonar da peste. Transmissão por gotículas. Letalidade extrema sem tratamento."
    },
    "Tularemia (Francisella tularensis)": {
        "tipo": "Bactéria",
        "R0": 0.0,
        "sigma": 1/5,
        "gamma": 1/14,
        "alpha": 0.0,
        "p_assintomatico": 0.0,
        "letalidade": 0.05,
        "desc": "Não contagiosa pessoa-pessoa. Transmissão por aerossóis ou vetores. Incapacitante."
    },
    "OUTRAS (Entrada Manual)": {
        "tipo": "Vírus/Bactéria",
        "R0": 2.0,
        "sigma": 1/5,
        "gamma": 1/7,
        "alpha": 0.5,
        "p_assintomatico": 0.3,
        "letalidade": 0.01,
        "desc": "Configure manualmente os parâmetros do agente."
    },
    "Influenza A (H1N1) Pandêmica": {
        "tipo": "Vírus (Influenza)",
        "R0": 1.8,
        "sigma": 1/2,
        "gamma": 1/7,
        "alpha": 0.4,
        "p_assintomatico": 0.3,
        "letalidade": 0.01,
        "desc": "Gripe pandêmica. Alta transmissibilidade. Pode causar colapso do sistema de saúde pelo volume de casos."
    },
    "MERS-CoV": {
        "tipo": "Vírus (Coronavírus)",
        "R0": 0.7,
        "sigma": 1/5,
        "gamma": 1/14,
        "alpha": 0.3,
        "p_assintomatico": 0.2,
        "letalidade": 0.35,
        "desc": "Síndrome Respiratória do Oriente Médio. Alta letalidade. Transmissão limitada pessoa-pessoa."
    },
    "SARS-CoV-1": {
        "tipo": "Vírus (Coronavírus)",
        "R0": 2.5,
        "sigma": 1/5,
        "gamma": 1/10,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.10,
        "desc": "Síndrome Respiratória Aguda Grave. Contida em 2003. Alta letalidade em idosos."
    },
    "Norovírus": {
        "tipo": "Vírus",
        "R0": 4.0,
        "sigma": 1/1,
        "gamma": 1/2,
        "alpha": 0.3,
        "p_assintomatico": 0.2,
        "letalidade": 0.001,
        "desc": "Altamente contagioso. Causa gastroenterite severa. Resistente a desinfetantes. Contaminação de alimentos."
    },
    "Rotavírus": {
        "tipo": "Vírus",
        "R0": 3.5,
        "sigma": 1/2,
        "gamma": 1/5,
        "alpha": 0.4,
        "p_assintomatico": 0.3,
        "letalidade": 0.001,
        "desc": "Causa gastroenterite severa em crianças. Altamente contagioso. Vacina disponível."
    },
    "Shigella dysenteriae": {
        "tipo": "Bactéria",
        "R0": 2.5,
        "sigma": 1/2,
        "gamma": 1/7,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.10,
        "desc": "Disenteria bacilar. Contaminação fecal-oral. Requer poucas bactérias para infectar. Risco de contaminação de água."
    },
    "Salmonella Typhi": {
        "tipo": "Bactéria",
        "R0": 2.8,
        "sigma": 1/10,
        "gamma": 1/14,
        "alpha": 0.3,
        "p_assintomatico": 0.2,
        "letalidade": 0.15,
        "desc": "Febre Tifoide. Contaminação de água e alimentos. Portadores assintomáticos podem transmitir por meses."
    },
    "Cólera (Vibrio cholerae)": {
        "tipo": "Bactéria",
        "R0": 2.5,
        "sigma": 1/2,
        "gamma": 1/5,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.50,
        "desc": "Ameaça à água potável. Diarreia severa leva à morte por desidratação em horas. Contágio fecal-oral."
    },
    "Difteria (Corynebacterium diphtheriae)": {
        "tipo": "Bactéria",
        "R0": 2.0,
        "sigma": 1/5,
        "gamma": 1/14,
        "alpha": 0.3,
        "p_assintomatico": 0.2,
        "letalidade": 0.10,
        "desc": "Transmissão por gotículas. Forma pseudomembrana na garganta. Vacina disponível (DTP)."
    },
    "Coqueluche (Bordetella pertussis)": {
        "tipo": "Bactéria",
        "R0": 5.5,
        "sigma": 1/7,
        "gamma": 1/21,
        "alpha": 0.4,
        "p_assintomatico": 0.3,
        "letalidade": 0.001,
        "desc": "Tosse convulsa. Altamente contagiosa. Perigosa para bebês. Vacina disponível (DTP)."
    },
    "Rubéola": {
        "tipo": "Vírus",
        "R0": 6.0,
        "sigma": 1/14,
        "gamma": 1/7,
        "alpha": 0.5,
        "p_assintomatico": 0.5,
        "letalidade": 0.001,
        "desc": "Altamente contagiosa. Perigosa para fetos (síndrome da rubéola congênita). Vacina disponível (MMR)."
    },
    "Caxumba": {
        "tipo": "Vírus",
        "R0": 4.5,
        "sigma": 1/16,
        "gamma": 1/10,
        "alpha": 0.3,
        "p_assintomatico": 0.3,
        "letalidade": 0.001,
        "desc": "Parotidite. Altamente contagiosa. Pode causar orquite e meningite. Vacina disponível (MMR)."
    },
    "Varicela (Catapora)": {
        "tipo": "Vírus",
        "R0": 8.0,
        "sigma": 1/14,
        "gamma": 1/10,
        "alpha": 0.2,
        "p_assintomatico": 0.1,
        "letalidade": 0.001,
        "desc": "Altamente contagiosa. Transmissão por gotículas e contato direto. Vacina disponível."
    },
    "Mononucleose (EBV)": {
        "tipo": "Vírus",
        "R0": 1.5,
        "sigma": 1/30,
        "gamma": 1/21,
        "alpha": 0.6,
        "p_assintomatico": 0.5,
        "letalidade": 0.001,
        "desc": "Doença do beijo. Transmissão por saliva. Alta proporção de assintomáticos. Incapacitante."
    }
}

# Persistência em Superfícies (Taxa de Decaimento k em 1/hora)
# Fonte: Estudos de laboratório (van Doremalen et al., Kampf et al., etc.)
# Modelo: C(t) = C₀ × exp(-k × t)
# Onde k é ajustado por umidade e temperatura
PERSISTENCIA_FOMITES = {
    "Aço Inoxidável": {
        "k_base": 0.05,  # 1/hora (base)
        "fator_umidade": 0.8,  # Reduz com alta umidade
        "fator_temp": 1.2,  # Aumenta com temperatura
        "desc": "Superfície comum em hospitais. Persistência média."
    },
    "Plástico (Polipropileno)": {
        "k_base": 0.04,
        "fator_umidade": 0.9,
        "fator_temp": 1.3,
        "desc": "Equipamentos médicos, embalagens. Persistência alta."
    },
    "Papel/Cartão": {
        "k_base": 0.08,
        "fator_umidade": 0.6,
        "fator_temp": 1.5,
        "desc": "Documentos, caixas. Persistência baixa (absorve umidade)."
    },
    "Tecido/Algodão": {
        "k_base": 0.10,
        "fator_umidade": 0.5,
        "fator_temp": 1.4,
        "desc": "Roupas, lençóis. Persistência baixa."
    },
    "Vidro": {
        "k_base": 0.03,
        "fator_umidade": 0.95,
        "fator_temp": 1.1,
        "desc": "Janelas, telas. Persistência muito alta."
    },
    "Cobre": {
        "k_base": 0.20,
        "fator_umidade": 1.0,
        "fator_temp": 1.0,
        "desc": "Superfície antimicrobiana natural. Persistência muito baixa."
    },
    "Alumínio": {
        "k_base": 0.06,
        "fator_umidade": 0.85,
        "fator_temp": 1.25,
        "desc": "Superfície comum em equipamentos. Persistência moderada."
    },
    "Borracha/Silicone": {
        "k_base": 0.05,
        "fator_umidade": 0.9,
        "fator_temp": 1.2,
        "desc": "Equipamentos médicos, selos. Persistência alta."
    },
    "Madeira": {
        "k_base": 0.12,
        "fator_umidade": 0.4,
        "fator_temp": 1.6,
        "desc": "Móveis, estruturas. Absorve umidade. Persistência baixa."
    },
    "Aço Galvanizado": {
        "k_base": 0.04,
        "fator_umidade": 0.85,
        "fator_temp": 1.3,
        "desc": "Estruturas, dutos. Persistência alta."
    },
    "Cerâmica/Azulejo": {
        "k_base": 0.03,
        "fator_umidade": 0.95,
        "fator_temp": 1.1,
        "desc": "Pisos, paredes. Superfície lisa. Persistência muito alta."
    }
}

# Eficácia de NPIs (Non-Pharmaceutical Interventions - Intervenções Não-Farmacológicas)
# Baseado em: Cochrane Reviews, estudos de efetividade de medidas de controle
# Valores representam redução percentual na taxa de transmissão (0-1)
NPIS = {
    "Nenhuma Intervenção": {
        "reducao_transmissao": 0.0,
        "desc": "Sem medidas de controle."
    },
    "Distanciamento Social (1.5m)": {
        "reducao_transmissao": 0.3,
        "desc": "Reduz contatos próximos em 30%."
    },
    "Máscaras Cirúrgicas": {
        "reducao_transmissao": 0.5,
        "desc": "Proteção básica. Reduz transmissão em 50%."
    },
    "Máscaras PFF2/N95": {
        "reducao_transmissao": 0.75,
        "desc": "Proteção alta. Reduz transmissão em 75%."
    },
    "Lockdown Parcial (50% redução de contatos)": {
        "reducao_transmissao": 0.5,
        "desc": "Fechamento de escolas/comércio não essencial."
    },
    "Lockdown Total (80% redução de contatos)": {
        "reducao_transmissao": 0.8,
        "desc": "Fechamento completo. Isolamento domiciliar."
    },
    "Combinação (PFF2 + Distanciamento)": {
        "reducao_transmissao": 0.85,
        "desc": "Máscaras PFF2 + distanciamento social."
    },
    "Ventilação Mecânica (6 ACH)": {
        "reducao_transmissao": 0.4,
        "desc": "Ventilação adequada reduz aerossóis suspensos. 6 trocas de ar por hora."
    },
    "Filtros HEPA": {
        "reducao_transmissao": 0.6,
        "desc": "Filtros de alta eficiência removem partículas do ar. Eficaz contra aerossóis."
    },
    "Barreiras Físicas (Acrílico)": {
        "reducao_transmissao": 0.3,
        "desc": "Barreiras físicas reduzem transmissão por gotículas grandes."
    },
    "Hygiene de Mãos Rigorosa": {
        "reducao_transmissao": 0.2,
        "desc": "Lavagem frequente de mãos reduz transmissão por fômites."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO: MODELO SEIR-A
# =============================================================================
def modelo_seira(y, t, beta, sigma, gamma, alpha, p_assintomatico, N, reducao_npi=0.0):
    """
    Sistema de Equações Diferenciais Ordinárias (EDOs) do modelo SEIR-A.
    
    Estados:
    - S: Suscetíveis
    - E: Expostos (em incubação)
    - I: Infectados Sintomáticos
    - A: Assintomáticos
    - R: Recuperados/Removidos
    
    Parâmetros:
    - beta: Taxa de transmissão (ajustada por NPIs)
    - sigma: Inverso do tempo de incubação
    - gamma: Inverso do tempo de recuperação
    - alpha: Redução de infectividade de assintomáticos
    - p_assintomatico: Proporção que fica assintomática
    - N: População total
    - reducao_npi: Redução na transmissão por NPIs (0-1)
    """
    S, E, I, A, R = y
    
    # Taxa de transmissão efetiva (reduzida por NPIs)
    beta_efetivo = beta * (1 - reducao_npi)
    
    # Taxa de contato efetivo
    # Assumindo que I e A transmitem, mas A com fator alpha
    lambda_t = beta_efetivo * (I + alpha * A) / N
    
    # Equações diferenciais
    dS_dt = -lambda_t * S
    dE_dt = lambda_t * S - sigma * E
    dI_dt = (1 - p_assintomatico) * sigma * E - gamma * I
    dA_dt = p_assintomatico * sigma * E - gamma * A
    dR_dt = gamma * (I + A)
    
    return [dS_dt, dE_dt, dI_dt, dA_dt, dR_dt]

def runge_kutta_4(f, y0, t, args):
    """
    Método de Runge-Kutta de 4ª ordem para resolver EDOs.
    Implementação própria para não depender de scipy.
    """
    n = len(t)
    y = np.zeros((n, len(y0)))
    y[0] = y0
    
    for i in range(n - 1):
        dt = t[i+1] - t[i]
        
        k1 = np.array(f(y[i], t[i], *args))
        k2 = np.array(f(y[i] + dt * k1 / 2, t[i] + dt / 2, *args))
        k3 = np.array(f(y[i] + dt * k2 / 2, t[i] + dt / 2, *args))
        k4 = np.array(f(y[i] + dt * k3, t[i] + dt, *args))
        
        y[i+1] = y[i] + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Garantir que valores não sejam negativos
        y[i+1] = np.maximum(0, y[i+1])
    
    return y

def calcular_seira(agente_dados, populacao, casos_iniciais, dias_simulacao, reducao_npi=0.0):
    """
    Resolve o modelo SEIR-A e retorna a evolução temporal.
    """
    # Parâmetros do agente
    R0 = agente_dados["R0"]
    sigma = agente_dados["sigma"]
    gamma = agente_dados["gamma"]
    alpha = agente_dados["alpha"]
    p_assintomatico = agente_dados["p_assintomatico"]
    
    # Calcular beta a partir de R0
    # R0 = beta / gamma (para modelo SIR simples)
    # Para SEIR-A: R0 ≈ beta / gamma * (1 + alpha * p_assintomatico / (1 - p_assintomatico))
    beta = R0 * gamma / (1 + alpha * p_assintomatico / max(0.01, 1 - p_assintomatico))
    
    # Condições iniciais
    I0 = casos_iniciais * (1 - p_assintomatico)
    A0 = casos_iniciais * p_assintomatico
    E0 = casos_iniciais * 0.5  # Alguns já em incubação
    S0 = populacao - E0 - I0 - A0
    R0_pop = 0
    
    y0 = [S0, E0, I0, A0, R0_pop]
    
    # Tempo de simulação (resolução diária para melhor performance)
    t = np.linspace(0, dias_simulacao, dias_simulacao + 1)
    
    # Resolver EDOs usando Runge-Kutta
    args = (beta, sigma, gamma, alpha, p_assintomatico, populacao, reducao_npi)
    solucao = runge_kutta_4(modelo_seira, y0, t, args)
    
    # Extrair resultados
    S = solucao[:, 0]
    E = solucao[:, 1]
    I = solucao[:, 2]
    A = solucao[:, 3]
    R = solucao[:, 4]
    
    # Calcular casos ativos totais
    casos_ativos = I + A
    
    # Calcular novos casos por dia (mudança em E + I + A)
    total_infectados = E + I + A
    novos_casos = np.diff(total_infectados, prepend=total_infectados[0])
    novos_casos = np.maximum(0, novos_casos)  # Não permitir negativos
    
    return {
        "tempo": t,  # Já em dias
        "S": S,
        "E": E,
        "I": I,
        "A": A,
        "R": R,
        "casos_ativos": casos_ativos,
        "novos_casos": novos_casos
    }

def calcular_persistencia_fomites(superficie_dados, umidade_percent, temperatura_c, tempo_horas):
    """
    Calcula a persistência do agente biológico em superfícies (fômites).
    
    C(t) = C₀ * exp(-k * t)
    
    Onde k é ajustado por umidade e temperatura.
    """
    k_base = superficie_dados["k_base"]
    fator_umidade = superficie_dados["fator_umidade"]
    fator_temp = superficie_dados["fator_temp"]
    
    # Ajustar k por condições ambientais
    # Alta umidade reduz persistência (para maioria dos vírus)
    k_umidade = k_base * (1 + (umidade_percent - 50) / 100 * (1 - fator_umidade))
    
    # Alta temperatura aumenta decaimento
    k_temp = k_umidade * (1 + (temperatura_c - 20) / 20 * (fator_temp - 1))
    
    # Concentração residual
    C_t = math.exp(-k_temp * tempo_horas)
    
    # Tempo para 99% de redução (considerado seguro)
    tempo_seguro = -math.log(0.01) / k_temp if k_temp > 0 else float('inf')
    
    return {
        "concentracao_residual": C_t,
        "reducao_percent": (1 - C_t) * 100,
        "tempo_seguro_horas": tempo_seguro,
        "k_efetivo": k_temp
    }

def calcular_janela_risco(superficies, umidade, temperatura):
    """
    Calcula a janela de risco (tempo de interdição) para múltiplas superfícies.
    Retorna o tempo máximo necessário.
    """
    tempos_seguros = []
    
    for superficie_nome, superficie_dados in superficies.items():
        resultado = calcular_persistencia_fomites(superficie_dados, umidade, temperatura, 0)
        tempos_seguros.append(resultado["tempo_seguro_horas"])
    
    return max(tempos_seguros) if tempos_seguros else 0

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Defesa Biológica Avançada - Modelo SEIR-A")
    st.markdown("**Simulação epidemiológica avançada com transmissão assintomática e análise de persistência em superfícies (fômites)**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos do Modelo SEIR-A", expanded=True):
        st.markdown("""
        #### O Modelo SEIR-A
        
        O Modelo SEIR-A é uma evolução do modelo SIR clássico, desenvolvido para capturar características importantes de doenças infecciosas modernas:
        
        **Estados da População:**
        - **S (Suscetíveis):** Pessoas em risco de contrair a doença
        - **E (Expostos):** Pessoas infectadas, mas ainda no período de incubação (não transmitem ainda)
        - **I (Infectados Sintomáticos):** Doentes com sintomas, transmitem ativamente
        - **A (Assintomáticos):** Infectados sem sintomas, mas também transmitem (transmissão silenciosa)
        - **R (Recuperados/Removidos):** Pessoas que se recuperaram (ou faleceram) e não podem mais ser infectadas
        
        #### Por que Assintomáticos são Críticos?
        
        A transmissão assintomática é um dos maiores desafios no controle de epidemias:
        - **Invisibilidade:** Assintomáticos não são detectados pelo sistema de saúde
        - **Onda Invisível:** A população de assintomáticos cresce antes da população de sintomáticos
        - **Detecção Tardia:** Quando casos sintomáticos são detectados, já existe uma grande população de assintomáticos
        - **Transmissão Contínua:** Assintomáticos continuam transmitindo enquanto não são identificados
        
        #### O que são Fômites?
        
        Fômites são superfícies ou objetos inanimados que podem ser contaminados com agentes patogênicos:
        - **Exemplos:** Maçanetas, mesas, roupas, equipamentos médicos, superfícies de toque
        - **Persistência:** O agente biológico sobrevive por horas ou dias dependendo do material e condições ambientais
        - **Rota de Transmissão:** Contato com superfície contaminada → mão → mucosas (olhos, nariz, boca) = infecção
        
        #### Janela de Risco
        
        A janela de risco é o tempo que um local deve permanecer interditado após contaminação:
        - Baseado no tempo necessário para 99% de redução do agente nas superfícies
        - Varia significativamente dependendo do tipo de superfície e condições ambientais
        - Superfícies antimicrobianas (como cobre) têm janelas de risco muito curtas
        - Superfícies porosas ou que absorvem umidade têm janelas de risco mais longas
        """)

    with st.expander("Parâmetros do Modelo SEIR-A", expanded=False):
        st.markdown("""
        #### Parâmetros Epidemiológicos
        
        **R₀ (Número Reprodutivo Básico):**
        - Quantas pessoas um infectado contamina em média, em uma população totalmente suscetível
        - R₀ < 1: Doença desaparece (cada infectado contamina menos de 1 pessoa)
        - R₀ = 1: Doença estável (cada infectado contamina exatamente 1 pessoa)
        - R₀ > 1: Doença se espalha (cada infectado contamina mais de 1 pessoa)
        - Quanto maior o R₀, mais difícil é controlar a epidemia
        
        **σ (Sigma) - Taxa de Progressão:**
        - Inverso do tempo médio de incubação (1/tempo_incubacao)
        - Quanto maior, mais rápido as pessoas passam de expostas para infectadas
        - Exemplo: σ = 1/5 significa que o tempo médio de incubação é 5 dias
        
        **γ (Gamma) - Taxa de Recuperação:**
        - Inverso do tempo médio de recuperação (1/tempo_recuperacao)
        - Quanto maior, mais rápido as pessoas se recuperam
        - Exemplo: γ = 1/7 significa que o tempo médio de recuperação é 7 dias
        
        **α (Alpha) - Redução de Infectividade de Assintomáticos:**
        - Fator de redução da capacidade de transmissão de assintomáticos (0-1)
        - α = 0.0: Assintomáticos não transmitem
        - α = 0.5: Assintomáticos transmitem 50% menos que sintomáticos
        - α = 1.0: Assintomáticos transmitem igual aos sintomáticos
        - Geralmente, assintomáticos transmitem menos porque não tossem/espirram tanto
        
        **p (Proporção Assintomática):**
        - Proporção de infectados que permanecem assintomáticos durante toda a infecção
        - p = 0.0: Todos desenvolvem sintomas
        - p = 0.3: 30% permanecem assintomáticos
        - p = 1.0: Todos permanecem assintomáticos (hipotético)
        - Doenças com alta proporção de assintomáticos são mais difíceis de controlar
        """)

    st.markdown("---")

    # --- SEÇÃO 1: AGENTE BIOLÓGICO ---
    st.subheader("1. Seleção do Agente Biológico")
    
    agente_nome = st.selectbox(
        "Selecione o Agente Biológico:",
        list(AGENTES_BIO_AVANCADO.keys()),
        help="Escolha o patógeno para simulação. Consulte classificações CDC/WHO para identificação."
    )
    
    agente_dados = AGENTES_BIO_AVANCADO[agente_nome]
    
    if agente_nome == "OUTRAS (Entrada Manual)":
        st.markdown("**Configuração Manual de Parâmetros:**")
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            R0_manual = st.number_input("R₀ (Número Reprodutivo)", min_value=0.0, value=2.5, step=0.1, key="r0_man")
            sigma_manual = st.number_input("σ (1/tempo incubação)", min_value=0.0, value=1/5.0, step=0.01, key="sigma_man")
            gamma_manual = st.number_input("γ (1/tempo recuperação)", min_value=0.0, value=1/7.0, step=0.01, key="gamma_man")
        
        with col_man2:
            alpha_manual = st.number_input("α (Redução assintomáticos)", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key="alpha_man")
            p_assint_manual = st.number_input("p (Proporção assintomáticos)", min_value=0.0, max_value=1.0, value=0.3, step=0.1, key="p_man")
            letalidade_manual = st.number_input("Letalidade (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, key="let_man")
        
        agente_dados = {
            "R0": R0_manual,
            "sigma": sigma_manual,
            "gamma": gamma_manual,
            "alpha": alpha_manual,
            "p_assintomatico": p_assint_manual,
            "letalidade": letalidade_manual / 100.0,
            "desc": "Agente configurado manualmente."
        }
    else:
        st.info(f"**{agente_nome}**\n\n{agente_dados['desc']}")
        
        col_prop1, col_prop2, col_prop3, col_prop4, col_prop5 = st.columns(5)
        col_prop1.metric("R₀", f"{agente_dados['R0']:.2f}", 
                        help="Número reprodutivo básico")
        col_prop2.metric("Tempo Incubação", f"{1/agente_dados['sigma']:.1f} dias",
                        help="Tempo médio entre exposição e aparecimento de sintomas")
        col_prop3.metric("Tempo Recuperação", f"{1/agente_dados['gamma']:.1f} dias",
                        help="Tempo médio de recuperação")
        col_prop4.metric("Assintomáticos", f"{agente_dados['p_assintomatico']*100:.0f}%",
                        help="Proporção de infectados que permanecem assintomáticos")
        col_prop5.metric("Letalidade", f"{agente_dados['letalidade']*100:.1f}%",
                        help="Taxa de letalidade sem tratamento adequado")

    st.markdown("---")

    # --- SEÇÃO 2: CENÁRIO EPIDEMIOLÓGICO ---
    st.subheader("2. Cenário Epidemiológico")
    
    col_cen1, col_cen2 = st.columns(2)
    
    with col_cen1:
        populacao = st.number_input(
            "População Total",
            min_value=100,
            value=10000,
            step=100,
            help="População na área de estudo"
        )
        
        casos_iniciais = st.number_input(
            "Casos Iniciais",
            min_value=1,
            value=10,
            step=1,
            help="Número de pessoas infectadas no início da simulação"
        )
        
        dias_simulacao = st.slider(
            "Dias de Simulação",
            min_value=30,
            max_value=365,
            value=90,
            step=30,
            help="Período de tempo para projetar a epidemia"
        )
    
    with col_cen2:
        st.markdown("**Intervenções Não-Farmacológicas (NPIs):**")
        
        npi_selecionada = st.selectbox(
            "Medida de Controle:",
            list(NPIS.keys()),
            help="Medidas para reduzir transmissão. Baseadas em evidências científicas."
        )
        
        npi_dados = NPIS[npi_selecionada]
        st.info(f"**{npi_selecionada}**\n\n{npi_dados['desc']}\n\n**Redução de Transmissão:** {npi_dados['reducao_transmissao']*100:.0f}%")
        
        # Opção de combinar NPIs
        usar_combinacao = st.checkbox(
            "Aplicar múltiplas intervenções simultaneamente",
            help="Marque para combinar diferentes medidas. A eficácia combinada é calculada multiplicativamente."
        )
        
        if usar_combinacao:
            npi_adicional = st.selectbox(
                "Segunda Intervenção:",
                [k for k in NPIS.keys() if k != npi_selecionada],
                help="Adicionar outra medida de controle"
            )
            # Eficácia combinada: 1 - (1 - r1) × (1 - r2)
            reducao_total = 1 - (1 - npi_dados['reducao_transmissao']) * (1 - NPIS[npi_adicional]['reducao_transmissao'])
            st.success(f"**Redução Combinada:** {reducao_total*100:.0f}%")
        else:
            reducao_total = npi_dados['reducao_transmissao']

    st.markdown("---")

    # --- SEÇÃO 3: ANÁLISE DE FÔMITES ---
    st.subheader("3. Persistência em Superfícies (Fômites)")
    
    st.markdown("**Selecione as superfícies presentes no ambiente:**")
    
    superficies_selecionadas = {}
    col_fom1, col_fom2, col_fom3 = st.columns(3)
    
    with col_fom1:
        usar_aco = st.checkbox("Aço Inoxidável", value=True)
        usar_plastico = st.checkbox("Plástico (Polipropileno)", value=True)
        usar_papel = st.checkbox("Papel/Cartão", value=False)
        usar_tecido = st.checkbox("Tecido/Algodão", value=False)
    
    with col_fom2:
        usar_vidro = st.checkbox("Vidro", value=False)
        usar_cobre = st.checkbox("Cobre", value=False)
        usar_aluminio = st.checkbox("Alumínio", value=False)
        usar_borracha = st.checkbox("Borracha/Silicone", value=False)
    
    with col_fom3:
        usar_madeira = st.checkbox("Madeira", value=False)
        usar_aco_galv = st.checkbox("Aço Galvanizado", value=False)
        usar_ceramica = st.checkbox("Cerâmica/Azulejo", value=False)
    
    if usar_aco:
        superficies_selecionadas["Aço Inoxidável"] = PERSISTENCIA_FOMITES["Aço Inoxidável"]
    if usar_plastico:
        superficies_selecionadas["Plástico (Polipropileno)"] = PERSISTENCIA_FOMITES["Plástico (Polipropileno)"]
    if usar_papel:
        superficies_selecionadas["Papel/Cartão"] = PERSISTENCIA_FOMITES["Papel/Cartão"]
    if usar_tecido:
        superficies_selecionadas["Tecido/Algodão"] = PERSISTENCIA_FOMITES["Tecido/Algodão"]
    if usar_vidro:
        superficies_selecionadas["Vidro"] = PERSISTENCIA_FOMITES["Vidro"]
    if usar_cobre:
        superficies_selecionadas["Cobre"] = PERSISTENCIA_FOMITES["Cobre"]
    if usar_aluminio:
        superficies_selecionadas["Alumínio"] = PERSISTENCIA_FOMITES["Alumínio"]
    if usar_borracha:
        superficies_selecionadas["Borracha/Silicone"] = PERSISTENCIA_FOMITES["Borracha/Silicone"]
    if usar_madeira:
        superficies_selecionadas["Madeira"] = PERSISTENCIA_FOMITES["Madeira"]
    if usar_aco_galv:
        superficies_selecionadas["Aço Galvanizado"] = PERSISTENCIA_FOMITES["Aço Galvanizado"]
    if usar_ceramica:
        superficies_selecionadas["Cerâmica/Azulejo"] = PERSISTENCIA_FOMITES["Cerâmica/Azulejo"]
    
    if not superficies_selecionadas:
        st.warning("Selecione pelo menos uma superfície para análise de fômites.")
    
    col_amb1, col_amb2 = st.columns(2)
    
    with col_amb1:
        umidade = st.slider(
            "Umidade Relativa (%)",
            min_value=20,
            max_value=90,
            value=60,
            step=5,
            help="Umidade afeta a persistência do agente"
        )
    
    with col_amb2:
        temperatura = st.slider(
            "Temperatura Ambiente (°C)",
            min_value=10,
            max_value=40,
            value=25,
            step=1,
            help="Temperatura afeta a taxa de decaimento"
        )

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("SIMULAR EPIDEMIA E ANÁLISE DE FÔMITES", type="primary", use_container_width=True):
        st.session_state['bio_avancado_calc'] = True

    if st.session_state.get('bio_avancado_calc', False):
        # Verificar se R0 > 0 (doença transmissível)
        if agente_dados["R0"] == 0:
            st.warning("**AGENTE NÃO TRANSMISSÍVEL:** Este agente não se espalha pessoa-pessoa. "
                      "Use o módulo de Dispersão Biológica para análise de liberação por aerossol.")
        else:
            # Calcular modelo SEIR-A
            with st.spinner("Calculando evolução da epidemia..."):
                resultado_seira = calcular_seira(
                    agente_dados, populacao, casos_iniciais, dias_simulacao, reducao_total
                )
            
            st.markdown("---")
            st.markdown("### Resultados da Simulação Epidemiológica")
            
            # Métricas principais
            pico_casos_ativos = np.max(resultado_seira["casos_ativos"])
            pico_casos_sintomaticos = np.max(resultado_seira["I"])
            pico_casos_assintomaticos = np.max(resultado_seira["A"])
            dia_pico = resultado_seira["tempo"][np.argmax(resultado_seira["casos_ativos"])]
            
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            
            col_res1.metric(
                "Pico de Casos Ativos",
                f"{pico_casos_ativos:.0f}",
                f"Dia {dia_pico:.0f}"
            )
            col_res2.metric(
                "Pico Sintomáticos",
                f"{pico_casos_sintomaticos:.0f}",
                "Onda Hospitalar"
            )
            col_res3.metric(
                "Pico Assintomáticos",
                f"{pico_casos_assintomaticos:.0f}",
                "Onda Invisível"
            )
            col_res4.metric(
                "Total Recuperados",
                f"{resultado_seira['R'][-1]:.0f}",
                f"{(resultado_seira['R'][-1]/populacao*100):.1f}%"
            )
            
            # Impacto das NPIs
            if reducao_total > 0:
                # Simular sem NPIs para comparação
                resultado_sem_npi = calcular_seira(
                    agente_dados, populacao, casos_iniciais, dias_simulacao, 0.0
                )
                pico_sem_npi = np.max(resultado_sem_npi["casos_ativos"])
                
                reducao_pico = ((pico_sem_npi - pico_casos_ativos) / pico_sem_npi) * 100
                dia_pico_sem = resultado_sem_npi["tempo"][np.argmax(resultado_sem_npi["casos_ativos"])]
                atraso_pico = dia_pico - dia_pico_sem
                
                st.success(f"**IMPACTO DAS NPIs:** Com {npi_selecionada}, o pico de casos será reduzido em **{reducao_pico:.0f}%** "
                          f"e atrasado em **{atraso_pico:.0f} dias**. Isso demonstra a importância das medidas de controle.")
            
            # Gráfico de Curvas Sobrepostas
            st.markdown("---")
            st.markdown("#### Evolução Temporal da Epidemia (Onda Invisível vs Onda Hospitalar)")
            
            df_grafico = pd.DataFrame({
                'Dias': resultado_seira["tempo"],
                'Suscetíveis (S)': resultado_seira["S"],
                'Expostos (E)': resultado_seira["E"],
                'Sintomáticos (I)': resultado_seira["I"],
                'Assintomáticos (A)': resultado_seira["A"],
                'Recuperados (R)': resultado_seira["R"],
                'Casos Ativos Total': resultado_seira["casos_ativos"]
            })
            
            # Gráfico de linha
            chart = alt.Chart(df_grafico).mark_line().encode(
                x=alt.X('Dias:Q', title='Dias desde o início'),
                y=alt.Y('value:Q', title='Número de Pessoas'),
                color=alt.Color('variable:N', 
                              scale=alt.Scale(domain=['Suscetíveis (S)', 'Expostos (E)', 'Sintomáticos (I)', 
                                                     'Assintomáticos (A)', 'Recuperados (R)', 'Casos Ativos Total'],
                                            range=['blue', 'orange', 'red', 'purple', 'green', 'black'])),
                strokeDash=alt.condition(
                    alt.datum.variable == 'Assintomáticos (A)',
                    alt.value([5, 5]),
                    alt.value([0])
                )
            ).transform_fold(
                ['Suscetíveis (S)', 'Expostos (E)', 'Sintomáticos (I)', 'Assintomáticos (A)', 
                 'Recuperados (R)', 'Casos Ativos Total'],
                as_=['variable', 'value']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
            
            st.caption("**Interpretação:** A 'Onda Invisível' (Assintomáticos - linha roxa tracejada) cresce ANTES da 'Onda Hospitalar' "
                      "(Sintomáticos - linha vermelha). Por isso surtos explodem rapidamente quando detectamos casos sintomáticos, "
                      "já existe uma grande população de assintomáticos transmitindo silenciosamente.")
            
            # Dashboard de Fômites
            if superficies_selecionadas:
                st.markdown("---")
                st.markdown("#### Dashboard de Fômites - Persistência em Superfícies")
                
                resultados_fomites = []
                
                for superficie_nome, superficie_dados in superficies_selecionadas.items():
                    resultado = calcular_persistencia_fomites(superficie_dados, umidade, temperatura, 0)
                    
                    resultados_fomites.append({
                        "Superfície": superficie_nome,
                        "Tempo para Descontaminação Natural": f"{resultado['tempo_seguro_horas']:.1f} horas",
                        "Tempo (dias)": f"{resultado['tempo_seguro_horas']/24:.1f}",
                        "Taxa de Decaimento (1/h)": f"{resultado['k_efetivo']:.4f}",
                        "Descrição": superficie_dados['desc']
                    })
                
                df_fomites = pd.DataFrame(resultados_fomites)
                st.dataframe(df_fomites, use_container_width=True, hide_index=True)
                
                # Janela de Risco
                janela_risco = calcular_janela_risco(superficies_selecionadas, umidade, temperatura)
                
                st.markdown("---")
                st.markdown("#### Janela de Risco (Tempo de Interdição)")
                
                col_jan1, col_jan2 = st.columns(2)
                
                with col_jan1:
                    col_jan1.metric(
                        "Tempo de Interdição",
                        f"{janela_risco:.1f} horas",
                        f"{janela_risco/24:.1f} dias",
                        help="Tempo necessário para 99% de redução do agente nas superfícies"
                    )
                
                with col_jan2:
                    if janela_risco < 24:
                        st.success("**Interdição Curta:** Local pode ser liberado após descontaminação rápida. "
                                  "Superfícies antimicrobianas ou condições ambientais favoráveis reduzem o tempo.")
                    elif janela_risco < 72:
                        st.warning("**Interdição Moderada:** Local deve permanecer fechado por alguns dias. "
                                  "Descontaminação ativa pode reduzir o tempo de interdição.")
                    else:
                        st.error("**Interdição Longa:** Local deve permanecer fechado por mais de 3 dias. "
                                "Considere descontaminação ativa (hipoclorito de sódio, peróxido de hidrogênio, radiação UV) "
                                "para reduzir o tempo de interdição.")
                
                # Gráfico de Decaimento
                st.markdown("---")
                st.markdown("#### Decaimento de Viabilidade ao Longo do Tempo")
                
                tempos_horas = np.linspace(0, min(janela_risco * 1.5, 168), 100)  # Até 7 dias ou 1.5x janela
                
                df_decaimento = pd.DataFrame({'Tempo (horas)': tempos_horas})
                
                for superficie_nome, superficie_dados in superficies_selecionadas.items():
                    concentracoes = []
                    for t in tempos_horas:
                        resultado = calcular_persistencia_fomites(superficie_dados, umidade, temperatura, t)
                        concentracoes.append(resultado["concentracao_residual"] * 100)
                    
                    df_decaimento[superficie_nome] = concentracoes
                
                df_decaimento_melt = df_decaimento.melt('Tempo (horas)', var_name='Superfície', value_name='Viabilidade (%)')
                
                chart_decaimento = alt.Chart(df_decaimento_melt).mark_line().encode(
                    x=alt.X('Tempo (horas):Q', title='Tempo (horas)'),
                    y=alt.Y('Viabilidade (%):Q', title='Viabilidade Residual (%)', scale=alt.Scale(type='log')),
                    color='Superfície:N',
                    tooltip=['Tempo (horas)', 'Superfície', 'Viabilidade (%)']
                ).properties(height=300)
                
                st.altair_chart(chart_decaimento, use_container_width=True)
                
                st.caption("**Gráfico em escala logarítmica:** Mostra como diferentes superfícies têm taxas de decaimento distintas. "
                          "Superfícies antimicrobianas (como cobre) decaem muito rápido, enquanto superfícies não porosas "
                          "(como vidro e cerâmica) mantêm o agente por mais tempo.")
            
            # Recomendações
            st.markdown("---")
            st.markdown("### Recomendações Operacionais")
            
            if pico_casos_ativos > populacao * 0.1:
                st.error("**SURTO CRÍTICO:** Mais de 10% da população será infectada simultaneamente. "
                        "O sistema de saúde será sobrecarregado. Implemente medidas drásticas de contenção:")
                st.markdown("""
                1. Lockdown total ou parcial imediato
                2. Isolamento rigoroso de casos e contatos
                3. Testagem em massa para identificar assintomáticos
                4. Preparação de centros de tratamento temporários
                5. Racionamento de recursos hospitalares
                6. Comunicação clara com a população sobre a gravidade
                """)
            elif pico_casos_ativos > populacao * 0.05:
                st.warning("**SURTO MODERADO:** 5-10% da população será infectada. "
                          "Prepare recursos hospitalares e mantenha NPIs rigorosas:")
                st.markdown("""
                1. Manter medidas de distanciamento social
                2. Uso obrigatório de máscaras de alta eficiência (PFF2/N95)
                3. Testagem regular para detecção precoce
                4. Preparação de leitos adicionais
                5. Monitoramento contínuo da situação
                """)
            else:
                st.info("**SURTO CONTROLADO:** Com as medidas implementadas, o surto permanece em níveis gerenciáveis. "
                       "Mantenha as medidas preventivas para evitar recrudescimento.")
            
            if pico_casos_assintomaticos > pico_casos_sintomaticos:
                st.warning("**ALERTA DE TRANSMISSÃO ASSINTOMÁTICA:** A 'onda invisível' (assintomáticos) é maior que a 'onda hospitalar' (sintomáticos). "
                          "Testagem em massa é essencial para detectar casos antes que desenvolvam sintomas e interromper cadeias de transmissão.")
            
            if superficies_selecionadas and janela_risco > 72:
                st.error("**JANELA DE RISCO LONGA:** O local deve permanecer interditado por mais de 3 dias. "
                        "Considere descontaminação ativa para reduzir o tempo:")
                st.markdown("""
                1. **Hipoclorito de Sódio (0.1-0.5%):** Eficaz contra a maioria dos vírus e bactérias
                2. **Peróxido de Hidrogênio (3-6%):** Eficaz e menos corrosivo que hipoclorito
                3. **Radiação UV-C:** Eficaz para descontaminação de superfícies e ar
                4. **Álcool 70%:** Eficaz para descontaminação rápida de superfícies pequenas
                5. **Vaporização de Peróxido de Hidrogênio:** Para descontaminação de ambientes inteiros
                """)
            
            st.markdown("---")
            st.markdown("### Considerações Técnicas")
            st.info("""
            **Limitações do Modelo:**
            - O modelo assume população homogênea e não considera grupos de risco
            - Não modela variações sazonais ou mudanças comportamentais ao longo do tempo
            - Assume que as NPIs têm eficácia constante
            - Não considera mutações do agente ou desenvolvimento de resistência
            - Modelos mais complexos (SEIRS com imunidade temporária, modelos estocásticos) podem ser necessários para análises avançadas
            
            **Interpretação dos Resultados:**
            - Os resultados são projeções baseadas em parâmetros estimados
            - Condições reais podem variar significativamente
            - Consulte epidemiologistas para análises detalhadas e estratégias de controle
            - Combine múltiplas fontes de dados (vigilância epidemiológica, testagem, hospitalizações) para validação
            """)
