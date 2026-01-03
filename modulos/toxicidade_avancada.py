import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================================================================
# 1. BANCO DE DADOS: SUBSTÂNCIAS QUÍMICAS COM IDLH (NIOSH)
# =============================================================================
# IDLH = Immediately Dangerous to Life or Health (ppm)
# Fonte: NIOSH Pocket Guide to Chemical Hazards
# Unidade: ppm (partes por milhão em volume)
SUBSTANCIAS_TOXICAS = {
    "Acetona": {
        "idlh": 2500,
        "desc": "Solvente comum. Irritante moderado, mas inflamável."
    },
    "Acetonitrila": {
        "idlh": 500,
        "desc": "Solvente de HPLC. Metaboliza em CIANETO no corpo (efeito retardado)."
    },
    "Ácido Clorídrico (HCl)": {
        "idlh": 50,
        "desc": "Vapores corrosivos brancos. Destrói tecido pulmonar rapidamente."
    },
    "Ácido Nítrico (Fumegante)": {
        "idlh": 25,
        "desc": "Vapores vermelhos (NOx). Causa edema pulmonar tardio (12-24h)."
    },
    "Ácido Sulfúrico": {
        "idlh": 15,
        "desc": "Névoa ácida densa. Queimaduras químicas severas."
    },
    "Amônia (Anidra)": {
        "idlh": 300,
        "desc": "Gás leve (sobe). Irritante severo, pode causar sufocamento."
    },
    "Arsina (SA)": {
        "idlh": 3,
        "desc": "Gás incolor (cheiro de alho). Destrói hemácias (anemia hemolítica)."
    },
    "Bromo": {
        "idlh": 3,
        "desc": "Vapor marrom denso. Extremamente corrosivo e tóxico."
    },
    "Cloro": {
        "idlh": 10,
        "desc": "Gás verde-amarelado. Irritante severo, causa edema pulmonar."
    },
    "Cianeto de Hidrogênio (HCN)": {
        "idlh": 50,
        "desc": "Gás letal. Bloqueia respiração celular. Cheiro de amêndoas amargas."
    },
    "Fosgênio (COCl2)": {
        "idlh": 2,
        "desc": "Gás de guerra química. Edema pulmonar tardio (6-24h)."
    },
    "Formaldeído": {
        "idlh": 20,
        "desc": "Gás irritante e carcinogênico. Cheiro pungente."
    },
    "Monóxido de Carbono (CO)": {
        "idlh": 1200,
        "desc": "Gás incolor e inodoro. Desloca oxigênio do sangue (hipóxia)."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "idlh": 100,
        "desc": "Gás ácido (cheiro de ovo podre). Paralisia respiratória em altas doses."
    },
    "Tetracloreto de Carbono": {
        "idlh": 200,
        "desc": "Solvente clorado. Tóxico para fígado e rins."
    },
    "Tolueno": {
        "idlh": 500,
        "desc": "Solvente aromático. Depressivo do sistema nervoso central."
    },
    # Gases Asfixiantes (para cálculo de hipóxia)
    "Nitrogênio (N2)": {
        "idlh": 0,  # Não é tóxico, mas desloca O2
        "tipo": "asfixiante",
        "desc": "Gás inerte. Desloca oxigênio do ar, causando hipóxia por falta de O2."
    },
    "Dióxido de Carbono (CO2)": {
        "idlh": 40000,  # ppm - muito alto, mas desloca O2
        "tipo": "asfixiante",
        "desc": "Gás denso. Em altas concentrações, desloca oxigênio e causa asfixia."
    },
    "Argônio": {
        "idlh": 0,
        "tipo": "asfixiante",
        "desc": "Gás inerte. Desloca oxigênio, causando hipóxia."
    },
    "Metano (CH4)": {
        "idlh": 0,  # Não é tóxico, mas pode deslocar O2 em altas concentrações
        "tipo": "asfixiante",
        "desc": "Gás natural. Em altas concentrações, pode deslocar oxigênio."
    }
}

# Classificação de tipos de contaminantes para filtros
TIPOS_CONTAMINANTES = {
    "particula": "Partículas sólidas ou líquidas (poeira, névoa, fumaça)",
    "gas_vapor": "Gases e vapores orgânicos/inorgânicos",
    "acido": "Gases ácidos (HCl, H2SO4, HNO3)",
    "amonia": "Amoníaco e derivados",
    "organico": "Vapores orgânicos (solventes, hidrocarbonetos)",
    "asfixiante": "Gases asfixiantes (N2, CO2, Ar) - deslocam O2"
}

