import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math
from datetime import datetime, timedelta

# =============================================================================
# 1. BANCO DE DADOS: ISÓTOPOS E PROPRIEDADES
# =============================================================================
ISOTOPOS_TATICOS = {
    "Cobalto-60 (Co-60)": {
        "gama_const": 13.0,  # mSv/h a 1m por Ci
        "energia": "Alta (1.17 e 1.33 MeV)",
        "meia_vida": 5.27,  # anos
        "desc": "Fonte de radioterapia. Alta energia, difícil de blindar."
    },
    "Césio-137 (Cs-137)": {
        "gama_const": 3.3,
        "energia": "Média (0.662 MeV)",
        "meia_vida": 30.2,  # anos
        "desc": "Fonte órfã comum. Contaminação de longo prazo."
    },
    "Irídio-192 (Ir-192)": {
        "gama_const": 4.8,
        "energia": "Média (~0.38 MeV)",
        "meia_vida": 73.8,  # dias
        "desc": "Gamagrafia industrial. Decai rápido."
    },
    "Iodo-131 (I-131)": {
        "gama_const": 2.2,
        "energia": "Média-Baixa (0.364 MeV)",
        "meia_vida": 8.0,  # dias
        "desc": "Medicina nuclear. Contaminação interna crítica."
    },
    "Fallout Nuclear (Mistura)": {
        "gama_const": 5.0,  # Aproximado
        "energia": "Média-Alta (espectro complexo)",
        "meia_vida": 0.0,  # Usa regra dos 7-10
        "desc": "Precipitação radioativa após explosão. Decai rapidamente (Regra dos 7-10)."
    },
    "Tecnécio-99m (Tc-99m)": {
        "gama_const": 0.78,
        "energia": "Baixa (0.140 MeV)",
        "meia_vida": 0.006,  # 6 horas
        "desc": "Isótopo médico mais comum. Baixa energia, mas usado em grandes quantidades em hospitais."
    },
    "Amerício-241 (Am-241)": {
        "gama_const": 0.1,
        "energia": "Baixíssima (0.060 MeV)",
        "meia_vida": 432.0,  # anos
        "desc": "Fonte de detecção de fumaça e perfilagem de poços. Gama fraco, mas muito persistente."
    },
    "Sódio-24 (Na-24)": {
        "gama_const": 18.4,
        "energia": "Muito Alta (1.37 e 2.75 MeV)",
        "meia_vida": 0.625,  # 15 horas
        "desc": "Gama extremamente forte. Usado como traçador. Decai rapidamente."
    },
    "Rádio-226 (Ra-226)": {
        "gama_const": 8.25,
        "energia": "Média-Alta (espectro complexo)",
        "meia_vida": 1600.0,  # anos
        "desc": "Fonte órfã histórica. Encontrado em para-raios antigos e relógios vintage. Muito persistente."
    },
    "Césio-134 (Cs-134)": {
        "gama_const": 8.7,
        "energia": "Média-Alta (0.605 e 0.796 MeV)",
        "meia_vida": 2.06,  # anos
        "desc": "Produto de fissão. Mais energético que Cs-137, mas decai mais rápido."
    },
    "Antimônio-124 (Sb-124)": {
        "gama_const": 9.8,
        "energia": "Alta (0.603 a 2.09 MeV)",
        "meia_vida": 0.164,  # 60 dias
        "desc": "Gama de alta energia. Usado em fontes de nêutrons e start-up de reatores."
    },
    "Európio-152 (Eu-152)": {
        "gama_const": 5.8,
        "energia": "Média (espectro complexo)",
        "meia_vida": 13.5,  # anos
        "desc": "Fonte de calibração com múltiplas energias. Comum em laboratórios."
    },
    "Manganês-54 (Mn-54)": {
        "gama_const": 4.7,
        "energia": "Média (0.835 MeV)",
        "meia_vida": 0.855,  # 312 dias
        "desc": "Produto de ativação em aços de reatores. Pode ser encontrado em sucata radioativa."
    },
    "Selênio-75 (Se-75)": {
        "gama_const": 2.0,
        "energia": "Média-Baixa (0.121 a 0.401 MeV)",
        "meia_vida": 0.329,  # 120 dias
        "desc": "Substituto moderno do Irídio-192 para gamagrafia. Menor energia, mais seguro."
    },
    "Zinco-65 (Zn-65)": {
        "gama_const": 2.7,
        "energia": "Média (1.115 MeV)",
        "meia_vida": 0.668,  # 244 dias
        "desc": "Emissor gama duro. Usado em estudos de desgaste de ligas metálicas."
    },
    "OUTRAS (Entrada Manual)": {
        "gama_const": 5.0,
        "energia": "Média",
        "meia_vida": 0.0,
        "desc": "Configure manualmente os parâmetros."
    }
}

# Materiais de Blindagem Improvisada
MATERIAIS_BLINDAGEM = {
    "Nenhuma Blindagem": {
        "hvl_cm": float('inf'),
        "densidade": 0,
        "desc": "Sem proteção. Dose completa."
    },
    "Parede de Concreto (20cm)": {
        "hvl_cm": 6.0,  # Aproximado para Co-60
        "densidade": 2.4,
        "desc": "Parede padrão de construção. Redução significativa."
    },
    "Parede de Concreto (40cm)": {
        "hvl_cm": 6.0,
        "densidade": 2.4,
        "desc": "Parede reforçada. Proteção alta."
    },
    "Veículo Blindado": {
        "hvl_cm": 2.2,  # Aço
        "densidade": 7.8,
        "desc": "Blindagem de aço. Redução moderada."
    },
    "Chumbo (1cm)": {
        "hvl_cm": 1.25,  # Para Co-60
        "densidade": 11.3,
        "desc": "Chumbo fino. Redução básica."
    },
    "Chumbo (5cm)": {
        "hvl_cm": 1.25,
        "densidade": 11.3,
        "desc": "Chumbo grosso. Proteção alta."
    },
    "Terra/Saco de Areia (50cm)": {
        "hvl_cm": 9.0,
        "densidade": 1.6,
        "desc": "Barricada improvisada. Eficaz para proteção temporária."
    }
}

