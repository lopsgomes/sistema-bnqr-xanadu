import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================================================================
# 1. PARÂMETROS TÁTICOS DE REFERÊNCIA
# =============================================================================
TIPOS_DECON = {
    "Descontaminação Técnica (Equipes)": {
        "tempo_medio": 10,  # minutos por pessoa
        "desc": "Processo minucioso para operadores com roupas nível A/B. Requer escovação, múltiplas estações e verificação de eficácia."
    },
    "Descontaminação em Massa (Público)": {
        "tempo_medio": 3,  # minutos por pessoa
        "desc": "Banho rápido (chuveirinho) focado em remover o grosso do contaminante da pele e roupas. Processo simplificado para grandes volumes."
    },
    "Vítimas Não-Ambulantes (Maca)": {
        "tempo_medio": 15,  # minutos por pessoa
        "desc": "Vítimas inconscientes ou feridas. Requer 2 a 4 operadores para manipular a vítima na linha. Processo mais demorado e complexo."
    }
}

# =============================================================================
# 2. BANCO DE DADOS: CONTAMINANTES E CARACTERÍSTICAS DE DESCONTAMINAÇÃO
# =============================================================================
# Informações sobre diferentes tipos de contaminantes e suas características
# que influenciam o processo de descontaminação
CONTAMINANTES_DECON = {
    "Agentes Químicos Voláteis (Gases/Vapores)": {
        "tipo": "Gas/Vapor",
        "persistencia": "Baixa",
        "metodo": "Ventilação e remoção de roupas. Lavagem com água e sabão.",
        "tempo_extra": 0,
        "desc": "Gases e vapores voláteis (ex: Cloro, Amônia, Monóxido de Carbono). Descontaminação rápida, foco em remoção de roupas e ventilação."
    },
    "Agentes Químicos Persistentes (Líquidos)": {
        "tipo": "Líquido",
        "persistencia": "Alta",
        "metodo": "Lavagem com água e sabão neutro. Múltiplas passagens. Remoção completa de roupas.",
        "tempo_extra": 2,
        "desc": "Líquidos persistentes (ex: Agentes VX, Mostarda de Enxofre, Pesticidas). Requer descontaminação mais demorada e cuidadosa."
    },
    "Agentes Biológicos (Bactérias/Vírus)": {
        "tipo": "Biológico",
        "persistencia": "Média",
        "metodo": "Lavagem com água e sabão. Desinfecção com hipoclorito de sódio (0.5%) ou solução desinfetante.",
        "tempo_extra": 1,
        "desc": "Agentes biológicos (ex: Antraz, Peste, Vírus). Descontaminação com desinfetantes apropriados."
    },
    "Agentes Radiológicos (Partículas)": {
        "tipo": "Radiológico",
        "persistencia": "Variável",
        "metodo": "Remoção mecânica (escovação, aspiração). Lavagem com água e sabão. Monitoramento com contador Geiger.",
        "tempo_extra": 1,
        "desc": "Material radioativo particulado (ex: Césio-137, Cobalto-60 em pó). Requer remoção mecânica e monitoramento."
    },
    "Agentes Corrosivos (Ácidos/Bases)": {
        "tipo": "Corrosivo",
        "persistencia": "Média",
        "metodo": "Lavagem copiosa com água. Neutralização se apropriado. Remoção imediata de roupas contaminadas.",
        "tempo_extra": 1,
        "desc": "Ácidos e bases corrosivos (ex: Ácido Sulfúrico, Hidróxido de Sódio). Lavagem imediata e copiosa essencial."
    },
    "Agentes Asfixiantes (Gases Inertes)": {
        "tipo": "Gas",
        "persistencia": "Baixa",
        "metodo": "Ventilação. Remoção de roupas. Oxigenação. Não requer descontaminação química extensa.",
        "tempo_extra": 0,
        "desc": "Gases asfixiantes (ex: Nitrogênio, Argônio, CO2). Foco em oxigenação e ventilação, não descontaminação química."
    },
    "Agentes Neurotóxicos (Organofosforados)": {
        "tipo": "Químico",
        "persistencia": "Alta",
        "metodo": "Lavagem imediata com água e sabão. Descontaminação com hipoclorito de cálcio ou solução alcalina.",
        "tempo_extra": 3,
        "desc": "Agentes neurotóxicos (ex: Sarin, VX, Tabun). Extremamente perigosos. Descontaminação imediata e cuidadosa essencial."
    },
    "Agentes Vesicantes (Mostarda/Lewisita)": {
        "tipo": "Químico",
        "persistencia": "Muito Alta",
        "metodo": "Lavagem imediata com água e sabão. Descontaminação com hipoclorito de cálcio. Múltiplas passagens.",
        "tempo_extra": 4,
        "desc": "Agentes vesicantes (ex: Mostarda de Enxofre, Lewisita). Altamente persistentes. Descontaminação demorada e complexa."
    },
    "Agentes Irritantes (Lacrimogêneos)": {
        "tipo": "Químico",
        "persistencia": "Baixa",
        "metodo": "Lavagem com água. Ventilação. Remoção de roupas. Descontaminação rápida.",
        "tempo_extra": 0,
        "desc": "Agentes irritantes (ex: CS, CN, Cloropicrina). Descontaminação relativamente rápida."
    },
    "Agentes Incapacitantes (BZ/Agentes Psicoquímicos)": {
        "tipo": "Químico",
        "persistencia": "Média",
        "metodo": "Lavagem com água e sabão. Descontaminação com hipoclorito de sódio.",
        "tempo_extra": 2,
        "desc": "Agentes incapacitantes (ex: BZ, Agentes Psicoquímicos). Descontaminação padrão com desinfetantes."
    },
    "Pesticidas Organofosforados": {
        "tipo": "Químico",
        "persistencia": "Alta",
        "metodo": "Lavagem imediata com água e sabão. Descontaminação com solução alcalina ou hipoclorito.",
        "tempo_extra": 3,
        "desc": "Pesticidas organofosforados (ex: Paration, Malation). Similar a agentes neurotóxicos. Descontaminação cuidadosa necessária."
    },
    "Metais Pesados (Chumbo, Mercúrio)": {
        "tipo": "Químico",
        "persistencia": "Muito Alta",
        "metodo": "Remoção mecânica (escovação). Lavagem com água e sabão. Descontaminação com EDTA ou quelantes se apropriado.",
        "tempo_extra": 2,
        "desc": "Metais pesados em forma particulada ou líquida. Altamente persistentes. Requer remoção mecânica cuidadosa."
    },
    "Agentes Cianogênicos": {
        "tipo": "Químico",
        "persistencia": "Baixa",
        "metodo": "Lavagem imediata com água. Descontaminação com hipoclorito de sódio. Ventilação.",
        "tempo_extra": 1,
        "desc": "Agentes cianogênicos (ex: Cianeto de Hidrogênio, Cianeto de Sódio). Descontaminação imediata essencial."
    },
    "Agentes Tóxicos Industriais (TICs)": {
        "tipo": "Químico",
        "persistencia": "Variável",
        "metodo": "Depende do agente específico. Geralmente lavagem com água e sabão. Consultar guias específicos.",
        "tempo_extra": 1,
        "desc": "Tóxicos Industriais Comuns (ex: Cloro, Amônia, Formaldeído). Descontaminação padrão, mas variável por agente."
    },
    "Agentes Biológicos de Alta Letalidade": {
        "tipo": "Biológico",
        "persistencia": "Média-Alta",
        "metodo": "Lavagem com água e sabão. Desinfecção rigorosa com hipoclorito de sódio (0.5-1%). Isolamento.",
        "tempo_extra": 2,
        "desc": "Agentes biológicos de alta letalidade (ex: Ebola, Antraz, Peste). Descontaminação rigorosa e isolamento necessários."
    },
    "Material Radioativo Líquido": {
        "tipo": "Radiológico",
        "persistencia": "Alta",
        "metodo": "Remoção imediata de roupas. Lavagem copiosa com água e sabão. Monitoramento contínuo.",
        "tempo_extra": 2,
        "desc": "Material radioativo em forma líquida (ex: Iodo-131 líquido, soluções radioativas). Persistente, requer lavagem cuidadosa."
    },
    "Agentes de Guerra Química (Categoria A)": {
        "tipo": "Químico",
        "persistencia": "Muito Alta",
        "metodo": "Descontaminação imediata e rigorosa. Múltiplas estações. Hipoclorito de cálcio ou solução alcalina.",
        "tempo_extra": 5,
        "desc": "Agentes de guerra química de alta prioridade (ex: VX, Sarin, Mostarda). Descontaminação mais demorada e complexa."
    },
    "Fumaça Tóxica (Combustão)": {
        "tipo": "Particulado",
        "persistencia": "Média",
        "metodo": "Remoção de roupas. Lavagem com água e sabão. Ventilação. Tratamento de inalação se necessário.",
        "tempo_extra": 1,
        "desc": "Fumaça tóxica de combustão (ex: CO, HCN, partículas). Descontaminação padrão com foco em inalação."
    },
    "Agentes Desconhecidos/Não Identificados": {
        "tipo": "Desconhecido",
        "persistencia": "Desconhecida",
        "metodo": "Descontaminação universal: Remoção de roupas, lavagem com água e sabão, desinfecção com hipoclorito.",
        "tempo_extra": 3,
        "desc": "Agente não identificado. Aplicar protocolo de descontaminação universal conservador."
    }
}

