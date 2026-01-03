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
    st.markdown("### ☢️ Radiologia Tática e Resposta")
    st.markdown("Ferramenta de comando para proteção radiológica operacional e gestão de tempo de permanência em zonas quentes.")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O que é Radiologia Tática?", expanded=True):
        st.markdown("""
        **O Desafio Operacional:**
        
        Em uma emergência radiológica, você precisa tomar decisões **AGORA**:
        - Quanto tempo minha equipe pode ficar nesta zona?
        - Qual a dose que já recebemos?
        - Quais sintomas devemos esperar?
        - Esta parede oferece proteção suficiente?
        
        **Dose Acumulada vs Taxa de Dose:**
        - **Taxa de Dose (mSv/h):** Quanto radiação você recebe POR HORA
        - **Dose Total (mSv):** Quanto você recebeu no TOTAL (acumulado)
        - **Fórmula:** Dose Total = Taxa × Tempo
        
        **Regra dos 7-10 (Fallout):**
        Após uma explosão nuclear, o fallout decai rapidamente:
        - **H+1h:** Taxa inicial (ex: 100 mSv/h)
        - **H+7h:** Taxa cai para 10 mSv/h (÷10)
        - **H+49h:** Taxa cai para 1 mSv/h (÷100)
        - **H+343h:** Taxa cai para 0.1 mSv/h (÷1000)
        
        **Efeito Combinado (Combined Injury):**
        Vítimas com radiação + queimadura/trauma têm risco **MUITO MAIOR**.
        Uma dose que seria recuperável pode se tornar fatal se houver lesão adicional.
        """)

    with st.expander("🛡️ Limites de Dose Operacional", expanded=False):
        st.markdown("""
        **CNEN / IAEA - Limites de Dose:**
        - **Emergência (Salvar Vidas):** 500 mSv - Situação extrema
        - **Operação de Resgate:** 100 mSv - Resgate de vítimas
        - **Trabalho Controlado:** 50 mSv - Operação planejada
        - **Trabalho Rotineiro:** 20 mSv - Operação normal
        - **Público Geral:** 1 mSv/ano - Limite anual
        
        **Stay Time (Tempo de Permanência):**
        Tempo máximo que você pode ficar antes de atingir o limite.
        """)

    st.markdown("---")

    # --- SEÇÃO 1: CENÁRIO RADIOLÓGICO ---
    st.subheader("1️⃣ Cenário Radiológico")
    
    col_cen1, col_cen2 = st.columns(2)
    
    with col_cen1:
        isotopo_nome = st.selectbox(
            "Fonte Radioativa:",
            list(ISOTOPOS_TATICOS.keys()),
            help="Selecione o isótopo ou tipo de fonte"
        )
        
        isotopo_dados = ISOTOPOS_TATICOS[isotopo_nome]
        
        if isotopo_nome == "OUTRAS (Entrada Manual)":
            gama_const_manual = st.number_input(
                "Constante Gama (mSv/h a 1m por Ci)",
                min_value=0.0,
                value=5.0,
                step=0.1,
                key="gama_man"
            )
            isotopo_dados = {
                "gama_const": gama_const_manual,
                "energia": "Média",
                "meia_vida": 0.0,
                "desc": "Fonte configurada manualmente."
            }
        else:
            st.info(f"ℹ️ {isotopo_dados['desc']}")
        
        # Tipo de fonte
        tipo_fonte = st.radio(
            "Tipo de Fonte:",
            ["Fonte Pontual", "Fallout Nuclear"],
            help="Fonte pontual = taxa constante | Fallout = decai com tempo"
        )
        
        is_fallout = (tipo_fonte == "Fallout Nuclear")
        
        if is_fallout:
            st.warning("⚠️ **FALLOUT DETECTADO:** A taxa de dose decairá rapidamente (Regra dos 7-10).")
    
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
        
        st.markdown(f"**📊 Taxa de Dose Atual:** {taxa_dose:.2f} mSv/h")
        
        # Tempo desde o início (para fallout)
        if is_fallout:
            tempo_desde_inicio = st.number_input(
                "Tempo desde a Explosão (horas)",
                min_value=0.0,
                value=1.0,
                step=0.5,
                help="H+? (horas após a explosão)"
            )
            
            # Recalcular taxa considerando decaimento
            taxa_dose = calcular_taxa_dose_fallout(taxa_inicial, tempo_desde_inicio, usar_regra_7_10=True)
            st.markdown(f"**📉 Taxa de Dose Atual (com decaimento):** {taxa_dose:.3f} mSv/h")

    st.markdown("---")

    # --- SEÇÃO 2: BLINDAGEM E PROTEÇÃO ---
    st.subheader("2️⃣ Blindagem e Proteção")
    
    material_blindagem = st.selectbox(
        "Material de Proteção Disponível:",
        list(MATERIAIS_BLINDAGEM.keys()),
        help="Selecione a blindagem entre você e a fonte"
    )
    
    material_dados = MATERIAIS_BLINDAGEM[material_blindagem]
    
    if material_blindagem != "Nenhuma Blindagem":
        st.info(f"🛡️ **{material_blindagem}**\n\n{material_dados['desc']}")
        
        # Calcular taxa protegida
        # Assumir HVL médio de 6cm para concreto (ajustável)
        hvl_medio = material_dados.get("hvl_cm", 6.0)
        espessura = 20.0 if "20cm" in material_blindagem else (40.0 if "40cm" in material_blindagem else 
                                                               (1.0 if "1cm" in material_blindagem else 
                                                                (5.0 if "5cm" in material_blindagem else 
                                                                 (50.0 if "50cm" in material_blindagem else 10.0))))
        
        taxa_protegida = calcular_atenuacao_blindagem(taxa_dose, espessura, hvl_medio)
        fator_reducao = taxa_dose / taxa_protegida if taxa_protegida > 0 else float('inf')
        
        st.success(f"✅ **Taxa Protegida:** {taxa_protegida:.3f} mSv/h (Redução de {fator_reducao:.1f}x)")
        
        # Usar taxa protegida para cálculos
        taxa_operacao = taxa_protegida
    else:
        taxa_operacao = taxa_dose
        st.warning("⚠️ **SEM PROTEÇÃO:** Você está recebendo a dose completa.")

    st.markdown("---")

    # --- SEÇÃO 3: OPERAÇÃO E LIMITES ---
    st.subheader("3️⃣ Operação e Limites de Dose")
    
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        tipo_operacao = st.selectbox(
            "Tipo de Operação:",
            list(LIMITES_DOSE.keys()),
            help="Selecione o limite de dose apropriado"
        )
        
        limite_dados = LIMITES_DOSE[tipo_operacao]
        limite_mSv = limite_dados["dose_max"]
        
        st.info(f"📋 **{tipo_operacao}**\n\n{limite_dados['desc']}\n\n**Limite:** {limite_mSv} mSv")
        
        dose_ja_recebida = st.number_input(
            "Dose Já Recebida (mSv)",
            min_value=0.0,
            value=0.0,
            step=0.1,
            help="Dose acumulada de operações anteriores"
        )
    
    with col_op2:
        tempo_operacao = st.number_input(
            "Tempo de Operação Planejado (horas)",
            min_value=0.0,
            value=1.0,
            step=0.1,
            help="Quanto tempo você planeja ficar nesta zona"
        )
        
        # Calcular dose que será recebida
        if is_fallout:
            dose_receber = calcular_dose_integrada(taxa_operacao, tempo_operacao, taxa_inicial, is_fallout=True)
        else:
            dose_receber = calcular_dose_integrada(taxa_operacao, tempo_operacao)
        
        dose_total = dose_ja_recebida + dose_receber
        
        st.markdown(f"**📊 Dose que Será Recebida:** {dose_receber:.2f} mSv")
        st.markdown(f"**📊 Dose Total Acumulada:** {dose_total:.2f} mSv")

    st.markdown("---")

    # --- SEÇÃO 4: EFEITO COMBINADO (OPCIONAL) ---
    st.subheader("4️⃣ Efeito Combinado (Radiação + Lesão Adicional)")
    
    usar_efeito_combinado = st.checkbox(
        "Avaliar efeito de lesão adicional (queimadura/trauma)",
        help="Marque se houver vítimas com lesões combinadas"
    )
    
    tipo_lesao = None
    if usar_efeito_combinado:
        tipo_lesao = st.selectbox(
            "Tipo de Lesão Adicional:",
            list(FATORES_LESAO_COMBINADA.keys()),
            help="Lesão além da exposição à radiação"
        )

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("⚡ Calcular Análise Tática", type="primary", use_container_width=True):
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
        st.markdown("### 📊 Resultados da Análise Tática")
        
        # Métricas principais
        col_res1, col_res2, col_res3 = st.columns(3)
        
        col_res1.metric(
            "Dose Total Acumulada",
            f"{dose_total_calc:.2f} mSv",
            f"{((dose_total_calc/limite_mSv)*100):.1f}% do limite",
            delta_color="inverse" if dose_total_calc > limite_mSv else "normal"
        )
        
        col_res2.metric(
            "Stay Time (Tempo Máximo)",
            f"{stay_time:.1f} horas",
            f"{stay_time*60:.0f} minutos"
        )
        
        col_res3.metric(
            "Taxa de Dose Operacional",
            f"{taxa_operacao:.3f} mSv/h",
            "Com blindagem" if material_blindagem != "Nenhuma Blindagem" else "Sem blindagem"
        )
        
        # Cronômetro Regressivo
        st.markdown("#### ⏱️ Cronômetro Regressivo de Missão")
        
        if stay_time > 0 and stay_time < 1000:
            minutos_restantes = int(stay_time * 60)
            horas_restantes = int(stay_time)
            minutos_frac = int((stay_time - horas_restantes) * 60)
            
            if horas_restantes > 0:
                tempo_display = f"{horas_restantes}h {minutos_frac}min"
            else:
                tempo_display = f"{minutos_restantes}min"
            
            if stay_time < 1.0:
                st.error(f"🚨 **TEMPO CRÍTICO:** Você tem apenas **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv!")
            elif stay_time < 4.0:
                st.warning(f"⚠️ **ATENÇÃO:** Você tem **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv.")
            else:
                st.success(f"✅ **TEMPO DISPONÍVEL:** Você tem **{tempo_display}** restantes antes de atingir o limite de {limite_mSv} mSv.")
        else:
            st.info("ℹ️ **TEMPO ILIMITADO:** A taxa de dose é muito baixa. Operação pode continuar indefinidamente dentro do limite.")
        
        # Diagnóstico de Segurança
        st.markdown("#### 🚨 Diagnóstico de Segurança")
        
        if dose_total_calc > limite_mSv:
            st.error(f"🚨 **LIMITE EXCEDIDO:** A dose total ({dose_total_calc:.2f} mSv) excede o limite operacional ({limite_mSv} mSv). "
                    f"**RETIRADA IMEDIATA DA ZONA!**")
        elif dose_total_calc > limite_mSv * 0.8:
            st.warning(f"⚠️ **APROXIMANDO DO LIMITE:** Dose total ({dose_total_calc:.2f} mSv) está em {((dose_total_calc/limite_mSv)*100):.0f}% do limite. "
                     f"Monitore continuamente e prepare retirada.")
        else:
            st.success(f"✅ **DENTRO DO LIMITE:** Dose total ({dose_total_calc:.2f} mSv) está dentro do limite operacional ({limite_mSv} mSv).")
        
        # Estimativa de ARS
        st.markdown("---")
        st.markdown("#### 🏥 Estimativa de Síndrome Aguda da Radiação (ARS)")
        
        dose_gy = dose_total_calc / 1000.0  # Converter mSv para Gy
        
        ars_resultado = avaliar_ars(dose_gy)
        
        st.markdown(f"**Dose Recebida:** {dose_gy:.3f} Gy ({dose_total_calc:.1f} mSv)")
        st.markdown(f"**Faixa de Dose:** {list(SINTOMAS_ARS.keys())[list(SINTOMAS_ARS.values()).index(ars_resultado)]}")
        
        st.markdown(f"**Sintomas Esperados:**")
        st.info(f"📋 {ars_resultado['sintomas']}")
        
        st.markdown(f"**Prognóstico:**")
        if ars_resultado['cor'] == 'green':
            st.success(f"✅ {ars_resultado['prognostico']}")
        elif ars_resultado['cor'] == 'orange':
            st.warning(f"⚠️ {ars_resultado['prognostico']}")
        else:
            st.error(f"🚨 {ars_resultado['prognostico']}")
        
        # Efeito Combinado
        if usar_efeito_combinado and tipo_lesao:
            st.markdown("---")
            st.markdown("#### ⚠️ Análise de Efeito Combinado (Combined Injury)")
            
            risco_combinado = calcular_risco_combinado(dose_gy, tipo_lesao)
            
            st.warning(f"🚨 **LESÃO COMBINADA DETECTADA:** {risco_combinado['desc_lesao']}")
            
            col_comb1, col_comb2 = st.columns(2)
            
            with col_comb1:
                col_comb1.metric(
                    "Dose Original",
                    f"{risco_combinado['dose_original']:.3f} Gy",
                    f"{risco_combinado['dose_original']*1000:.1f} mSv"
                )
            
            with col_comb2:
                col_comb2.metric(
                    "Dose Equivalente (com lesão)",
                    f"{risco_combinado['dose_equivalente']:.3f} Gy",
                    f"Fator: {risco_combinado['fator_multiplicacao']:.1f}x",
                    delta_color="inverse"
                )
            
            st.markdown("**Reavaliação de ARS com Lesão Combinada:**")
            ars_comb = risco_combinado['ars_equivalente']
            
            if ars_comb['cor'] == 'green':
                st.success(f"✅ {ars_comb['prognostico']}")
            elif ars_comb['cor'] == 'orange':
                st.warning(f"⚠️ {ars_comb['prognostico']}")
            else:
                st.error(f"🚨 {ars_comb['prognostico']}")
            
            st.error(f"💀 **ALERTA CRÍTICO:** A lesão adicional aumenta o risco em {risco_combinado['fator_multiplicacao']:.1f}x. "
                    f"Uma dose que seria recuperável ({risco_combinado['dose_original']:.3f} Gy) agora equivale a "
                    f"{risco_combinado['dose_equivalente']:.3f} Gy. **Tratamento médico imediato obrigatório!**")
        
        # Tabela de Sintomas Prováveis
        st.markdown("---")
        st.markdown("#### 📋 Tabela de Sintomas Prováveis por Faixa de Dose")
        
        df_sintomas = pd.DataFrame({
            'Faixa de Dose': list(SINTOMAS_ARS.keys()),
            'Sintomas': [d['sintomas'] for d in SINTOMAS_ARS.values()],
            'Prognóstico': [d['prognostico'] for d in SINTOMAS_ARS.values()]
        })
        
        st.dataframe(df_sintomas, use_container_width=True, hide_index=True)
        
        # Impacto da Blindagem
        if material_blindagem != "Nenhuma Blindagem":
            st.markdown("---")
            st.markdown("#### 🛡️ Impacto da Blindagem Improvisada")
            
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
                    f"{stay_time_sem*60:.0f} min"
                )
            
            with col_blind2:
                col_blind2.metric(
                    "Stay Time COM Blindagem",
                    f"{stay_time:.1f} horas",
                    f"+{aumento_tempo:.0f}%",
                    delta_color="normal"
                )
            
            st.success(f"✅ **BLINDAGEM EFICAZ:** Com {material_blindagem}, seu tempo de operação aumenta de "
                      f"{stay_time_sem:.1f}h para {stay_time:.1f}h (aumento de {aumento_tempo:.0f}%).")
        
        # Gráfico de Evolução da Dose
        st.markdown("---")
        st.markdown("#### 📈 Evolução da Dose Acumulada ao Longo do Tempo")
        
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
        
        chart = alt.Chart(df_evolucao).mark_line().encode(
            x=alt.X('Tempo (horas):Q', title='Tempo de Operação (horas)'),
            y=alt.Y('value:Q', title='Dose Acumulada (mSv)'),
            color=alt.Color('variable:N', 
                          scale=alt.Scale(domain=['Dose Acumulada (mSv)', 'Limite Operacional'],
                                        range=['blue', 'red'])),
            strokeDash=alt.condition(
                alt.datum.variable == 'Limite Operacional',
                alt.value([5, 5]),
                alt.value([0])
            )
        ).transform_fold(
            ['Dose Acumulada (mSv)', 'Limite Operacional'],
            as_=['variable', 'value']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
        
        st.caption("💡 A linha azul mostra a dose acumulada ao longo do tempo. "
                  "A linha vermelha tracejada indica o limite operacional. "
                  "O cruzamento mostra quando você deve sair da zona.")
        
        # Recomendações
        st.markdown("---")
        st.markdown("#### 💡 Recomendações Táticas")
        
        if dose_total_calc > limite_mSv:
            st.error("🚨 **RETIRADA IMEDIATA:** Você já excedeu o limite. Saia da zona AGORA e procure atendimento médico.")
        elif stay_time < 0.5:
            st.error("🚨 **TEMPO MUITO LIMITADO:** Menos de 30 minutos restantes. Complete apenas tarefas críticas e saia.")
        elif stay_time < 2.0:
            st.warning("⚠️ **OPERAÇÃO DE CURTA DURAÇÃO:** Tempo limitado. Priorize tarefas essenciais. Monitore dose continuamente.")
        else:
            st.info("✅ **OPERAÇÃO VIÁVEL:** Tempo suficiente para operação planejada. Mantenha monitoramento contínuo.")
        
        if ars_resultado['cor'] in ['red', 'darkred']:
            st.error("🚨 **SINTOMAS GRAVES ESPERADOS:** Com esta dose, sintomas severos são prováveis. "
                    "Hospitalização e tratamento especializado são obrigatórios.")
        
        if usar_efeito_combinado and tipo_lesao and risco_combinado['fator_multiplicacao'] > 2.0:
            st.error("💀 **RISCO EXTREMO:** Lesão combinada aumenta drasticamente a mortalidade. "
                    "Tratamento médico especializado imediato é crítico para sobrevivência.")