# =============================================================================
# 2. TABELA DE APF (ASSIGNED PROTECTION FACTORS) - NIOSH
# =============================================================================
# APF = Fator de Proteção Atribuído
# Representa quantas vezes o EPI reduz a concentração inalada
# Fonte: NIOSH 42 CFR Part 84 / OSHA 29 CFR 1910.134
APF_NIOSH = {
    "Sem Proteção (Ar Livre)": {
        "apf": 1,
        "desc": "Nenhum EPI. A concentração ambiente é igual à inalada."
    },
    "Máscara PFF2 (N95)": {
        "apf": 10,
        "filtros_adequados": ["particula"],
        "desc": "Respirador descartável com filtro P2/N95. ⚠️ **APENAS PARTÍCULAS** - NÃO protege contra gases/vapores!"
    },
    "Máscara PFF3 (P100)": {
        "apf": 50,
        "filtros_adequados": ["particula"],
        "desc": "Respirador descartável de alta eficiência. Filtro P100 remove 99.97% das partículas. ⚠️ **APENAS PARTÍCULAS** - NÃO protege contra gases!"
    },
    "Máscara Facial Inteira (Half-Mask)": {
        "apf": 10,
        "filtros_adequados": ["particula", "gas_vapor", "organico", "acido", "amonia"],
        "desc": "Máscara que cobre nariz e boca. ⚠️ **DEPENDE DO FILTRO QUÍMICO** instalado (cartucho apropriado)."
    },
    "Máscara Facial Inteira (Full-Face)": {
        "apf": 50,
        "filtros_adequados": ["particula", "gas_vapor", "organico", "acido", "amonia"],
        "desc": "Máscara que cobre rosto inteiro. ⚠️ **DEPENDE DO FILTRO QUÍMICO** instalado (cartucho apropriado)."
    },
    "Respirador Motorizado (PAPR)": {
        "apf": 25,
        "filtros_adequados": ["particula", "gas_vapor", "organico", "acido", "amonia"],
        "desc": "Powered Air-Purifying Respirator. ⚠️ **DEPENDE DO FILTRO QUÍMICO** instalado."
    },
    "Respirador Autônomo (SCBA)": {
        "apf": 10000,
        "filtros_adequados": ["particula", "gas_vapor", "organico", "acido", "amonia", "asfixiante"],
        "desc": "Self-Contained Breathing Apparatus. ✅ **PROTEÇÃO TOTAL** - Ar comprimido próprio, independente do ambiente."
    },
    "Respirador de Linha de Ar": {
        "apf": 1000,
        "filtros_adequados": ["particula", "gas_vapor", "organico", "acido", "amonia", "asfixiante"],
        "desc": "Supplied Air Respirator. ✅ **PROTEÇÃO TOTAL** - Ar fornecido por mangueira de fonte externa limpa."
    }
}

# Mapeamento de substâncias para tipos de contaminantes
MAPEAMENTO_TIPO_CONTAMINANTE = {
    "Acetona": "organico",
    "Acetonitrila": "organico",
    "Ácido Clorídrico (HCl)": "acido",
    "Ácido Nítrico (Fumegante)": "acido",
    "Ácido Sulfúrico": "acido",
    "Amônia (Anidra)": "amonia",
    "Arsina (SA)": "gas_vapor",
    "Bromo": "gas_vapor",
    "Cloro": "gas_vapor",
    "Cianeto de Hidrogênio (HCN)": "gas_vapor",
    "Fosgênio (COCl2)": "gas_vapor",
    "Formaldeído": "organico",
    "Monóxido de Carbono (CO)": "gas_vapor",
    "Sulfeto de Hidrogênio (H2S)": "gas_vapor",
    "Tetracloreto de Carbono": "organico",
    "Tolueno": "organico",
    "Nitrogênio (N2)": "asfixiante",
    "Dióxido de Carbono (CO2)": "asfixiante",
    "Argônio": "asfixiante",
    "Metano (CH4)": "asfixiante"
}

