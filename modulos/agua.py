import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================================================================
# BANCO DE DADOS: AGENTES DE CONTAMINAÇÃO HÍDRICA
# =============================================================================
# LD50 (Lethal Dose 50%): Dose que mata 50% da população em testes com animais
# (mg/kg de peso corporal). Valores baseados em literatura toxicológica.
# Limite Potável: Baseado em padrões CONAMA, OMS e EPA (mg/L).
CONTAMINANTES_AGUA = {
    "Aldicarb (Chumbinho)": {
        "tipo": "Químico (Pesticida)",
        "LD50": 0.9, 
        "limite_potavel": 0.01,
        "desc": "Carbamato ilegal muito comum no Brasil. Bloqueia a colinesterase. Extremamente letal."
    },
    "Arsênio (Trióxido)": {
        "tipo": "Químico",
        "LD50": 14.0, 
        "limite_potavel": 0.01,
        "desc": "Veneno insípido e inodoro. Usado historicamente para envenenamento em massa."
    },
    "Bário (Cloreto Solúvel)": {
        "tipo": "Químico",
        "LD50": 118.0, 
        "limite_potavel": 0.7,
        "desc": "Afeta o coração (arritmias) e músculos. Sais de bário são muito solúveis."
    },
    "Cádmio": {
        "tipo": "Químico (Metal Pesado)",
        "LD50": 225.0, 
        "limite_potavel": 0.005,
        "desc": "Altamente tóxico para os rins. Intoxicação aguda causa vômitos severos e choque."
    },
    "Césio-137 (Solúvel - Cloreto)": {
        "tipo": "Radiológico",
        "LD50": 1000.0, # (Risco radiológico preponderante sobre o químico)
        "limite_potavel": 0.0, 
        "desc": "Se dissolvido, quem bebe se torna radioativo internamente. Danos celulares massivos."
    },
    "Cianeto de Potássio": {
        "tipo": "Químico",
        "LD50": 2.5, 
        "limite_potavel": 0.07,
        "desc": "O veneno clássico. Bloqueia a respiração celular. Solúvel e invisível na água."
    },
    "Cloro (Superdosagem)": {
        "tipo": "Químico",
        "LD50": 850.0, # (Hipoclorito concentrado)
        "limite_potavel": 5.0,
        "desc": "Sabotagem operacional (despejar o tanque de tratamento puro). Queimaduras internas severas."
    },
    "Dioxina (TCDD)": {
        "tipo": "Químico",
        "LD50": 0.02, # Extremamente potente
        "limite_potavel": 0.00000003,
        "desc": "O veneno do Agente Laranja. Causa cloracne e falência hepática aguda em altas doses."
    },
    "Estricnina": {
        "tipo": "Químico",
        "LD50": 2.0, 
        "limite_potavel": 0.0,
        "desc": "Pesticida antigo. Causa convulsões violentas (tetania). Gosto muito amargo."
    },
    "Fentanil": {
        "tipo": "Opioide Sintético",
        "LD50": 0.03, 
        "limite_potavel": 0.0,
        "desc": "Ameaça moderna. 50x mais forte que heroína. Parada respiratória imediata."
    },
    "Fluoroacetato de Sódio (1080)": {
        "tipo": "Químico",
        "LD50": 2.0, 
        "limite_potavel": 0.0,
        "desc": "Rodenticida inodoro e insípido. Bloqueia o ciclo de Krebs. Sem antídoto eficaz."
    },
    "Flúor (Excesso)": {
        "tipo": "Químico",
        "LD50": 50.0, 
        "limite_potavel": 1.5,
        "desc": "Sabotagem em estações de tratamento. Ocorre se o sistema de fluoretação for manipulado."
    },
    "LSD (Alucinógeno)": {
        "tipo": "Psicotrópico",
        "LD50": 100.0, 
        "limite_potavel": 0.0,
        "desc": "Cenário de desorganização social. Não mata, mas incapacita a população com alucinações."
    },
    "Mercúrio (Orgânico/Metil)": {
        "tipo": "Químico",
        "LD50": 25.0, 
        "limite_potavel": 0.001,
        "desc": "Dano neurológico severo. Bioacumulativo, mas em ataque agudo causa falência renal."
    },
    "Nicotina (Pura)": {
        "tipo": "Químico",
        "LD50": 6.5, 
        "limite_potavel": 0.0,
        "desc": "Extraída de tabaco. Paralisia respiratória rápida. Gosto amargo e picante."
    },
    "Paraquat": {
        "tipo": "Herbicida",
        "LD50": 35.0, 
        "limite_potavel": 0.01,
        "desc": "Causa fibrose pulmonar irreversível dias após a ingestão. Morte lenta e dolorosa."
    },
    "Polônio-210": {
        "tipo": "Radiológico",
        "LD50": 0.00005, # 50 nanogramas (Estimativa)
        "limite_potavel": 0.0,
        "desc": "O veneno do espião (Litvinenko). Emissor Alfa massivo. Destrói o corpo por dentro."
    },
    "Ricina (Toxina)": {
        "tipo": "Biotoxina",
        "LD50": 0.02, # Ingestão
        "limite_potavel": 0.0001,
        "desc": "Toxina da mamona. Causa falência de órgãos e hemorragia gástrica severa."
    },
    "Saxitoxina": {
        "tipo": "Biotoxina (Marinha)",
        "LD50": 0.01, 
        "limite_potavel": 0.000003,
        "desc": "Veneno da maré vermelha. Paralisia muscular imediata. Resistente à fervura."
    },
    "Tálio (Sulfato)": {
        "tipo": "Químico",
        "LD50": 12.0, 
        "limite_potavel": 0.002,
        "desc": "O 'Veneno dos Envenenadores'. Insípido. Causa queda de cabelo e dor excruciante."
    },
    "Tetrodotoxina (TTX)": {
        "tipo": "Biotoxina (Baiacu)",
        "LD50": 0.33, 
        "limite_potavel": 0.0,
        "desc": "Bloqueador de canal de sódio. A vítima fica paralisada consciente até morrer."
    },
    "Toxina Botulínica A": {
        "tipo": "Biotoxina",
        "LD50": 0.000001, 
        "limite_potavel": 0.0000001,
        "desc": "A substância mais tóxica conhecida. Uma grama poderia contaminar um reservatório inteiro."
    },
    "Varfarina (Superdosagem)": {
        "tipo": "Químico",
        "LD50": 180.0, 
        "limite_potavel": 0.03,
        "desc": "Anticoagulante (Veneno de rato). Doses massivas causam hemorragia interna espontânea."
    },
    "VX (Agente de Guerra)": {
        "tipo": "Químico (Neurotóxico)",
        "LD50": 0.005, 
        "limite_potavel": 0.0,
        "desc": "Persistente em água fria e pH neutro. Letalidade extrema em doses minúsculas."
    },
    "Chumbo (Pb)": {
        "tipo": "Químico (Metal Pesado)",
        "LD50": 450.0,
        "limite_potavel": 0.01,
        "desc": "Neurotóxico cumulativo. Causa danos neurológicos permanentes, especialmente em crianças. Bioacumulativo."
    },
    "Cromo Hexavalente (CrVI)": {
        "tipo": "Químico (Metal Pesado)",
        "LD50": 150.0,
        "limite_potavel": 0.05,
        "desc": "Carcinogênico classe 1 (IARC). Causa danos ao DNA e câncer de pulmão. Muito mais tóxico que cromo trivalente."
    },
    "Benzeno": {
        "tipo": "Químico (Hidrocarboneto Aromático)",
        "LD50": 930.0,
        "limite_potavel": 0.01,
        "desc": "Carcinogênico hematológico. Causa leucemia e anemia aplástica. Volátil, mas pode persistir em água contaminada."
    },
    "Tricloroetileno (TCE)": {
        "tipo": "Químico (Solvente Clorado)",
        "LD50": 2400.0,
        "limite_potavel": 0.07,
        "desc": "Solvente industrial comum. Carcinogênico hepático e renal. Neurotóxico. Muito persistente em aquíferos."
    },
    "Metanol": {
        "tipo": "Químico (Álcool Tóxico)",
        "LD50": 3400.0,
        "limite_potavel": 0.5,
        "desc": "Metabolizado em formaldeído e ácido fórmico. Causa cegueira e acidose metabólica severa. Odor suave, difícil detecção."
    },
    "Etilenoglicol": {
        "tipo": "Químico (Glicol)",
        "LD50": 4700.0,
        "limite_potavel": 0.2,
        "desc": "Anticongelante comum. Metabolizado em ácido oxálico, causando insuficiência renal aguda e cristalização nos rins."
    },
    "Amônia (NH3)": {
        "tipo": "Químico (Alcalino)",
        "LD50": 350.0,
        "limite_potavel": 1.5,
        "desc": "Corrosivo para tecidos. Em altas concentrações causa queimaduras internas e edema pulmonar. Odor característico forte."
    },
    "Formaldeído": {
        "tipo": "Químico (Aldeído)",
        "LD50": 800.0,
        "limite_potavel": 0.9,
        "desc": "Carcinogênico classe 1 (IARC). Irritante severo de mucosas. Usado como conservante, mas tóxico em concentrações elevadas."
    },
    "Perclorato": {
        "tipo": "Químico (Sal Inorgânico)",
        "LD50": 2100.0,
        "limite_potavel": 0.07,
        "desc": "Inibe a captação de iodo pela tireoide, causando hipotireoidismo. Muito persistente em água. Contaminação comum em áreas militares."
    },
    "Nitratos/Nitritos": {
        "tipo": "Químico (Sal Inorgânico)",
        "LD50": 85.0,
        "limite_potavel": 10.0,
        "desc": "Nitritos convertem hemoglobina em metahemoglobina, causando hipóxia. Especialmente perigoso para lactentes (síndrome do bebê azul)."
    },
    "Tetracloroetileno (PCE)": {
        "tipo": "Químico (Solvente Clorado)",
        "LD50": 2600.0,
        "limite_potavel": 0.04,
        "desc": "Solvente de limpeza a seco. Carcinogênico provável. Neurotóxico e hepatotóxico. Muito persistente em aquíferos."
    }
}