# =============================================================================
# 3. MOTOR DE LOGÍSTICA (TEORIA DAS FILAS SIMPLIFICADA)
# =============================================================================
def simular_decon(num_vitimas, num_linhas, tempo_por_pessoa):
    """
    Calcula a dinâmica de processamento da descontaminação usando teoria de filas simplificada.
    
    Parâmetros:
        num_vitimas: Número total de vítimas a serem descontaminadas
        num_linhas: Número de linhas de descontaminação disponíveis
        tempo_por_pessoa: Tempo médio de descontaminação por pessoa (minutos)
    
    Retorna:
        Tupla: (DataFrame com evolução temporal, vazão total por hora, tempo total em horas)
    """
    # Capacidade de processamento (Vítimas por hora por linha)
    vazao_por_linha = 60 / tempo_por_pessoa
    vazao_total_hora = vazao_por_linha * num_linhas
    
    # Tempo total para processar todas as vítimas (em horas)
    tempo_total_horas = num_vitimas / vazao_total_hora if vazao_total_hora > 0 else float('inf')
    
    # Gerar dados para o gráfico de evolução temporal
    # Criar pontos de tempo a cada 0.5 horas até o tempo total
    horas = np.arange(0, min(tempo_total_horas + 1, 24), 0.5)  # Limitar a 24 horas
    if horas[-1] < tempo_total_horas:
        horas = np.append(horas, min(tempo_total_horas, 24))
        
    processadas = [min(num_vitimas, vazao_total_hora * h) for h in horas]
    pendentes = [max(0, num_vitimas - p) for p in processadas]
    
    df_evolucao = pd.DataFrame({
        'Tempo (Horas)': horas,
        'Vítimas Processadas': processadas,
        'Vítimas na Fila (Zona Suja)': pendentes
    })
    
    return df_evolucao, vazao_total_hora, tempo_total_horas