# Limites de Dose Operacional (CNEN / IAEA)
LIMITES_DOSE = {
    "Emergência (Salvar Vidas)": {
        "dose_max": 500,  # mSv
        "desc": "Situação extrema. Apenas para salvar vidas."
    },
    "Operação de Resgate": {
        "dose_max": 100,  # mSv
        "desc": "Resgate de vítimas. Limite por evento."
    },
    "Trabalho Controlado": {
        "dose_max": 50,  # mSv
        "desc": "Operação planejada. Limite anual típico."
    },
    "Trabalho Rotineiro": {
        "dose_max": 20,  # mSv
        "desc": "Operação normal. Limite mensal."
    },
    "Público Geral": {
        "dose_max": 1,  # mSv
        "desc": "Limite anual para população."
    }
}

# Síndrome Aguda da Radiação (ARS) - Sintomas por Dose
SINTOMAS_ARS = {
    "0-0.5 Gy (0-50 rad)": {
        "dose_min": 0,
        "dose_max": 0.5,
        "sintomas": "Nenhum sintoma imediato. Possível redução temporária de células sanguíneas.",
        "prognostico": "Excelente. Recuperação completa esperada.",
        "cor": "green"
    },
    "0.5-1.0 Gy (50-100 rad)": {
        "dose_min": 0.5,
        "dose_max": 1.0,
        "sintomas": "Náusea leve em 10-20% dos expostos (2-4h). Fadiga. Redução de glóbulos brancos.",
        "prognostico": "Bom. Tratamento de suporte. Recuperação em semanas.",
        "cor": "green"
    },
    "1.0-2.0 Gy (100-200 rad)": {
        "dose_min": 1.0,
        "dose_max": 2.0,
        "sintomas": "Náusea e vômito em 50% (1-3h). Diarreia leve. Redução significativa de células sanguíneas.",
        "prognostico": "Moderado. Hospitalização recomendada. Tratamento com fatores de crescimento.",
        "cor": "orange"
    },
    "2.0-4.0 Gy (200-400 rad)": {
        "dose_min": 2.0,
        "dose_max": 4.0,
        "sintomas": "Náusea/vômito em 80-100% (30min-2h). Diarreia. Hemorragias. Queda de cabelo (2-3 semanas).",
        "prognostico": "Grave. Hospitalização obrigatória. Mortalidade 0-50% sem tratamento.",
        "cor": "red"
    },
    "4.0-6.0 Gy (400-600 rad)": {
        "dose_min": 4.0,
        "dose_max": 6.0,
        "sintomas": "Vômito imediato (<30min). Diarreia severa. Hemorragias múltiplas. Queda de cabelo total.",
        "prognostico": "Muito Grave. Mortalidade 50-90% mesmo com tratamento intensivo.",
        "cor": "red"
    },
    ">6.0 Gy (>600 rad)": {
        "dose_min": 6.0,
        "dose_max": float('inf'),
        "sintomas": "Vômito imediato. Diarreia sanguinolenta. Choque. Falência de múltiplos órgãos.",
        "prognostico": "Letal. Mortalidade >90%. Cuidados paliativos.",
        "cor": "darkred"
    }
}