# =============================================================================
# MOTOR DE CÁLCULO: DILUIÇÃO E TOXICOLOGIA
# =============================================================================
def calcular_impacto_agua(volume_litros, massa_agente_kg, dados_agente):
    """
    Calcula a concentração final do contaminante após diluição e avalia
    o risco toxicológico comparando com doses letais e limites de potabilidade.
    
    Parâmetros:
        volume_litros: Volume total de água no reservatório (L)
        massa_agente_kg: Massa do contaminante adicionado (kg)
        dados_agente: Dicionário com propriedades toxicológicas do agente
    
    Retorna:
        Dicionário com concentração, dose letal, status de risco e classificação
    """
    # 1. Conversão de Massa (kg -> mg)
    massa_mg = massa_agente_kg * 1_000_000
    
    # 2. Concentração Final (mg/L ou ppm)
    # A concentração é calculada assumindo mistura homogênea instantânea
    concentracao_mg_L = massa_mg / volume_litros if volume_litros > 0 else float('inf')
    
    # 3. Toxicologia Humana (Padrão: Adulto 70kg)
    # LD50 representa a dose que mata 50% dos indivíduos em testes toxicológicos
    peso_medio_adulto = 70.0  # kg (padrão OMS)
    dose_letal_total_mg = dados_agente['LD50'] * peso_medio_adulto
    
    # 4. Análise de Ingestão Típica
    # Um copo padrão contém aproximadamente 250 mL (0.25 L)
    volume_copo_litros = 0.25
    massa_contaminante_copo_mg = concentracao_mg_L * volume_copo_litros
    
    # 5. Cálculo de Copos Necessários para Dose Letal
    # Estima quantos copos seriam necessários para atingir a dose letal
    if massa_contaminante_copo_mg > 0:
        copos_para_morte = dose_letal_total_mg / massa_contaminante_copo_mg
    else:
        copos_para_morte = float('inf')
    
    # 6. Avaliação de Potabilidade
    # Compara a concentração com o limite máximo permitido para água potável
    if dados_agente['limite_potavel'] > 0:
        fator_excesso = concentracao_mg_L / dados_agente['limite_potavel']
    else:
        fator_excesso = float('inf') if concentracao_mg_L > 0 else 0
    
    # 7. Classificação de Risco
    # Baseada em critérios toxicológicos e regulatórios
    if copos_para_morte <= 1.0:
        status = "LETAL IMEDIATO"
        cor = "#e74c3c"  # Vermelho
    elif copos_para_morte <= 10.0:
        status = "PERIGO AGUDO"
        cor = "#f39c12"  # Laranja
    elif fator_excesso > 1:
        status = "IMPRÓPRIA PARA CONSUMO"
        cor = "#f1c40f"  # Amarelo
    else:
        status = "DILUIÇÃO EFICAZ"
        cor = "#2ecc71"  # Verde
        
    return {
        "concentracao": concentracao_mg_L,
        "mg_copo": massa_contaminante_copo_mg,
        "dose_letal_pessoa": dose_letal_total_mg,
        "copos_letais": copos_para_morte,
        "fator_limite": fator_excesso,
        "status": status,
        "cor": cor
    }

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Segurança em Redes de Água")
    st.markdown("**Modelagem de Contaminação Hídrica: Análise de Diluição, Toxicidade e Potabilidade**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de Contaminação Hídrica", expanded=True):
        st.markdown("""
        **Princípio Fundamental:** A toxicidade de uma substância depende da dose ingerida, não apenas da presença do contaminante.
        
        **Cenário de Análise:** Este módulo simula a introdução de um contaminante em um reservatório de água, 
        calculando a concentração resultante após diluição e avaliando os riscos toxicológicos.
        
        **Metodologia de Cálculo:**
        1. **Concentração Final:** Calculada pela divisão da massa do contaminante (kg) pelo volume total de água (L), 
           resultando em mg/L (equivalente a partes por milhão - ppm).
        2. **Dose Letal:** Baseada na LD50 (dose letal para 50% da população em testes toxicológicos), 
           ajustada para um adulto padrão de 70 kg.
        3. **Análise de Ingestão:** Avalia a quantidade de contaminante presente em um copo padrão de 250 mL, 
           comparando com a dose letal estimada.
        4. **Limite de Potabilidade:** Compara a concentração final com os padrões regulatórios (CONAMA, OMS, EPA).
        
        **Importante:** Este modelo assume mistura homogênea instantânea. Em cenários reais, fatores como 
        estratificação, reações químicas, degradação e adsorção podem alterar os resultados.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros do Reservatório")
        
        # Presets de Volume para facilitar
        tipo_reservatorio = st.selectbox(
            "Tipo de Reservatório",
            ["Caixa d'Água Residencial (1.000 L)", 
             "Caminhão Pipa (10.000 L)", 
             "Torre de Condomínio (50.000 L)",
             "Piscina Olímpica (2.500.000 L)",
             "Pequena Represa/ETA (100.000.000 L)",
             "Personalizado"],
            index=2
        )
        
        # Extrair volume do texto ou permitir customizado
        mapa_vol = {
            "Caixa d'Água Residencial (1.000 L)": 1000,
            "Caminhão Pipa (10.000 L)": 10000,
            "Torre de Condomínio (50.000 L)": 50000,
            "Piscina Olímpica (2.500.000 L)": 2500000,
            "Pequena Represa/ETA (100.000.000 L)": 100000000
        }
        
        if tipo_reservatorio == "Personalizado":
            volume = st.number_input("Volume do Reservatório (Litros)", value=50000, min_value=100, step=1000)
        else:
            volume = st.number_input("Volume do Reservatório (Litros)", value=mapa_vol[tipo_reservatorio], min_value=100, step=1000)
        
        st.caption(f"Volume equivalente: {volume/1000:.2f} metros cúbicos ({volume:,.0f} litros)")

    with col2:
        st.subheader("Parâmetros do Contaminante")
        agente = st.selectbox("Substância Contaminante", list(CONTAMINANTES_AGUA.keys()))
        dados_agente = CONTAMINANTES_AGUA[agente]
        
        st.info(f"**{agente}**\n\n**Tipo:** {dados_agente['tipo']}\n\n**Descrição:** {dados_agente['desc']}\n\n**LD50:** {dados_agente['LD50']} mg/kg\n**Limite Potável:** {dados_agente['limite_potavel']} mg/L")
        
        massa = st.number_input("Massa do Contaminante Introduzida (kg)", value=1.0, step=0.1, min_value=0.001, format="%.3f")

    # Botão de Cálculo
    if 'agua_calc' not in st.session_state: 
        st.session_state['agua_calc'] = False
    
    if st.button("Calcular Impacto Toxicológico", type="primary", use_container_width=True):
        st.session_state['agua_calc'] = True

    if st.session_state['agua_calc']:
        res = calcular_impacto_agua(volume, massa, dados_agente)
        
        st.markdown("---")
        st.markdown(f"### Diagnóstico de Risco: <span style='color:{res['cor']}'>{res['status']}</span>", unsafe_allow_html=True)

        # Métricas Principais
        m1, m2, m3 = st.columns(3)
        
        limite_texto = f"Limite: {dados_agente['limite_potavel']} mg/L" if dados_agente['limite_potavel'] > 0 else "Sem limite estabelecido"
        m1.metric("Concentração Final", f"{res['concentracao']:.6f} mg/L", limite_texto, delta_color="inverse")
        m2.metric("Massa por Copo (250 mL)", f"{res['mg_copo']:.4f} mg", "Ingestão típica")
        m3.metric("Dose Letal Estimada (70 kg)", f"{res['dose_letal_pessoa']:.2f} mg", "LD50 para adulto padrão")

        # Análise de Risco por Ingestão
        st.markdown("#### Análise de Risco por Ingestão")
        
        if res['copos_letais'] < 1:
            st.error(f"**RISCO LETAL IMEDIATO:** Um único copo de 250 mL contém {res['mg_copo']:.4f} mg de contaminante, "
                    f"superando a dose letal estimada de {res['dose_letal_pessoa']:.2f} mg para um adulto de 70 kg. "
                    f"Sobrevivência extremamente improvável após ingestão.")
        elif res['copos_letais'] < 5:
            st.warning(f"**PERIGO AGUDO:** A ingestão de {int(res['copos_letais'])+1} copos ({(int(res['copos_letais'])+1)*0.25:.2f} L) "
                     f"poderia resultar em dose letal. Sintomas graves podem ocorrer após o primeiro copo. "
                     f"Evacuação imediata do reservatório é necessária.")
        elif res['fator_limite'] > 1:
            st.warning(f"**ÁGUA IMPRÓPRIA PARA CONSUMO:** A concentração de {res['concentracao']:.6f} mg/L excede o limite "
                     f"regulatório de {dados_agente['limite_potavel']} mg/L em {res['fator_limite']:.1f} vezes. "
                     f"Embora não seja letal imediatamente (seriam necessários aproximadamente {int(res['copos_letais'])} copos para dose letal), "
                     f"o consumo prolongado causaria intoxicação crônica e danos à saúde.")
        else:
            st.success(f"**DILUIÇÃO EFICAZ:** A concentração final de {res['concentracao']:.6f} mg/L está abaixo do limite "
                     f"regulatório de {dados_agente['limite_potavel']} mg/L. O volume de água foi suficiente para diluir "
                     f"o contaminante a níveis seguros. Ainda assim, recomenda-se monitoramento e análise laboratorial.")

        # Calculadora de Remediação
        if res['fator_limite'] > 1:
            with st.expander("Estratégias de Remediação e Diluição", expanded=False):
                if dados_agente['limite_potavel'] > 0:
                    agua_necessaria = (res['concentracao'] / dados_agente['limite_potavel']) * volume - volume
                    if agua_necessaria > 0:
                        st.markdown(f"**Diluição por Adição de Água Limpa:**")
                        st.markdown(f"Para reduzir a concentração até o limite potável ({dados_agente['limite_potavel']} mg/L), "
                                   f"seria necessário adicionar aproximadamente **{agua_necessaria/1000000:.2f} milhões de litros** "
                                   f"de água limpa ao reservatório.")
                        st.markdown("**Observação:** Esta abordagem geralmente é inviável em cenários reais devido ao volume necessário.")
                
                st.markdown("**Estratégias Alternativas de Remediação:**")
                st.markdown("""
                1. **Drenagem e Descontaminação:** Esvaziar o reservatório e realizar limpeza química/mecânica completa.
                2. **Tratamento Químico:** Neutralização ou precipitação do contaminante (depende do tipo químico).
                3. **Filtração Avançada:** 
                   - Osmose reversa (efetiva para a maioria dos contaminantes químicos)
                   - Carvão ativado granular (adsorção de compostos orgânicos)
                   - Ultrafiltração (para contaminantes biológicos e partículas)
                4. **Oxidação Avançada:** Processos como ozonização ou fotocatálise para degradação de contaminantes orgânicos.
                5. **Isolamento Temporário:** Interromper o abastecimento até confirmação de segurança por análise laboratorial.
                """)
                st.markdown("**Importante:** Todas as estratégias devem ser acompanhadas por análise laboratorial para confirmação da eficácia.")

        # Gráfico Comparativo (Escala Logarítmica)
        st.markdown("#### Comparação Visual de Concentrações (Escala Logarítmica)")
        st.caption("A escala logarítmica permite visualizar valores que diferem por várias ordens de grandeza.")
        
        # Calcular concentração letal (se 250 mL contém dose letal, então 1 L contém 4x)
        if res['dose_letal_pessoa'] > 0 and res['copos_letais'] < float('inf'):
            concentracao_letal = res['dose_letal_pessoa'] * 4
        else:
            # Se não há dose letal definida ou é muito alta, usar um múltiplo da concentração atual
            concentracao_letal = res['concentracao'] * 1000
        
        # Preparar dados para o gráfico
        if dados_agente['limite_potavel'] > 0:
            limite_valor = dados_agente['limite_potavel']
        else:
            # Se não há limite, usar uma fração da concentração atual como referência
            limite_valor = res['concentracao'] * 0.01 if res['concentracao'] > 0 else 0.000001
        
        # Garantir valores mínimos para escala logarítmica
        valores_chart = {
            'Limite Potável': max(limite_valor, 0.000001),
            'Concentração Atual': max(res['concentracao'], 0.000001),
            'Concentração Letal (1 L)': max(concentracao_letal, 0.000001)
        }
        
        df_chart = pd.DataFrame({
            'Referência': list(valores_chart.keys()),
            'Valor (mg/L)': list(valores_chart.values()),
            'Cor': ['#2ecc71', res['cor'], '#e74c3c']
        })
        
        # Calcular domínio da escala logarítmica
        valores_numericos = df_chart['Valor (mg/L)'].values
        min_valor = valores_numericos.min() * 0.1
        max_valor = valores_numericos.max() * 10
        
        chart = alt.Chart(df_chart).mark_bar(size=40).encode(
            x=alt.X('Valor (mg/L)', 
                   scale=alt.Scale(type='log', domain=[min_valor, max_valor]),
                   title='Concentração (mg/L) - Escala Logarítmica'),
            y=alt.Y('Referência', 
                   sort=['Concentração Letal (1 L)', 'Concentração Atual', 'Limite Potável'],
                   title=''),
            color=alt.Color('Cor', scale=None, legend=None),
            tooltip=[
                alt.Tooltip('Referência', title='Referência'),
                alt.Tooltip('Valor (mg/L)', format='.6f', title='Concentração (mg/L)')
            ]
        ).properties(
            title="Comparação de Concentrações: Limite Potável vs. Concentração Atual vs. Concentração Letal",
            height=200
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Legenda explicativa
        st.caption("**Interpretação:** A barra verde representa o limite regulatório. A barra colorida mostra a concentração atual. "
                  "A barra vermelha indica a concentração que seria letal em 1 litro de água.")