# =============================================================================
# 4. INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Corredor de Descontaminação")
    st.markdown("**Dimensionamento de Corredores de Descontaminação e Análise de Tempo de Resposta Operacional**")
    st.markdown("---")

    with st.expander("Fundamentos da Descontaminação em Incidentes BNQR", expanded=True):
        st.markdown("""
        **O Desafio da Descontaminação:**
        
        Em incidentes envolvendo agentes biológicos, químicos ou radiológicos, a descontaminação é um 
        componente crítico da resposta. O processo remove ou neutraliza contaminantes da pele, roupas e 
        equipamentos, prevenindo exposição adicional e contaminação secundária.
        
        **O Gargalo Operacional:**
        
        A descontaminação frequentemente representa o "gargalo" da operação de resposta. Se o processo for 
        muito lento, as vítimas esperam excessivamente na "zona suja" (área contaminada), aumentando o 
        risco de exposição prolongada e deterioração do estado de saúde. Se for muito rápido, a limpeza 
        pode ser ineficaz, permitindo que contaminantes permaneçam e causem danos adicionais.
        
        **Tipos de Descontaminação:**
        
        1. **Descontaminação Técnica (Equipes):** Processo minucioso para operadores com equipamentos de 
           proteção individual (EPI) nível A ou B. Requer múltiplas estações, escovação cuidadosa e 
           verificação de eficácia. Tempo médio: 10 minutos por pessoa.
        
        2. **Descontaminação em Massa (Público):** Processo simplificado para grandes volumes de vítimas. 
           Foco em remoção rápida do grosso do contaminante através de banho com chuveirinho. Tempo médio: 
           3 minutos por pessoa.
        
        3. **Vítimas Não-Ambulantes (Maca):** Processo para vítimas inconscientes ou feridas que não podem 
           se descontaminar sozinhas. Requer 2 a 4 operadores para manipular a vítima. Tempo médio: 15 minutos 
           por pessoa.
        
        **Dimensionamento de Recursos:**
        
        Este módulo utiliza teoria de filas simplificada para calcular:
        - Número de linhas de descontaminação necessárias
        - Tempo total para processar todas as vítimas
        - Evolução temporal do processamento
        - Capacidade do sistema (vítimas por hora)
        
        **Fatores que Influenciam o Tempo:**
        
        - Tipo de contaminante (volátil vs. persistente)
        - Tipo de descontaminação (técnica vs. massa)
        - Estado das vítimas (ambulantes vs. não-ambulantes)
        - Recursos disponíveis (número de linhas, pessoal treinado)
        - Condições ambientais (temperatura, vento)
        
        **Limitações do Modelo:**
        
        Este modelo assume processamento linear e constante. Na realidade, fatores como fadiga de operadores, 
        variações na complexidade de casos individuais, e necessidade de retriagem podem alterar significativamente 
        os tempos. Sempre considere margem de segurança e monitore o progresso real.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros do Cenário")
        
        total_vitimas = st.number_input("Total de Vítimas Afetadas", 
                                       value=100, min_value=1, step=10,
                                       help="Número total de pessoas que necessitam descontaminação.")
        
        tipo_alvo = st.selectbox("Tipo de Descontaminação", 
                                list(TIPOS_DECON.keys()),
                                help="Selecione o tipo de processo de descontaminação baseado no perfil das vítimas.")
        tempo_base = TIPOS_DECON[tipo_alvo]['tempo_medio']
        
        st.info(f"**Tempo Estimado:** {tempo_base} minutos por pessoa\n\n"
               f"**Descrição:** {TIPOS_DECON[tipo_alvo]['desc']}")
        
        # Seleção de contaminante (opcional, para ajuste de tempo)
        st.markdown("---")
        st.markdown("**Tipo de Contaminante (Opcional - para ajuste de tempo)**")
        contaminante = st.selectbox("Contaminante Envolvido", 
                                   ["Não especificado"] + list(CONTAMINANTES_DECON.keys()),
                                   help="Selecione o tipo de contaminante para ajustar o tempo de descontaminação se necessário.")
        
        if contaminante != "Não especificado":
            dados_cont = CONTAMINANTES_DECON[contaminante]
            st.caption(f"**Tipo:** {dados_cont['tipo']} | **Persistência:** {dados_cont['persistencia']}")
            st.caption(f"**Método:** {dados_cont['metodo']}")
            tempo_ajustado = tempo_base + dados_cont['tempo_extra']
            st.caption(f"**Tempo Ajustado:** {tempo_ajustado} min/pessoa (base: {tempo_base} + extra: {dados_cont['tempo_extra']})")
        else:
            tempo_ajustado = tempo_base

    with col2:
        st.subheader("Recursos Disponíveis")
        
        linhas = st.slider("Número de Linhas de Descontaminação Ativas", 
                         1, 20, 2, 
                         help="Cada linha é uma tenda ou corredor de banho completo com equipe de operadores.")
        
        tempo_manual = st.number_input("Ajuste Manual de Tempo (min/pessoa)", 
                                     value=float(tempo_ajustado), min_value=0.5, step=0.5,
                                     help="Ajuste manual do tempo de descontaminação por pessoa se necessário.")
        
        vazao_sistema = (60 / tempo_manual) * linhas if tempo_manual > 0 else 0
        st.metric("Capacidade do Sistema", f"{vazao_sistema:.1f} vítimas/hora",
                 f"{vazao_sistema/60:.2f} vítimas/minuto",
                 help="Capacidade total de processamento do sistema de descontaminação")

    # Botão de Ação
    if 'decon_calc' not in st.session_state:
        st.session_state['decon_calc'] = False
    
    if st.button("Calcular Fluxo de Descontaminação", type="primary", use_container_width=True):
        st.session_state['decon_calc'] = True

    if st.session_state['decon_calc']:
        df, vazao, total_h = simular_decon(total_vitimas, linhas, tempo_manual)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        m1, m2, m3 = st.columns(3)
        m1.metric("Tempo Total Estimado", f"{total_h:.1f} Horas", f"{total_h*60:.0f} minutos",
                 help="Tempo total necessário para processar todas as vítimas")
        m2.metric("Vazão do Sistema", f"{vazao:.0f} vítimas/hora",
                 help="Capacidade total de processamento do sistema")
        m3.metric("Eficiência por Linha", f"{60/tempo_manual:.1f} vítimas/hora",
                 help="Capacidade de processamento por linha individual")

        # Análise de Capacidade
        st.markdown("#### Análise de Capacidade e Tempo de Resposta")
        
        if total_h > 2.0:
            st.error(f"**ALERTA DE SATURAÇÃO:** A operação levará mais de 2 horas ({total_h:.1f} horas). "
                    f"Muitas vítimas podem sofrer danos graves aguardando na zona suja. "
                    f"**Recomendação:** Considere aumentar significativamente o número de linhas ou otimizar o processo.")
        elif total_h > 1.0:
            st.warning(f"**OPERAÇÃO CRÍTICA:** Tempo de espera elevado ({total_h:.1f} horas). "
                      f"Monitore sinais vitais das vítimas na fila. Considere adicionar linhas adicionais se possível.")
        else:
            st.success(f"**FLUXO ADEQUADO:** Operação eficiente para o volume de vítimas. "
                      f"Tempo total estimado: {total_h:.1f} horas.")

        # Gráfico de Evolução
        st.markdown("---")
        st.markdown("#### Evolução Temporal do Processamento")
        st.caption("Gráfico mostrando a evolução do número de vítimas processadas e aguardando na fila ao longo do tempo.")
        
        df_melt = df.melt('Tempo (Horas)', var_name='Status', value_name='Quantidade')
        
        chart = alt.Chart(df_melt).mark_area(opacity=0.7, interpolate='monotone').encode(
            x=alt.X('Tempo (Horas):Q', title="Tempo (Horas)", scale=alt.Scale(domain=[0, min(total_h + 1, 24)])),
            y=alt.Y('Quantidade:Q', title="Número de Vítimas"),
            color=alt.Color('Status:N', 
                          scale=alt.Scale(
                              domain=['Vítimas Processadas', 'Vítimas na Fila (Zona Suja)'], 
                              range=['#2ecc71', '#e74c3c']
                          ),
                          legend=alt.Legend(title="Status")),
            tooltip=[alt.Tooltip('Tempo (Horas)', format='.1f'),
                    alt.Tooltip('Status', title='Status'),
                    alt.Tooltip('Quantidade', format=',', title='Número de Vítimas')]
        ).properties(height=350, title="Evolução do Processamento de Descontaminação").interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        st.caption("**Interpretação:** A área verde representa vítimas já descontaminadas (zona limpa). "
                  "A área vermelha representa vítimas ainda aguardando na zona suja (área contaminada). "
                  "O objetivo é minimizar a área vermelha o mais rápido possível.")
        
        # Tabela de resultados
        st.markdown("#### Tabela de Evolução Temporal")
        st.caption("Dados detalhados da evolução do processamento ao longo do tempo.")
        
        df_display = df.copy()
        df_display['Tempo (Horas)'] = df_display['Tempo (Horas)'].apply(lambda x: f"{x:.1f}")
        df_display['Vítimas Processadas'] = df_display['Vítimas Processadas'].apply(lambda x: f"{int(x):,}")
        df_display['Vítimas na Fila (Zona Suja)'] = df_display['Vítimas na Fila (Zona Suja)'].apply(lambda x: f"{int(x):,}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Recomendações operacionais
        st.markdown("---")
        with st.expander("Recomendações Operacionais", expanded=False):
            st.markdown(f"""
            **Cenário Analisado:**
            - **Total de Vítimas:** {total_vitimas}
            - **Tipo de Descontaminação:** {tipo_alvo}
            - **Tempo por Pessoa:** {tempo_manual:.1f} minutos
            - **Número de Linhas:** {linhas}
            - **Tempo Total Estimado:** {total_h:.1f} horas ({total_h*60:.0f} minutos)
            - **Capacidade do Sistema:** {vazao:.0f} vítimas/hora
            
            **Recomendações:**
            
            1. **Organização da Cena:**
               - Estabelecer zona suja (contaminada) claramente demarcada
               - Estabelecer zona limpa (descontaminada) separada
               - Estabelecer zona de controle entre as duas
               - Implementar sistema de triagem antes da descontaminação
            
            2. **Recursos Necessários:**
               - **Linhas de Descontaminação:** {linhas} linhas ativas
               - **Pessoal:** Aproximadamente {linhas * 3} a {linhas * 4} operadores (3-4 por linha)
               - **Equipamentos:** Tendas/chuveiros, água, sabão, desinfetantes apropriados
               - **Monitoramento:** Equipamentos de detecção para verificar eficácia da descontaminação
            
            3. **Gestão de Fila:**
               - Implementar sistema de numeração ou identificação
               - Priorizar vítimas críticas (vermelhas) para descontaminação rápida
               - Monitorar sinais vitais de vítimas aguardando
               - Estabelecer área de espera protegida na zona suja
            
            4. **Otimização:**
               - Se tempo total > 2 horas: Considere dobrar o número de linhas
               - Otimize o processo removendo etapas desnecessárias
               - Considere descontaminação em massa para vítimas verdes (leves)
               - Implemente sistema de retriagem após descontaminação
            
            5. **Segurança:**
               - Operadores devem usar EPI apropriado (nível C no mínimo)
               - Implementar rotação de pessoal para evitar fadiga
               - Monitorar condições ambientais (temperatura, vento)
               - Ter plano de evacuação de emergência para a equipe
            
            6. **Documentação:**
               - Registrar todas as vítimas processadas
               - Manter controle de tempo de espera
               - Documentar eficácia da descontaminação
               - Reportar problemas ou ineficiências
            
            **Importante:** Este modelo assume processamento linear e constante. Na realidade, fatores como 
            fadiga, variações na complexidade de casos, e necessidade de retriagem podem alterar os tempos. 
            Monitore o progresso real e ajuste conforme necessário.
            """)