# =============================================================================
# 3. MOTOR DE CÁLCULO: ÍNDICE DE ADITIVIDADE
# =============================================================================
def calcular_indice_aditividade(mistura):
    """
    Calcula o Índice de Aditividade para toxicidade mista.
    
    Fórmula: IA = Σ (C_i / IDLH_i)
    
    Onde:
    - C_i = Concentração da substância i (ppm)
    - IDLH_i = Valor IDLH da substância i (ppm)
    
    Nota: Asfixiantes (N2, Ar, etc.) não têm IDLH tóxico, mas causam hipóxia.
    Eles são tratados separadamente na função calcular_hipoxia().
    
    Interpretação:
    - IA < 1.0: Ambiente seguro (mesmo com múltiplas substâncias)
    - IA = 1.0: Limite crítico (exatamente no IDLH combinado)
    - IA > 1.0: PERIGO - Concentração excede o limite seguro
    """
    indice_total = 0.0
    detalhes = []
    
    for substancia, concentracao in mistura.items():
        if substancia in SUBSTANCIAS_TOXICAS:
            idlh = SUBSTANCIAS_TOXICAS[substancia].get("idlh", 0)
            
            # Asfixiantes com IDLH = 0 não contribuem para o índice de toxicidade
            # (mas são analisados separadamente para hipóxia)
            if idlh > 0:
                razao = concentracao / idlh
                indice_total += razao
                
                detalhes.append({
                    "Substância": substancia,
                    "Concentração (ppm)": concentracao,
                    "IDLH (ppm)": idlh,
                    "Razão (C/IDLH)": razao
                })
            else:
                # Asfixiante - não contribui para toxicidade, mas será analisado para hipóxia
                detalhes.append({
                    "Substância": substancia,
                    "Concentração (ppm)": concentracao,
                    "IDLH (ppm)": "N/A (Asfixiante)",
                    "Razão (C/IDLH)": 0.0
                })
    
    return indice_total, detalhes

def verificar_protecao_epi(concentracao_ambiente, apf):
    """
    Verifica se o EPI oferece proteção adequada.
    
    Concentração Protegida = Concentração Ambiente / APF
    
    Critério: Concentração Protegida < IDLH
    """
    concentracao_protegida = concentracao_ambiente / apf
    return concentracao_protegida

def calcular_idlh_equivalente(mistura):
    """
    Calcula o IDLH equivalente da mistura usando o Índice de Aditividade.
    
    Se IA = Σ(C_i / IDLH_i) = 1.0, então a mistura está no limite IDLH.
    Portanto, podemos calcular qual concentração total seria equivalente ao IDLH.
    """
    indice, _ = calcular_indice_aditividade(mistura)
    
    # Se o índice é 1.0, estamos exatamente no limite
    # Para calcular o IDLH equivalente, precisamos da concentração total
    concentracao_total = sum(mistura.values())
    
    if indice > 0:
        idlh_equivalente = concentracao_total / indice
    else:
        idlh_equivalente = float('inf')
    
    return idlh_equivalente, indice

def verificar_compatibilidade_filtro(mistura, epi_nome):
    """
    Verifica se o filtro do EPI é adequado para as substâncias presentes.
    Retorna lista de substâncias não protegidas.
    """
    dados_epi = APF_NIOSH[epi_nome]
    filtros_adequados = dados_epi.get("filtros_adequados", [])
    
    # SCBA e Respirador de Linha protegem contra tudo
    if "asfixiante" in filtros_adequados:
        return []
    
    substancias_nao_protegidas = []
    
    for substancia in mistura.keys():
        tipo_contaminante = MAPEAMENTO_TIPO_CONTAMINANTE.get(substancia, "gas_vapor")
        
        if tipo_contaminante not in filtros_adequados:
            substancias_nao_protegidas.append({
                "substancia": substancia,
                "tipo": tipo_contaminante,
                "concentracao": mistura[substancia]
            })
    
    return substancias_nao_protegidas

def calcular_hipoxia(mistura):
    """
    Calcula o deslocamento de oxigênio por gases asfixiantes.
    
    O ar normal tem ~21% de O2 (210000 ppm).
    Gases asfixiantes (N2, CO2, Ar, CH4) deslocam o O2.
    
    O2_restante = 210000 - Σ(concentrações de asfixiantes)
    
    Limite seguro: O2 > 19.5% (195000 ppm)
    Perigo: O2 < 19.5%
    """
    o2_normal = 210000  # ppm (21% do ar)
    concentracao_asfixiantes = 0.0
    asfixiantes_presentes = []
    
    for substancia, concentracao in mistura.items():
        tipo = MAPEAMENTO_TIPO_CONTAMINANTE.get(substancia, "")
        if tipo == "asfixiante":
            concentracao_asfixiantes += concentracao
            asfixiantes_presentes.append({
                "substancia": substancia,
                "concentracao": concentracao
            })
    
    o2_restante = o2_normal - concentracao_asfixiantes
    o2_percentual = (o2_restante / 1000000) * 100  # Converter para porcentagem
    
    return {
        "o2_restante_ppm": o2_restante,
        "o2_restante_percent": o2_percentual,
        "concentracao_asfixiantes": concentracao_asfixiantes,
        "asfixiantes_presentes": asfixiantes_presentes,
        "hipoxia_detectada": o2_restante < 195000  # Limite de 19.5%
    }