# Fator de Multiplicação de Risco para Lesões Combinadas
FATORES_LESAO_COMBINADA = {
    "Sem Lesão Adicional": {
        "fator": 1.0,
        "desc": "Apenas exposição à radiação."
    },
    "Queimadura Térmica Leve (<10% corpo)": {
        "fator": 1.5,
        "desc": "Queimaduras de 1º grau. Aumenta risco moderadamente."
    },
    "Queimadura Térmica Moderada (10-20% corpo)": {
        "fator": 2.5,
        "desc": "Queimaduras de 2º grau. Risco significativamente aumentado."
    },
    "Queimadura Térmica Grave (>20% corpo)": {
        "fator": 4.0,
        "desc": "Queimaduras extensas. Dose letal reduzida drasticamente."
    },
    "Trauma Mecânico (Fratura)": {
        "fator": 2.0,
        "desc": "Fratura ou trauma. Compromete sistema imune."
    },
    "Trauma Múltiplo": {
        "fator": 3.0,
        "desc": "Múltiplas lesões. Risco extremamente elevado."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================
def calcular_taxa_dose_fallout(taxa_inicial_mSv_h, tempo_horas, usar_regra_7_10=True):
    """
    Calcula taxa de dose de fallout usando Regra dos 7-10 ou Equação de Way-Wigner.
    
    Regra dos 7-10: A cada 7 horas, a taxa cai por fator de 10.
    Way-Wigner: R(t) = R_1 * t^(-1.2)
    """
    if tempo_horas <= 0:
        return taxa_inicial_mSv_h
    
    if usar_regra_7_10:
        # Regra dos 7-10 (mais conservadora e didática)
        # A cada 7 horas, divide por 10
        fator_tempo = (tempo_horas / 7.0)
        taxa_atual = taxa_inicial_mSv_h / (10 ** fator_tempo)
    else:
        # Equação de Way-Wigner
        taxa_atual = taxa_inicial_mSv_h * (tempo_horas ** (-1.2))
    
    return max(0.0, taxa_atual)

def calcular_dose_integrada(taxa_dose_mSv_h, tempo_horas, taxa_inicial_mSv_h=0, is_fallout=False):
    """
    Calcula Dose Total Integrada (TID).
    
    Para taxa constante: D = R * t
    Para fallout (decai): Integração de R(t) * dt
    """
    if is_fallout and taxa_inicial_mSv_h > 0:
        # Integração numérica do decaimento
        # D = ∫ R(t) dt de 0 a t
        num_pontos = max(100, int(tempo_horas * 10))
        tempos = np.linspace(0, tempo_horas, num_pontos)
        dt = tempo_horas / num_pontos
        
        dose_total = 0.0
        for t in tempos:
            taxa_t = calcular_taxa_dose_fallout(taxa_inicial_mSv_h, t, usar_regra_7_10=True)
            dose_total += taxa_t * dt
        
        return dose_total
    else:
        # Taxa constante
        return taxa_dose_mSv_h * tempo_horas

def calcular_atenuacao_blindagem(dose_inicial, espessura_cm, hvl_cm):
    """
    Lei de Beer-Lambert simplificada usando HVL.
    I = I0 * (1/2)^(x / HVL)
    """
    if hvl_cm <= 0 or hvl_cm == float('inf'):
        return dose_inicial
    
    num_hvls = espessura_cm / hvl_cm
    fator_reducao = 2 ** num_hvls
    dose_protegida = dose_inicial / fator_reducao
    
    return dose_protegida

def calcular_stay_time(taxa_dose_mSv_h, limite_operacional_mSv, dose_ja_recebida_mSv=0, 
                       taxa_inicial_mSv_h=0, is_fallout=False):
    """
    Calcula tempo máximo de permanência (Stay Time).
    
    t_stay = (Limite - Dose_Recebida) / Taxa_Dose
    
    Para fallout, resolve iterativamente.
    """
    dose_disponivel = limite_operacional_mSv - dose_ja_recebida_mSv
    
    if dose_disponivel <= 0:
        return 0.0
    
    if is_fallout and taxa_inicial_mSv_h > 0:
        # Resolver iterativamente para fallout
        tempo_atual = 0.0
        dose_acumulada = 0.0
        dt = 0.1  # Passo de 0.1 horas (6 minutos)
        
        while dose_acumulada < dose_disponivel and tempo_atual < 1000:  # Limite de segurança
            taxa_atual = calcular_taxa_dose_fallout(taxa_inicial_mSv_h, tempo_atual)
            dose_incremento = taxa_atual * dt
            
            if dose_acumulada + dose_incremento > dose_disponivel:
                # Ajuste fino
                tempo_restante = (dose_disponivel - dose_acumulada) / taxa_atual
                return tempo_atual + tempo_restante
            
            dose_acumulada += dose_incremento
            tempo_atual += dt
        
        return tempo_atual
    else:
        # Taxa constante
        if taxa_dose_mSv_h <= 0:
            return float('inf')
        
        return dose_disponivel / taxa_dose_mSv_h

def avaliar_ars(dose_gy):
    """
    Avalia Síndrome Aguda da Radiação baseado na dose.
    """
    for faixa, dados in SINTOMAS_ARS.items():
        if dados["dose_min"] <= dose_gy < dados["dose_max"]:
            return dados
    
    # Se exceder todas as faixas
    return SINTOMAS_ARS[">6.0 Gy (>600 rad)"]

def calcular_risco_combinado(dose_gy, tipo_lesao):
    """
    Calcula risco combinado de radiação + lesão adicional.
    """
    fator = FATORES_LESAO_COMBINADA.get(tipo_lesao, FATORES_LESAO_COMBINADA["Sem Lesão Adicional"])
    
    # Dose efetiva equivalente (aumentada pelo fator)
    dose_equivalente = dose_gy * fator["fator"]
    
    # Reavaliar ARS com dose equivalente
    ars_equivalente = avaliar_ars(dose_equivalente)
    
    return {
        "dose_original": dose_gy,
        "dose_equivalente": dose_equivalente,
        "fator_multiplicacao": fator["fator"],
        "ars_equivalente": ars_equivalente,
        "desc_lesao": fator["desc"]
    }

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Cálculo de Dose Tática")
    st.markdown("**Ferramenta de Comando para Proteção Radiológica Operacional: Gestão de Tempo de Permanência e Análise de Risco**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Radiologia Tática e Proteção Radiológica Operacional", expanded=True):
        st.markdown("""
        **O Desafio Operacional:**
        
        Em emergências radiológicas, decisões críticas devem ser tomadas imediatamente:
        - Quanto tempo a equipe pode permanecer na zona de risco sem exceder limites de dose?
        - Qual a dose acumulada que já foi recebida?
        - Quais sintomas devem ser esperados baseados na dose recebida?
        - A blindagem disponível oferece proteção adequada?
        
        **Conceitos Fundamentais:**
        
        1. **Taxa de Dose (mSv/h):** Quantidade de radiação recebida por unidade de tempo (por hora).
           É uma medida instantânea do risco no momento.
        
        2. **Dose Total Acumulada (mSv):** Quantidade total de radiação recebida ao longo do tempo.
           É a soma de todas as exposições. Fórmula: **Dose Total = Taxa × Tempo**
        
        3. **Stay Time (Tempo de Permanência):** Tempo máximo que uma pessoa pode permanecer em uma 
           área antes de atingir um limite de dose predefinido. Calculado como:
           **Stay Time = (Limite de Dose - Dose Já Recebida) / Taxa de Dose**
        
        **Regra dos 7-10 (Decaimento de Fallout):**
        
        Após uma explosão nuclear, o fallout radioativo decai rapidamente seguindo uma regra empírica:
        - **H+1h (1 hora após):** Taxa inicial (exemplo: 100 mSv/h)
        - **H+7h (7 horas após):** Taxa cai para 1/10 do valor inicial (10 mSv/h)
        - **H+49h (49 horas após):** Taxa cai para 1/100 do valor inicial (1 mSv/h)
        - **H+343h (343 horas após):** Taxa cai para 1/1000 do valor inicial (0.1 mSv/h)
        
        Esta regra é conservadora e útil para planejamento tático, permitindo estimar quando uma área 
        se tornará segura para operações prolongadas.
        
        **Efeito Combinado (Combined Injury Syndrome):**
        
        Vítimas que sofrem exposição à radiação combinada com outras lesões (queimaduras, trauma, 
        contaminação química) apresentam risco significativamente aumentado. O efeito sinérgico 
        pode fazer com que uma dose que seria recuperável se torne fatal. Este fenômeno é conhecido 
        como "Combined Injury Syndrome" e é crítico em cenários de acidentes múltiplos.
        
        **Síndrome Aguda da Radiação (ARS - Acute Radiation Syndrome):**
        
        A ARS ocorre quando uma pessoa recebe uma dose alta de radiação em um curto período de tempo. 
        Os sintomas e prognóstico dependem da dose recebida:
        - **0-0.5 Gy:** Geralmente assintomático, recuperação completa
        - **0.5-1.0 Gy:** Sintomas leves, recuperação em semanas
        - **1.0-2.0 Gy:** Sintomas moderados, hospitalização recomendada
        - **2.0-4.0 Gy:** Sintomas graves, mortalidade 0-50% sem tratamento
        - **4.0-6.0 Gy:** Sintomas muito graves, mortalidade 50-90% mesmo com tratamento
        - **>6.0 Gy:** Geralmente letal, mortalidade >90%
        
        **Limitações do Modelo:**
        
        Este modelo assume condições ideais e não considera:
        - Variações individuais na sensibilidade à radiação
        - Efeitos de radiação parcial do corpo (exposição não uniforme)
        - Efeitos de longo prazo (câncer, doenças crônicas)
        - Interações complexas com medicamentos ou condições pré-existentes
        """)

    with st.expander("Limites de Dose Operacional (CNEN / IAEA)", expanded=False):
        st.markdown("""
        **Limites de Dose para Diferentes Cenários Operacionais:**
        
        - **Emergência (Salvar Vidas):** 500 mSv - Situação extrema onde vidas estão em risco imediato.
          Apenas para operações de salvamento crítico. Requer justificativa documentada.
        
        - **Operação de Resgate:** 100 mSv - Resgate de vítimas em emergências. Limite por evento, 
          não anual. Requer planejamento e monitoramento contínuo.
        
        - **Trabalho Controlado:** 50 mSv - Operação planejada em zona controlada. Limite anual típico 
          para trabalhadores nuclear. Requer dosimetria pessoal e controle de acesso.
        
        - **Trabalho Rotineiro:** 20 mSv - Operação normal em instalações nucleares. Limite mensal 
          típico. Requer monitoramento regular e procedimentos estabelecidos.
        
        - **Público Geral:** 1 mSv/ano - Limite anual para população geral. Área deve ser segura 
          para acesso público sem restrições.
        
        **Stay Time (Tempo de Permanência):**
        
        O tempo máximo que uma pessoa pode permanecer em uma área antes de atingir o limite de dose 
        é calculado considerando a taxa de dose atual e a dose já recebida. Para operações seguras, 
        sempre mantenha uma margem de segurança e monitore continuamente.
        """)

    st.markdown("---")

    # --- SEÇÃO 1: CENÁRIO RADIOLÓGICO ---
    st.subheader("Cenário Radiológico")
    
    col_cen1, col_cen2 = st.columns(2)
    
    with col_cen1:
        isotopo_nome = st.selectbox(
            "Fonte Radioativa",
            list(ISOTOPOS_TATICOS.keys()),
            help="Selecione o isótopo ou tipo de fonte radioativa presente no cenário."
        )
        
        isotopo_dados = ISOTOPOS_TATICOS[isotopo_nome]
        
        if isotopo_nome == "OUTRAS (Entrada Manual)":
            gama_const_manual = st.number_input(
                "Constante Gama (mSv/h a 1m por Ci)",
                min_value=0.0,
                value=5.0,
                step=0.1,
                key="gama_man",
                help="Constante gama do isótopo. Consulte tabelas de referência se necessário."
            )
            isotopo_dados = {
                "gama_const": gama_const_manual,
                "energia": "Média",
                "meia_vida": 0.0,
                "desc": "Fonte configurada manualmente."
            }
        else:
            st.info(f"**{isotopo_nome}**\n\n**Descrição:** {isotopo_dados['desc']}\n\n"
                   f"**Energia:** {isotopo_dados['energia']}\n\n"
                   f"**Meia-vida:** {isotopo_dados['meia_vida']} anos" if isotopo_dados['meia_vida'] > 1 
                   else f"**Meia-vida:** {isotopo_dados['meia_vida']*365} dias" if isotopo_dados['meia_vida'] > 0.01
                   else f"**Meia-vida:** {isotopo_dados['meia_vida']*24*60:.1f} horas")
        
        # Tipo de fonte
        tipo_fonte = st.radio(
            "Tipo de Fonte",
            ["Fonte Pontual", "Fallout Nuclear"],
            help="Fonte pontual: taxa constante ao longo do tempo. Fallout: taxa decai rapidamente (Regra dos 7-10)."
        )
        
        is_fallout = (tipo_fonte == "Fallout Nuclear")
        
        if is_fallout:
            st.warning("**FALLOUT NUCLEAR DETECTADO:** A taxa de dose decairá rapidamente seguindo a Regra dos 7-10. "
                      "A cada 7 horas, a taxa cai por um fator de 10.")
    
    with col_cen2:
        if not is_fallout:
            # Para fonte pontual, usar atividade e distância
            atividade = st.number_input(
                "Atividade da Fonte (Ci)",
                min_value=0.01,
                value=10.0,
                step=0.1,
                help="Intensidade da fonte"
            )
            
            distancia = st.number_input(
                "Distância da Fonte (metros)",
                min_value=0.1,
                value=2.0,
                step=0.5,
                help="Distância entre a fonte e o operador"
            )
            
            # Calcular taxa de dose inicial
            taxa_dose = (isotopo_dados["gama_const"] * atividade) / (distancia ** 2)
            taxa_inicial = taxa_dose
        else:
            # Para fallout, entrada direta da taxa
            taxa_dose = st.number_input(
                "Taxa de Dose Inicial (mSv/h) - H+1h",
                min_value=0.1,
                value=100.0,
                step=1.0,
                help="Taxa de dose medida 1 hora após a explosão"
            )
            taxa_inicial = taxa_dose
        
        st.metric("Taxa de Dose Atual", f"{taxa_dose:.2f} mSv/h",
                 help="Taxa de dose no momento atual, considerando decaimento se aplicável")
        
        # Tempo desde o início (para fallout)
        if is_fallout:
            tempo_desde_inicio = st.number_input(
                "Tempo desde a Explosão (horas)",
                min_value=0.0,
                value=1.0,
                step=0.5,
                help="Tempo decorrido desde a explosão nuclear (H+? horas). Usado para calcular o decaimento do fallout."
            )
            
            # Recalcular taxa considerando decaimento
            taxa_dose = calcular_taxa_dose_fallout(taxa_inicial, tempo_desde_inicio, usar_regra_7_10=True)
            st.metric("Taxa de Dose Atual (com decaimento)", f"{taxa_dose:.3f} mSv/h",
                     f"Reduzida de {taxa_inicial:.2f} mSv/h",
                     help="Taxa de dose ajustada pelo decaimento do fallout usando Regra dos 7-10")

    st.markdown("---")

    # --- SEÇÃO 2: BLINDAGEM E PROTEÇÃO ---
    st.subheader("Blindagem e Proteção")
    
    material_blindagem = st.selectbox(
        "Material de Proteção Disponível",
        list(MATERIAIS_BLINDAGEM.keys()),
        help="Selecione o tipo de blindagem ou proteção disponível entre você e a fonte radioativa."
    )
    
    material_dados = MATERIAIS_BLINDAGEM[material_blindagem]
    
    if material_blindagem != "Nenhuma Blindagem":
        st.info(f"**{material_blindagem}**\n\n**Descrição:** {material_dados['desc']}")
        
        # Calcular taxa protegida
        # Assumir HVL médio de 6cm para concreto (ajustável)
        hvl_medio = material_dados.get("hvl_cm", 6.0)
        espessura = 20.0 if "20cm" in material_blindagem else (40.0 if "40cm" in material_blindagem else 
                                                               (1.0 if "1cm" in material_blindagem else 
                                                                (5.0 if "5cm" in material_blindagem else 
                                                                 (50.0 if "50cm" in material_blindagem else 10.0))))
        
        taxa_protegida = calcular_atenuacao_blindagem(taxa_dose, espessura, hvl_medio)
        fator_reducao = taxa_dose / taxa_protegida if taxa_protegida > 0 else float('inf')
        
        st.success(f"**Taxa Protegida:** {taxa_protegida:.3f} mSv/h (Redução de {fator_reducao:.1f}x)")
        
        # Usar taxa protegida para cálculos
        taxa_operacao = taxa_protegida
    else:
        taxa_operacao = taxa_dose
        st.warning("**SEM PROTEÇÃO:** Você está recebendo a dose completa da fonte. Considere usar blindagem se disponível.")

    st.markdown("---")

    # --- SEÇÃO 3: OPERAÇÃO E LIMITES ---
    st.subheader("Operação e Limites de Dose")
    
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        tipo_operacao = st.selectbox(
            "Tipo de Operação",
            list(LIMITES_DOSE.keys()),
            help="Selecione o limite de dose apropriado para o tipo de operação planejada."
        )
        
        limite_dados = LIMITES_DOSE[tipo_operacao]
        limite_mSv = limite_dados["dose_max"]
        
        st.info(f"**{tipo_operacao}**\n\n**Descrição:** {limite_dados['desc']}\n\n"
               f"**Limite de Dose:** {limite_mSv} mSv")
        
        dose_ja_recebida = st.number_input(
            "Dose Já Recebida (mSv)",
            min_value=0.0,
            value=0.0,
            step=0.1,
            help="Dose acumulada de operações anteriores ou exposições prévias. "
                 "Importante para calcular o tempo restante disponível."
        )
    
    with col_op2:
        tempo_operacao = st.number_input(
            "Tempo de Operação Planejado (horas)",
            min_value=0.0,
            value=1.0,
            step=0.1,
            help="Tempo que você planeja permanecer na zona de risco. "
                 "Usado para calcular a dose que será recebida."
        )
        
        # Calcular dose que será recebida
        if is_fallout:
            dose_receber = calcular_dose_integrada(taxa_operacao, tempo_operacao, taxa_inicial, is_fallout=True)
        else:
            dose_receber = calcular_dose_integrada(taxa_operacao, tempo_operacao)
        
        dose_total = dose_ja_recebida + dose_receber
        
        st.metric("Dose que Será Recebida", f"{dose_receber:.2f} mSv",
                 help="Dose adicional que será recebida durante o tempo de operação planejado")
        st.metric("Dose Total Acumulada", f"{dose_total:.2f} mSv",
                 f"{((dose_total/limite_mSv)*100):.1f}% do limite",
                 delta_color="inverse" if dose_total > limite_mSv else "normal",
                 help="Dose total acumulada (já recebida + planejada)")

    st.markdown("---")

    # --- SEÇÃO 4: EFEITO COMBINADO (OPCIONAL) ---
    st.subheader("Efeito Combinado (Radiação + Lesão Adicional)")
    
    usar_efeito_combinado = st.checkbox(
        "Avaliar Efeito de Lesão Adicional",
        help="Marque esta opção se houver vítimas com lesões combinadas (queimaduras, trauma) além da exposição à radiação."
    )
    
    tipo_lesao = None
    if usar_efeito_combinado:
        tipo_lesao = st.selectbox(
            "Tipo de Lesão Adicional",
            list(FATORES_LESAO_COMBINADA.keys()),
            help="Selecione o tipo de lesão adicional presente. Lesões combinadas aumentam significativamente o risco."
        )
        
        if tipo_lesao != "Sem Lesão Adicional":
            fator_lesao = FATORES_LESAO_COMBINADA[tipo_lesao]
            st.warning(f"**Lesão Combinada:** {fator_lesao['desc']}\n\n"
                      f"**Fator de Multiplicação de Risco:** {fator_lesao['fator']:.1f}x\n\n"
                      f"Esta lesão aumenta o risco equivalente em {fator_lesao['fator']:.1f} vezes.")

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("Calcular Análise Tática", type="primary", use_container_width=True):
        st.session_state['rad_tatica_calc'] = True

    if st.session_state.get('rad_tatica_calc', False):
        # Calcular Stay Time
        if is_fallout:
            stay_time = calcular_stay_time(taxa_operacao, limite_mSv, dose_ja_recebida, taxa_inicial, is_fallout=True)
        else:
            stay_time = calcular_stay_time(taxa_operacao, limite_mSv, dose_ja_recebida)
        
        # Calcular dose total
        if is_fallout:
            dose_total_calc = calcular_dose_integrada(taxa_operacao, tempo_operacao, taxa_inicial, is_fallout=True) + dose_ja_recebida
        else:
            dose_total_calc = dose_ja_recebida + (taxa_operacao * tempo_operacao)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise Tática")
        
        # Métricas principais
        col_res1, col_res2, col_res3 = st.columns(3)
        
        col_res1.metric(
            "Dose Total Acumulada",
            f"{dose_total_calc:.2f} mSv",
            f"{((dose_total_calc/limite_mSv)*100):.1f}% do limite",
            delta_color="inverse" if dose_total_calc > limite_mSv else "normal",
            help="Dose total acumulada (já recebida + planejada)"
        )
        
        col_res2.metric(
            "Stay Time (Tempo Máximo)",
            f"{stay_time:.1f} horas",
            f"{stay_time*60:.0f} minutos",
            help="Tempo máximo de permanência antes de atingir o limite de dose"
        )
        
        col_res3.metric(
            "Taxa de Dose Operacional",
            f"{taxa_operacao:.3f} mSv/h",
            "Com blindagem" if material_blindagem != "Nenhuma Blindagem" else "Sem blindagem",
            help="Taxa de dose considerando blindagem se aplicável"
        )
        
        # Cronômetro Regressivo
        st.markdown("#### Tempo Restante Disponível")
        
        if stay_time > 0 and stay_time < 1000:
            minutos_restantes = int(stay_time * 60)
            horas_restantes = int(stay_time)
            minutos_frac = int((stay_time - horas_restantes) * 60)
            
            if horas_restantes > 0:
                tempo_display = f"{horas_restantes}h {minutos_frac}min"
            else:
                tempo_display = f"{minutos_restantes}min"
            
            if stay_time < 1.0:
                st.error(f"**TEMPO CRÍTICO:** Você tem apenas **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv. "
                        f"Complete apenas tarefas essenciais e saia imediatamente.")
            elif stay_time < 4.0:
                st.warning(f"**ATENÇÃO:** Você tem **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv. "
                          f"Monitore continuamente e prepare retirada.")
            else:
                st.success(f"**TEMPO DISPONÍVEL:** Você tem **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv. "
                          f"Operação viável, mas mantenha monitoramento contínuo.")
        else:
            st.info("**TEMPO ILIMITADO:** A taxa de dose é muito baixa. Operação pode continuar indefinidamente dentro do limite, "
                   "mas sempre monitore para mudanças nas condições.")
        
        # Diagnóstico de Segurança
        st.markdown("---")
        st.markdown("#### Diagnóstico de Segurança")
        
        if dose_total_calc > limite_mSv:
            st.error(f"**LIMITE EXCEDIDO:** A dose total ({dose_total_calc:.2f} mSv) excede o limite operacional ({limite_mSv} mSv). "
                    f"**RETIRADA IMEDIATA DA ZONA!** Procure atendimento médico e notifique supervisão.")
        elif dose_total_calc > limite_mSv * 0.8:
            st.warning(f"**APROXIMANDO DO LIMITE:** Dose total ({dose_total_calc:.2f} mSv) está em {((dose_total_calc/limite_mSv)*100):.0f}% do limite. "
                     f"Monitore continuamente e prepare retirada. Considere reduzir tempo de operação.")
        else:
            st.success(f"**DENTRO DO LIMITE:** Dose total ({dose_total_calc:.2f} mSv) está dentro do limite operacional ({limite_mSv} mSv). "
                      f"Operação viável, mas mantenha monitoramento contínuo.")
        
        # Estimativa de ARS
        st.markdown("---")
        st.markdown("#### Estimativa de Síndrome Aguda da Radiação (ARS)")
        
        dose_gy = dose_total_calc / 1000.0  # Converter mSv para Gy
        
        ars_resultado = avaliar_ars(dose_gy)
        
        st.markdown(f"**Dose Recebida:** {dose_gy:.3f} Gy ({dose_total_calc:.1f} mSv)")
        
        # Encontrar a faixa de dose (já calculada em ars_resultado, mas vamos exibir a faixa)
        faixa_dose = None
        for faixa, dados in SINTOMAS_ARS.items():
            if dados == ars_resultado:
                faixa_dose = faixa
                break
        if faixa_dose is None:
            # Buscar por comparação de valores
            for faixa, dados in SINTOMAS_ARS.items():
                if dados["dose_min"] <= dose_gy < dados["dose_max"]:
                    faixa_dose = faixa
                    break
        if faixa_dose is None:
            faixa_dose = ">6.0 Gy (>600 rad)"
        
        st.markdown(f"**Faixa de Dose:** {faixa_dose}")
        
        st.markdown(f"**Sintomas Esperados:**")
        st.info(f"{ars_resultado['sintomas']}")
        
        st.markdown(f"**Prognóstico:**")
        if ars_resultado['cor'] == 'green':
            st.success(f"{ars_resultado['prognostico']}")
        elif ars_resultado['cor'] == 'orange':
            st.warning(f"{ars_resultado['prognostico']}")
        else:
            st.error(f"{ars_resultado['prognostico']}")
        
        # Efeito Combinado
        if usar_efeito_combinado and tipo_lesao:
            st.markdown("---")
            st.markdown("#### Análise de Efeito Combinado (Combined Injury Syndrome)")
            
            risco_combinado = calcular_risco_combinado(dose_gy, tipo_lesao)
            
            st.warning(f"**LESÃO COMBINADA DETECTADA:** {risco_combinado['desc_lesao']}")
            
            col_comb1, col_comb2 = st.columns(2)
            
            with col_comb1:
                col_comb1.metric(
                    "Dose Original",
                    f"{risco_combinado['dose_original']:.3f} Gy",
                    f"{risco_combinado['dose_original']*1000:.1f} mSv",
                    help="Dose de radiação recebida"
                )
            
            with col_comb2:
                col_comb2.metric(
                    "Dose Equivalente (com lesão)",
                    f"{risco_combinado['dose_equivalente']:.3f} Gy",
                    f"Fator: {risco_combinado['fator_multiplicacao']:.1f}x",
                    delta_color="inverse",
                    help="Dose equivalente considerando o efeito sinérgico da lesão adicional"
                )
            
            st.markdown("**Reavaliação de ARS com Lesão Combinada:**")
            ars_comb = risco_combinado['ars_equivalente']
            
            if ars_comb['cor'] == 'green':
                st.success(f"{ars_comb['prognostico']}")
            elif ars_comb['cor'] == 'orange':
                st.warning(f"{ars_comb['prognostico']}")
            else:
                st.error(f"{ars_comb['prognostico']}")
            
            st.error(f"**ALERTA CRÍTICO:** A lesão adicional aumenta o risco em {risco_combinado['fator_multiplicacao']:.1f} vezes. "
                    f"Uma dose que seria recuperável ({risco_combinado['dose_original']:.3f} Gy) agora equivale a "
                    f"{risco_combinado['dose_equivalente']:.3f} Gy. **Tratamento médico especializado imediato é obrigatório!**")
        
        # Tabela de Sintomas Prováveis
        st.markdown("---")
        st.markdown("#### Tabela de Sintomas Prováveis por Faixa de Dose")
        st.caption("Tabela de referência mostrando sintomas e prognóstico esperados para diferentes faixas de dose.")
        
        df_sintomas = pd.DataFrame({
            'Faixa de Dose': list(SINTOMAS_ARS.keys()),
            'Sintomas': [d['sintomas'] for d in SINTOMAS_ARS.values()],
            'Prognóstico': [d['prognostico'] for d in SINTOMAS_ARS.values()]
        })
        
        st.dataframe(df_sintomas, use_container_width=True, hide_index=True)
        
        # Impacto da Blindagem
        if material_blindagem != "Nenhuma Blindagem":
            st.markdown("---")
            st.markdown("#### Impacto da Blindagem")
            
            # Comparar com/sem blindagem
            taxa_sem_blindagem = taxa_dose
            stay_time_sem = calcular_stay_time(taxa_sem_blindagem, limite_mSv, dose_ja_recebida, 
                                               taxa_inicial if is_fallout else 0, is_fallout)
            
            aumento_tempo = ((stay_time - stay_time_sem) / stay_time_sem * 100) if stay_time_sem > 0 else 0
            
            col_blind1, col_blind2 = st.columns(2)
            
            with col_blind1:
                col_blind1.metric(
                    "Stay Time SEM Blindagem",
                    f"{stay_time_sem:.1f} horas",
                    f"{stay_time_sem*60:.0f} minutos",
                    help="Tempo máximo de permanência sem proteção"
                )
            
            with col_blind2:
                col_blind2.metric(
                    "Stay Time COM Blindagem",
                    f"{stay_time:.1f} horas",
                    f"+{aumento_tempo:.0f}%",
                    delta_color="normal",
                    help="Tempo máximo de permanência com blindagem"
                )
            
            st.success(f"**BLINDAGEM EFICAZ:** Com {material_blindagem}, seu tempo de operação aumenta de "
                      f"{stay_time_sem:.1f}h para {stay_time:.1f}h (aumento de {aumento_tempo:.0f}%). "
                      f"A blindagem oferece proteção significativa.")
        
        # Gráfico de Evolução da Dose
        st.markdown("---")
        st.markdown("#### Evolução da Dose Acumulada ao Longo do Tempo")
        st.caption("Gráfico mostrando como a dose acumula ao longo do tempo de operação.")
        
        tempos_grafico = np.linspace(0, min(stay_time * 1.2, 24), 100)  # Até 24h ou 1.2x stay time
        
        doses_acumuladas = []
        for t in tempos_grafico:
            if is_fallout:
                dose_t = calcular_dose_integrada(taxa_operacao, t, taxa_inicial, is_fallout=True) + dose_ja_recebida
            else:
                dose_t = dose_ja_recebida + (taxa_operacao * t)
            doses_acumuladas.append(dose_t)
        
        df_evolucao = pd.DataFrame({
            'Tempo (horas)': tempos_grafico,
            'Dose Acumulada (mSv)': doses_acumuladas,
            'Limite Operacional': [limite_mSv] * len(tempos_grafico)
        })
        
        chart = alt.Chart(df_evolucao).mark_line(size=2).encode(
            x=alt.X('Tempo (horas):Q', title='Tempo de Operação (horas)'),
            y=alt.Y('value:Q', title='Dose Acumulada (mSv)'),
            color=alt.Color('variable:N', 
                          scale=alt.Scale(domain=['Dose Acumulada (mSv)', 'Limite Operacional'],
                                        range=['#3498db', '#e74c3c']),
                          legend=alt.Legend(title="")),
            strokeDash=alt.condition(
                alt.datum.variable == 'Limite Operacional',
                alt.value([5, 5]),
                alt.value([0])
            )
        ).transform_fold(
            ['Dose Acumulada (mSv)', 'Limite Operacional'],
            as_=['variable', 'value']
        ).properties(height=350, title="Evolução da Dose Acumulada")
        
        st.altair_chart(chart, use_container_width=True)
        
        st.caption("**Interpretação:** A linha azul mostra a dose acumulada ao longo do tempo. "
                  "A linha vermelha tracejada indica o limite operacional. "
                  "O ponto onde as linhas se cruzam representa o momento em que você deve sair da zona.")
        
        # Recomendações
        st.markdown("---")
        st.markdown("#### Recomendações Operacionais")
        
        if dose_total_calc > limite_mSv:
            st.error("**RETIRADA IMEDIATA:** Você já excedeu o limite de dose. Saia da zona imediatamente e procure atendimento médico. "
                    "Notifique supervisão sobre a exposição.")
        elif stay_time < 0.5:
            st.error("**TEMPO MUITO LIMITADO:** Menos de 30 minutos restantes. Complete apenas tarefas absolutamente críticas e saia. "
                    "Não arrisque exposição adicional.")
        elif stay_time < 2.0:
            st.warning("**OPERAÇÃO DE CURTA DURAÇÃO:** Tempo limitado disponível. Priorize tarefas essenciais. "
                      "Monitore dose continuamente e prepare retirada antes de atingir o limite.")
        else:
            st.info("**OPERAÇÃO VIÁVEL:** Tempo suficiente disponível para operação planejada. "
                   "Mantenha monitoramento contínuo da dose e esteja preparado para retirada se condições mudarem.")
        
        if ars_resultado['cor'] in ['red', 'darkred']:
            st.error("**SINTOMAS GRAVES ESPERADOS:** Com esta dose, sintomas severos de Síndrome Aguda da Radiação são prováveis. "
                    "Hospitalização e tratamento especializado são obrigatórios. Procure atendimento médico imediato.")
        
        if usar_efeito_combinado and tipo_lesao and risco_combinado['fator_multiplicacao'] > 2.0:
            st.error("**RISCO EXTREMO:** Lesão combinada aumenta drasticamente a mortalidade. "
                    "Tratamento médico especializado imediato é crítico para sobrevivência. "
                    "Priorize evacuação e tratamento médico sobre outras operações.")
        
        # Recomendações adicionais
        with st.expander("Recomendações Adicionais e Considerações Táticas", expanded=False):
            st.markdown(f"""
            **Cenário Analisado:**
            - **Fonte:** {isotopo_nome}
            - **Tipo:** {tipo_fonte}
            - **Taxa de Dose:** {taxa_operacao:.3f} mSv/h (com blindagem: {material_blindagem})
            - **Limite Operacional:** {limite_mSv} mSv ({tipo_operacao})
            - **Dose Já Recebida:** {dose_ja_recebida:.2f} mSv
            - **Dose Total Estimada:** {dose_total_calc:.2f} mSv
            - **Stay Time:** {stay_time:.1f} horas ({stay_time*60:.0f} minutos)
            
            **Ações Recomendadas:**
            
            1. **Monitoramento Contínuo:**
               - Use dosímetros pessoais para todos os membros da equipe
               - Monitore taxa de dose em tempo real se possível
               - Registre doses recebidas por cada pessoa
               - Estabeleça pontos de verificação de dose ao longo da operação
            
            2. **Gestão de Tempo:**
               - Planeje operação para completar antes de atingir 80% do limite
               - Mantenha margem de segurança (não use todo o stay time disponível)
               - Implemente sistema de alerta quando aproximar do limite
               - Prepare rota de saída rápida
            
            3. **Proteção:**
               - Use toda blindagem disponível
               - Maximize distância da fonte quando possível
               - Minimize tempo de exposição
               - Implemente rotação de pessoal se operação for longa
            
            4. **Comunicação:**
               - Mantenha comunicação constante com comando
               - Reporte mudanças nas condições
               - Notifique quando aproximar do limite
               - Documente todas as exposições
            
            5. **Preparação Médica:**
               - Tenha equipe médica preparada para receber vítimas
               - Prepare tratamento para ARS se doses forem altas
               - Considere efeito combinado se houver outras lesões
               - Mantenha contato com centro de tratamento especializado
            
            **Importante:** Este modelo fornece estimativas baseadas em condições ideais. Na realidade, fatores como 
            variações na taxa de dose, geometria da fonte, e condições individuais podem alterar os resultados. 
            Sempre use medições de campo para validar e ajuste conforme necessário.
            """)