# =============================================================================
# 4. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### 🧪 Toxicidade Avançada - Índice de Aditividade")
    st.markdown("Análise de toxicidade mista e verificação de proteção respiratória (APF/NIOSH).")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 O que é o Índice de Aditividade?", expanded=True):
        st.markdown("""
        **O Problema:** Em um acidente químico, raramente há apenas UMA substância no ar. 
        Pode haver uma mistura de gases tóxicos (ex: HCl + Cloro + Amônia).
        
        **A Solução - Índice de Aditividade:**
        O modelo assume que os efeitos tóxicos são **aditivos**. Se você respira 50% do IDLH de HCl 
        e 50% do IDLH de Cloro ao mesmo tempo, o risco total é equivalente a 100% do IDLH.
        
        **Fórmula Matemática:**
        ```
        IA = (C₁/IDLH₁) + (C₂/IDLH₂) + (C₃/IDLH₃) + ...
        ```
        
        **Interpretação:**
        - **IA < 1.0:** ✅ Ambiente seguro (mesmo com múltiplas substâncias)
        - **IA = 1.0:** ⚠️ Limite crítico (exatamente no IDLH combinado)
        - **IA > 1.0:** 🚨 **PERIGO** - Concentração excede o limite seguro
        
        **Exemplo Prático:**
        - HCl: 25 ppm (IDLH = 50 ppm) → Razão = 0.5
        - Cloro: 5 ppm (IDLH = 10 ppm) → Razão = 0.5
        - **IA Total = 0.5 + 0.5 = 1.0** → Limite crítico!
        """)

    with st.expander("🛡️ O que é APF (Assigned Protection Factor)?", expanded=False):
        st.markdown("""
        **APF = Fator de Proteção Atribuído (NIOSH)**
        
        O APF indica **quantas vezes** o EPI reduz a concentração que você respira.
        
        **Exemplo:**
        - Ambiente: 500 ppm de Acetona
        - IDLH da Acetona: 2500 ppm
        - Sem EPI: Você respira 500 ppm (ainda seguro, mas próximo do limite)
        - Com PFF2 (APF=10): Você respira 500/10 = **50 ppm** (muito mais seguro!)
        - Com SCBA (APF=10000): Você respira 500/10000 = **0.05 ppm** (praticamente zero)
        
        **Regra de Ouro:**
        ```
        Concentração Protegida = Concentração Ambiente / APF
        ```
        
        Se a **Concentração Protegida < IDLH**, o EPI é adequado! ✅
        
        **⚠️ IMPORTANTE - Compatibilidade de Filtros:**
        - **PFF2/PFF3:** Protegem APENAS contra **partículas** (poeira, névoa). 
          **NÃO protegem contra gases/vapores!**
        - **Máscaras com Filtros Químicos:** Dependem do **cartucho instalado**.
          Cada cartucho protege contra tipos específicos (ácidos, orgânicos, amônia, etc.).
        - **SCBA/Respirador de Linha:** Proteção total (ar próprio), funcionam para tudo.
        """)

    with st.expander("💨 O que é Hipóxia (Deslocamento de Oxigênio)?", expanded=False):
        st.markdown("""
        **O Problema dos Gases Asfixiantes:**
        
        Alguns gases não são tóxicos por si só, mas **deslocam o oxigênio do ar**.
        Exemplos: Nitrogênio (N₂), Argônio, Dióxido de Carbono (CO₂), Metano (CH₄).
        
        **Como Funciona:**
        - O ar normal tem **21% de oxigênio** (210.000 ppm)
        - Se um gás asfixiante ocupa espaço no ar, ele "empurra" o oxigênio para fora
        - **O₂ Restante = 210.000 ppm - Concentração de Asfixiantes**
        
        **Limites de Segurança:**
        - **> 19.5% O₂:** ✅ Seguro
        - **17-19.5% O₂:** ⚠️ Atenção (sintomas leves)
        - **< 17% O₂:** 🚨 Perigo (perda de consciência em minutos)
        - **< 12% O₂:** 💀 Morte por asfixia
        
        **Exemplo Prático:**
        - Vazamento de Nitrogênio: 50.000 ppm (5%)
        - O₂ Restante = 210.000 - 50.000 = **160.000 ppm (16%)**
        - **RISCO DE ASFIXIA!** Mesmo que o N₂ não seja tóxico.
        
        **Proteção:**
        Apenas **SCBA** ou **Respirador de Linha de Ar** protegem contra hipóxia, 
        pois fornecem ar próprio. Filtros purificadores **NÃO funcionam** para asfixiantes!
        """)

    st.markdown("---")

    # --- SEÇÃO 1: CONFIGURAÇÃO DA MISTURA ---
    st.subheader("1️⃣ Configuração da Mistura Química")
    
    num_substancias = st.number_input(
        "Quantas substâncias estão presentes no ambiente?",
        min_value=1,
        max_value=5,
        value=2,
        step=1,
        help="Selecione quantos gases/vapores tóxicos diferentes estão misturados no ar."
    )

    mistura = {}
    colunas = st.columns(min(num_substancias, 3))
    
    for i in range(num_substancias):
        col = colunas[i % len(colunas)]
        with col:
            substancia = st.selectbox(
                f"Substância {i+1}",
                list(SUBSTANCIAS_TOXICAS.keys()),
                key=f"subst_{i}"
            )
            dados = SUBSTANCIAS_TOXICAS[substancia]
            
            st.caption(f"ℹ️ {dados['desc']}")
            st.caption(f"📊 IDLH: {dados['idlh']} ppm")
            
            concentracao = st.number_input(
                f"Concentração ({substancia})",
                min_value=0.0,
                value=10.0,
                step=0.1,
                format="%.2f",
                key=f"conc_{i}",
                help=f"Concentração medida no ambiente (em ppm). IDLH desta substância: {dados['idlh']} ppm"
            )
            
            mistura[substancia] = concentracao

    st.markdown("---")

    # --- SEÇÃO 2: SELEÇÃO DO EPI ---
    st.subheader("2️⃣ Equipamento de Proteção Individual (EPI)")
    
    epi_selecionado = st.selectbox(
        "Selecione o EPI que será utilizado:",
        list(APF_NIOSH.keys()),
        help="Escolha o tipo de proteção respiratória disponível."
    )
    
    dados_epi = APF_NIOSH[epi_selecionado]
    st.info(f"🛡️ **{epi_selecionado}**\n\nAPF = **{dados_epi['apf']}x**\n\n{dados_epi['desc']}")

    st.markdown("---")

    # --- BOTÃO DE CÁLCULO ---
    if st.button("🧮 Calcular Toxicidade e Verificar Proteção", type="primary", use_container_width=True):
        st.session_state['toxicidade_calc'] = True

    if st.session_state.get('toxicidade_calc', False):
        # Calcular Índice de Aditividade
        indice_total, detalhes = calcular_indice_aditividade(mistura)
        
        # Calcular IDLH equivalente
        concentracao_total = sum(mistura.values())
        idlh_equiv, _ = calcular_idlh_equivalente(mistura)
        
        # Verificar proteção do EPI
        apf_valor = dados_epi['apf']
        concentracao_protegida = verificar_protecao_epi(concentracao_total, apf_valor)
        
        # Determinar o IDLH mais restritivo da mistura para comparação
        idlh_minimo = min([SUBSTANCIAS_TOXICAS[s]["idlh"] for s in mistura.keys()])
        
        st.markdown("---")
        st.markdown("### 📊 Resultados da Análise")

        # --- MÉTRICAS PRINCIPAIS ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if indice_total < 1.0:
                delta_color = "normal"
                delta = f"{(1.0 - indice_total)*100:.1f}% abaixo do limite"
            elif indice_total == 1.0:
                delta_color = "off"
                delta = "Exatamente no limite"
            else:
                delta_color = "inverse"
                delta = f"{(indice_total - 1.0)*100:.1f}% acima do limite"
            
            col1.metric(
                "Índice de Aditividade",
                f"{indice_total:.3f}",
                delta=delta,
                delta_color=delta_color,
                help="IA < 1.0 = Seguro | IA = 1.0 = Limite | IA > 1.0 = Perigoso"
            )
        
        with col2:
            col2.metric(
                "Concentração Total",
                f"{concentracao_total:.2f} ppm",
                help="Soma de todas as concentrações na mistura"
            )
        
        with col3:
            col3.metric(
                "IDLH Equivalente",
                f"{idlh_equiv:.1f} ppm",
                help="IDLH equivalente da mistura completa"
            )

        # --- DIAGNÓSTICO DE SEGURANÇA ---
        st.markdown("#### 🚨 Diagnóstico de Segurança")
        
        if indice_total < 1.0:
            st.success(f"✅ **AMBIENTE SEGURO (Sem EPI):** O Índice de Aditividade ({indice_total:.3f}) está abaixo de 1.0. "
                      f"A mistura de substâncias não excede o limite IDLH combinado. "
                      f"Entretanto, recomenda-se uso de EPI para operações prolongadas.")
        elif indice_total == 1.0:
            st.warning(f"⚠️ **LIMITE CRÍTICO:** O Índice de Aditividade é exatamente 1.0. "
                      f"Você está no limite máximo seguro. **EPI OBRIGATÓRIO!**")
        else:
            st.error(f"🚨 **PERIGO IMINENTE:** O Índice de Aditividade ({indice_total:.3f}) excede 1.0. "
                    f"A mistura é **IMEDIATAMENTE PERIGOSA PARA VIDA E SAÚDE**. "
                    f"**EVACUAÇÃO IMEDIATA** ou uso de **SCBA (APF=10000)** obrigatório!")

        # --- TABELA DETALHADA ---
        st.markdown("#### 📋 Detalhamento por Substância")
        df_detalhes = pd.DataFrame(detalhes)
        df_detalhes['Razão (C/IDLH)'] = df_detalhes['Razão (C/IDLH)'].apply(lambda x: f"{x:.4f}")
        st.dataframe(df_detalhes, use_container_width=True, hide_index=True)

        # --- VERIFICAÇÃO DO EPI ---
        st.markdown("---")
        st.markdown("#### 🛡️ Verificação de Proteção do EPI")
        
        # VERIFICAÇÃO 1: Compatibilidade do Filtro Químico
        substancias_incompatíveis = verificar_compatibilidade_filtro(mistura, epi_selecionado)
        
        if substancias_incompatíveis:
            st.error("🚨 **ALERTA CRÍTICO: FILTRO INADEQUADO!**")
            st.markdown("O EPI selecionado **NÃO protege** contra as seguintes substâncias:")
            
            for item in substancias_incompatíveis:
                tipo_desc = TIPOS_CONTAMINANTES.get(item["tipo"], item["tipo"])
                st.warning(f"❌ **{item['substancia']}** ({item['concentracao']:.2f} ppm) - Tipo: {tipo_desc}")
            
            st.markdown("**⚠️ AÇÃO IMEDIATA:**")
            if "PFF2" in epi_selecionado or "PFF3" in epi_selecionado:
                st.error("Filtros PFF2/PFF3 são **APENAS para partículas**. Para gases/vapores, você precisa de:")
                st.markdown("- Máscara Facial Inteira com **cartucho químico apropriado**")
                st.markdown("- **SCBA** (proteção total)")
                st.markdown("- **Respirador de Linha de Ar** (proteção total)")
            else:
                st.error("Verifique se o **cartucho químico** instalado é adequado para estas substâncias!")
        else:
            st.success("✅ **Filtro Compatível:** O EPI selecionado oferece proteção adequada contra os tipos de contaminantes presentes.")
        
        st.markdown("---")
        
        # VERIFICAÇÃO 2: Cálculo de Proteção por APF
        st.markdown("**📊 Análise de Proteção por APF:**")
        
        # Calcular concentração protegida para cada substância
        protecao_detalhada = []
        for substancia, concentracao in mistura.items():
            # Se o filtro não é compatível, a proteção é ZERO (não funciona)
            tipo_contaminante = MAPEAMENTO_TIPO_CONTAMINANTE.get(substancia, "gas_vapor")
            dados_epi_temp = APF_NIOSH[epi_selecionado]
            filtros_adequados = dados_epi_temp.get("filtros_adequados", [])
            
            # Verificar se o filtro protege contra este tipo
            filtro_compativel = ("asfixiante" in filtros_adequados) or (tipo_contaminante in filtros_adequados)
            
            if filtro_compativel:
                conc_protegida = concentracao / apf_valor
            else:
                conc_protegida = concentracao  # Sem proteção!
            
            idlh_subst = SUBSTANCIAS_TOXICAS.get(substancia, {}).get("idlh", 0)
            
            # Para asfixiantes, verificar hipóxia separadamente
            if idlh_subst == 0 and tipo_contaminante == "asfixiante":
                protecao_adequada = filtro_compativel  # Apenas SCBA/linha protegem contra hipóxia
                idlh_display = "N/A (Asfixiante - ver Hipóxia)"
            elif idlh_subst == 0:
                protecao_adequada = True  # Não tóxico
                idlh_display = "N/A (Não tóxico)"
            else:
                protecao_adequada = conc_protegida < idlh_subst
                idlh_display = f"{idlh_subst:.0f}"
            
            protecao_detalhada.append({
                "Substância": substancia,
                "Tipo": tipo_contaminante,
                "Concentração Ambiente (ppm)": f"{concentracao:.2f}",
                "Concentração Protegida (ppm)": f"{conc_protegida:.4f}" if conc_protegida < concentracao else f"{concentracao:.2f} (SEM PROTEÇÃO)",
                "IDLH (ppm)": idlh_display,
                "Proteção Adequada": "✅ Sim" if protecao_adequada else "❌ Não"
            })
        
        df_protecao = pd.DataFrame(protecao_detalhada)
        st.dataframe(df_protecao, use_container_width=True, hide_index=True)

        # Diagnóstico do EPI
        concentracao_protegida_total = concentracao_total / apf_valor
        protecao_adequada_geral = concentracao_protegida_total < idlh_equiv
        
        st.markdown(f"**Concentração Total Protegida:** {concentracao_protegida_total:.4f} ppm")
        st.markdown(f"**IDLH Equivalente da Mistura:** {idlh_equiv:.1f} ppm")
        
        if protecao_adequada_geral:
            st.success(f"✅ **EPI ADEQUADO:** Com {epi_selecionado} (APF={apf_valor}x), a concentração protegida "
                      f"({concentracao_protegida_total:.4f} ppm) está abaixo do IDLH equivalente ({idlh_equiv:.1f} ppm).")
        else:
            st.error(f"❌ **EPI INADEQUADO:** Com {epi_selecionado} (APF={apf_valor}x), a concentração protegida "
                    f"({concentracao_protegida_total:.4f} ppm) ainda excede o IDLH equivalente ({idlh_equiv:.1f} ppm). "
                    f"**NECESSÁRIO EPI COM MAIOR APF!**")

        # --- VERIFICAÇÃO DE HIPÓXIA (ASFIXIANTES) ---
        resultado_hipoxia = calcular_hipoxia(mistura)
        
        if resultado_hipoxia["asfixiantes_presentes"]:
            st.markdown("---")
            st.markdown("#### 💨 Análise de Hipóxia (Deslocamento de Oxigênio)")
            
            st.markdown(f"**Gases Asfixiantes Detectados:**")
            for item in resultado_hipoxia["asfixiantes_presentes"]:
                st.caption(f"- {item['substancia']}: {item['concentracao']:.2f} ppm")
            
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                col_h1.metric(
                    "Oxigênio Restante",
                    f"{resultado_hipoxia['o2_restante_percent']:.2f}%",
                    f"{resultado_hipoxia['o2_restante_ppm']:.0f} ppm",
                    delta_color="inverse" if resultado_hipoxia['hipoxia_detectada'] else "normal"
                )
            with col_h2:
                col_h2.metric(
                    "Concentração de Asfixiantes",
                    f"{resultado_hipoxia['concentracao_asfixiantes']:.2f} ppm",
                    "Total deslocado"
                )
            
            if resultado_hipoxia['hipoxia_detectada']:
                st.error(f"🚨 **HIPÓXIA DETECTADA:** O oxigênio restante ({resultado_hipoxia['o2_restante_percent']:.2f}%) está abaixo do limite seguro (19.5%). "
                        f"**RISCO DE ASFIXIA!** Mesmo que as substâncias não sejam tóxicas, a falta de oxigênio pode causar:")
                st.markdown("- Perda de consciência em minutos")
                st.markdown("- Dano cerebral irreversível")
                st.markdown("- Morte por asfixia")
                st.warning("**⚠️ AÇÃO:** Apenas SCBA ou Respirador de Linha de Ar oferecem proteção contra hipóxia!")
            elif resultado_hipoxia['o2_restante_percent'] < 20.0:
                st.warning(f"⚠️ **ATENÇÃO:** O oxigênio está próximo do limite (19.5%). Monitore continuamente. "
                          f"Se a concentração de asfixiantes aumentar, o risco de hipóxia se torna crítico.")
            else:
                st.success(f"✅ **Oxigênio Adequado:** O nível de O2 ({resultado_hipoxia['o2_restante_percent']:.2f}%) está dentro da faixa segura.")
        
        # --- GRÁFICO VISUAL ---
        st.markdown("---")
        st.markdown("#### 📈 Visualização do Índice de Aditividade")
        
        # Preparar dados para o gráfico
        df_grafico = pd.DataFrame({
            'Substância': [d['Substância'] for d in detalhes],
            'Razão (C/IDLH)': [d['Razão (C/IDLH)'] for d in detalhes],
            'Contribuição (%)': [(d['Razão (C/IDLH)'] / indice_total * 100) if indice_total > 0 else 0 for d in detalhes]
        })
        
        # Verificar se há grande disparidade nas razões (para decidir escala logarítmica)
        razoes = df_grafico['Razão (C/IDLH)'].values
        razao_max = razoes.max()
        razao_min = razoes[razoes > 0].min() if (razoes > 0).any() else 1.0
        
        # Se a diferença for maior que 100x, usar escala logarítmica
        usar_log = (razao_max / razao_min) > 100 if razao_min > 0 else False
        
        # Gráfico de barras
        if usar_log:
            # Escala logarítmica
            chart = alt.Chart(df_grafico).mark_bar().encode(
                x=alt.X('Substância:N', title="Substância", sort='-y'),
                y=alt.Y('Razão (C/IDLH):Q', 
                       title="Razão (Concentração / IDLH) - Escala Logarítmica",
                       scale=alt.Scale(type='log', nice=True)),
                color=alt.Color('Razão (C/IDLH):Q', 
                              scale=alt.Scale(type='log', domain=[razao_min*0.1, 1, razao_max*10],
                                            range=['green', 'orange', 'red']),
                              legend=None),
                tooltip=['Substância', alt.Tooltip('Razão (C/IDLH)', format='.4f'), 
                        alt.Tooltip('Contribuição (%)', format='.1f')]
            ).properties(height=300)
            
            st.caption("📊 **Escala Logarítmica Ativada:** As concentrações são muito díspares. "
                      "A escala log permite visualizar todas as substâncias, mesmo as de baixa concentração (mas altamente letais).")
        else:
            # Escala linear normal
            chart = alt.Chart(df_grafico).mark_bar().encode(
                x=alt.X('Substância:N', title="Substância", sort='-y'),
                y=alt.Y('Razão (C/IDLH):Q', title="Razão (Concentração / IDLH)"),
                color=alt.Color('Razão (C/IDLH):Q', 
                              scale=alt.Scale(domain=[0, 1, max(razoes.max(), 1.5)],
                                            range=['green', 'orange', 'red']),
                              legend=None),
                tooltip=['Substância', 'Razão (C/IDLH)', alt.Tooltip('Contribuição (%)', format='.1f')]
            ).properties(height=300)
        
        # Linha de referência (IA = 1.0) - apenas se não for log
        if not usar_log:
            linha_limite = alt.Chart(pd.DataFrame({'limite': [1.0]})).mark_rule(
                color='red', strokeDash=[5, 5], strokeWidth=2
            ).encode(y='limite:Q')
            
            # Texto na linha
            texto_limite = alt.Chart(pd.DataFrame({'x': [len(df_grafico)-1], 'y': [1.0], 'text': ['Limite Crítico (IA=1.0)']})).mark_text(
                align='left', dx=5, color='red', fontSize=12
            ).encode(x='x:Q', y='y:Q', text='text:N')
            
            st.altair_chart(chart + linha_limite + texto_limite, use_container_width=True)
        else:
            st.altair_chart(chart, use_container_width=True)
        
        st.caption("💡 Cada barra mostra a contribuição individual de cada substância para o Índice de Aditividade total. "
                  "Substâncias com baixa concentração mas IDLH muito baixo (ex: Fosgênio) podem ser mais perigosas que outras com alta concentração.")

        # --- RECOMENDAÇÕES ---
        st.markdown("---")
        st.markdown("#### 💡 Recomendações Táticas")
        
        if indice_total < 0.5:
            st.info("✅ **Situação Controlada:** O ambiente está bem abaixo do limite. "
                   "EPI básico (PFF2) é suficiente para operações curtas.")
        elif indice_total < 1.0:
            st.info("⚠️ **Atenção:** Embora abaixo do limite, recomenda-se EPI de média proteção "
                   "(Máscara Facial Inteira ou PAPR) para operações prolongadas.")
        elif indice_total < 2.0:
            st.warning("🚨 **Alto Risco:** EPI de alta proteção obrigatório. Considere SCBA ou Respirador de Linha de Ar.")
        else:
            st.error("💀 **Extremo Perigo:** Apenas SCBA (APF=10000) oferece proteção adequada. "
                    "Evacuação imediata recomendada para pessoal não essencial.")
