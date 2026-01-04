import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. REFERÊNCIAS DE DENSIDADE POPULACIONAL (Pessoas por km²)
# =============================================================================
# Valores baseados em dados demográficos típicos e cenários de emergência
DENSIDADES = {
    "Área Rural / Industrial Isolada": 50,
    "Subúrbio / Residencial Baixo": 2500,
    "Urbano Denso (Centro da Cidade)": 8000,
    "Evento de Massa (Estádio/Show)": 25000,
    "Shopping Center / Centro Comercial": 15000,
    "Aeroporto / Terminal de Transporte": 12000,
    "Campus Universitário": 6000,
    "Parque Industrial": 3000,
    "Zona Portuária": 2000,
    "Área Hospitalar / Complexo Médico": 10000,
    "Personalizado (Inserir Manualmente)": 0
}

# =============================================================================
# 2. MOTOR DE CÁLCULO ESTATÍSTICO (PROTOCOLO START)
# =============================================================================
def calcular_triage(populacao_exposta, gravidade_incidente):
    """
    Distribui a população exposta nas categorias do protocolo START (Simple Triage and Rapid Treatment)
    baseado na gravidade do incidente.
    
    Protocolo START:
    - Vermelho (Imediato): Lesões críticas que requerem tratamento imediato
    - Amarelo (Retardado): Lesões sérias que podem esperar tratamento
    - Verde (Leve): Lesões menores, vítimas ambulatoriais
    - Preto (Expectante/Óbito): Vítimas fatais ou expectante (sem chance de sobrevivência)
    
    Parâmetros:
        populacao_exposta: Número total de pessoas expostas ao incidente
        gravidade_incidente: Severidade do incidente (0.0 a 1.0)
    
    Retorna:
        Dicionário com distribuição de vítimas por categoria
    """
    # Lógica de distribuição estatística baseada em dados históricos de desastres:
    # À medida que a gravidade sobe, a mortalidade (Preto) e casos críticos (Vermelho) aumentam exponencialmente.
    
    # Fator Preto (Óbitos): Curva exponencial acelerada
    # Para gravidade alta, a mortalidade aumenta rapidamente
    f_preto = (gravidade_incidente ** 2.5) * 0.7
    
    # Fator Vermelho (Crítico): Curva exponencial moderada
    # Vítimas que requerem tratamento imediato
    f_vermelho = (gravidade_incidente ** 1.5) * 0.3
    
    # Fator Amarelo (Retardado): Inversamente proporcional à gravidade
    # Vítimas sérias mas estáveis
    f_amarelo = (1 - gravidade_incidente) * 0.4
    
    # Fator Verde (Leve): O restante após subtrair os casos críticos
    # Vítimas com lesões menores, ambulatoriais
    soma_criticos = f_preto + f_vermelho + f_amarelo
    f_verde = max(0, 1.0 - soma_criticos)
    
    vitimas = {
        "Vermelho (Imediato)": int(populacao_exposta * f_vermelho),
        "Amarelo (Retardado)": int(populacao_exposta * f_amarelo),
        "Verde (Leve)": int(populacao_exposta * f_verde),
        "Preto (Expectante/Óbito)": int(populacao_exposta * f_preto)
    }
    
    return vitimas

# =============================================================================
# 3. INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Triagem e Carga de Vítimas")
    st.markdown("**Estimativa de Impacto Populacional e Necessidade de Recursos Médicos usando Protocolo START**")
    st.markdown("---")

    with st.expander("Fundamentos da Estimativa de Vítimas e Protocolo START", expanded=True):
        st.markdown("""
        **O que é o Protocolo START?**
        
        O START (Simple Triage and Rapid Treatment) é um protocolo padronizado de triagem em massa usado 
        em desastres e emergências de grande escala. Ele classifica vítimas em quatro categorias baseadas 
        na gravidade das lesões e na necessidade de tratamento imediato.
        
        **Categorias do Protocolo START:**
        
        1. **Vermelho (Imediato):** Vítimas críticas que requerem tratamento imediato para sobreviver. 
           Geralmente apresentam problemas respiratórios, hemorragia severa ou choque. Prioridade máxima.
        
        2. **Amarelo (Retardado):** Vítimas com lesões sérias mas estáveis, que podem esperar tratamento 
           sem risco imediato de morte. Requerem atenção médica, mas não são críticas.
        
        3. **Verde (Leve):** Vítimas com lesões menores, capazes de caminhar. Podem ser tratadas mais tarde 
           ou se autotratar. Não representam risco imediato à vida.
        
        4. **Preto (Expectante/Óbito):** Vítimas fatais ou em estado expectante (sem chance de sobrevivência 
           mesmo com tratamento). Em recursos limitados, estas vítimas recebem menor prioridade.
        
        **Metodologia de Estimativa:**
        
        Este módulo estima a distribuição de vítimas baseado em:
        
        1. **Área Afetada:** Calcula a área da zona de risco em quilômetros quadrados.
        
        2. **Densidade Populacional:** Multiplica a área pela densidade populacional local para estimar 
           o número total de pessoas expostas ao incidente.
        
        3. **Gravidade do Incidente:** Ajusta a distribuição de vítimas baseado na intensidade do agente 
           (dose de radiação, concentração tóxica, sobrepressão de explosão, etc.). Quanto maior a gravidade, 
           maior a proporção de vítimas críticas e fatais.
        
        4. **Distribuição Estatística:** Aplica curvas estatísticas baseadas em dados históricos de desastres 
           para distribuir vítimas entre as categorias.
        
        **Limitações do Modelo:**
        
        Esta é uma estimativa baseada em modelos estatísticos. A distribuição real de vítimas pode variar 
        significativamente baseado em:
        - Tipo específico de incidente (explosão, vazamento químico, radiação, etc.)
        - Condições meteorológicas
        - Topografia e geometria do local
        - Hora do dia e padrões de ocupação
        - Eficácia de sistemas de alerta e evacuação
        - Resiliência da população (idade, saúde pré-existente)
        
        Sempre valide com observações de campo e ajuste conforme informações reais se tornem disponíveis.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros Populacionais")
        
        tipo_area = st.selectbox("Tipo de Ocupação da Área", list(DENSIDADES.keys()),
                                 help="Selecione o tipo de área afetada para estimar a densidade populacional.")
        
        if tipo_area == "Personalizado (Inserir Manualmente)":
            densidade_ref = st.number_input("Densidade Populacional (Pessoas/km²)", 
                                           value=1000, min_value=1, step=100,
                                           help="Insira manualmente a densidade populacional da área afetada.")
        else:
            densidade_ref = DENSIDADES[tipo_area]
            st.info(f"**Densidade de Referência:** {densidade_ref} pessoas por km²")

        area_afetada_m2 = st.number_input("Área da Zona de Risco (m²)", 
                                         value=50000, min_value=1, step=5000,
                                         help="Área total afetada pelo incidente em metros quadrados.")
        area_km2 = area_afetada_m2 / 1_000_000
        
        total_expostos = int(area_km2 * densidade_ref)
        st.metric("Total de Pessoas Expostas", f"{total_expostos} pessoas", 
                 f"Área: {area_km2:.4f} km²")

    with col2:
        st.subheader("Severidade do Incidente")
        st.markdown("**Intensidade do Agente (Dose/Concentração/Pressão)**")
        
        nivel_perigo = st.slider("Nível de Gravidade do Incidente", 
                               0.0, 1.0, 0.5, 0.05,
                               help="Ajuste baseado na intensidade observada do agente (radiação, concentração tóxica, sobrepressão, etc.). "
                                   "0.0 = Exposição mínima, 1.0 = Exposição máxima (ground zero).")

        # GUIA DIDÁTICO DINÂMICO DA SEVERIDADE
        if nivel_perigo <= 0.2:
            st.success("**Impacto Leve:** Exposição mínima. Sintomas leves (odor perceptível, irritação ocular leve). "
                      "Maioria das vítimas será classificada como 'Verde' (leve).")
        elif nivel_perigo <= 0.5:
            st.warning("**Impacto Moderado:** Exposição moderada. Sintomas significativos (dificuldade respiratória, tontura) "
                      "ou danos estruturais leves (quebra de vidros). Distribuição equilibrada entre categorias.")
        elif nivel_perigo <= 0.8:
            st.error("**Impacto Grave:** Exposição severa. Sintomas graves (perda de consciência, queimaduras químicas severas) "
                    "ou danos estruturais significativos (colapso de paredes). Alta proporção de vítimas críticas.")
        else:
            st.error("**Impacto Catastrófico:** Exposição máxima (ground zero). Alta probabilidade de óbitos imediatos por trauma, "
                    "asfixia ou dose letal. Maioria das vítimas será classificada como 'Preto' (expectante/óbito) ou 'Vermelho' (crítico).")

        st.markdown("---")
        if st.button("Calcular Estimativa de Vítimas", type="primary", use_container_width=True):
            st.session_state['triage_calc'] = True

    if st.session_state.get('triage_calc'):
        resultado = calcular_triage(total_expostos, nivel_perigo)
        
        st.markdown("---")
        st.markdown("### Estimativa de Triagem START")
        
        # Métricas principais
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vermelho (Imediato)", resultado["Vermelho (Imediato)"], 
                 "Crítico - Tratamento imediato", delta_color="inverse")
        c2.metric("Amarelo (Retardado)", resultado["Amarelo (Retardado)"], 
                 "Sério - Pode esperar", delta_color="off")
        c3.metric("Verde (Leve)", resultado["Verde (Leve)"], 
                 "Ambulatorial", delta_color="normal")
        c4.metric("Preto (Expectante/Óbito)", resultado["Preto (Expectante/Óbito)"], 
                 "Fatal/Expectante", delta_color="inverse")

        # Gráfico de Distribuição
        st.markdown("#### Distribuição de Vítimas por Categoria")
        
        df_triage = pd.DataFrame({
            'Categoria': list(resultado.keys()),
            'Quantidade': list(resultado.values()),
            'Cor': ['#e74c3c', '#f39c12', '#2ecc71', '#34495e']
        })

        chart = alt.Chart(df_triage).mark_bar(size=50).encode(
            x=alt.X('Quantidade:Q', title="Número de Vítimas"),
            y=alt.Y('Categoria:N', sort=None, title="Categoria START"),
            color=alt.Color('Cor:N', scale=None, legend=None),
            tooltip=[alt.Tooltip('Categoria', title='Categoria'),
                    alt.Tooltip('Quantidade', title='Número de Vítimas', format=',')]
        ).properties(height=300, title="Distribuição de Vítimas por Categoria START")
        
        st.altair_chart(chart, use_container_width=True)
        
        # Tabela de resultados
        st.markdown("#### Tabela de Resultados")
        df_resultados = pd.DataFrame({
            'Categoria': list(resultado.keys()),
            'Número de Vítimas': list(resultado.values()),
            'Percentual (%)': [f"{(v/total_expostos*100):.1f}" if total_expostos > 0 else "0.0" 
                              for v in resultado.values()]
        })
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)

        # Logística de Resgate
        st.markdown("---")
        st.markdown("### Necessidade de Recursos Médicos")
        
        # Cálculo de recursos baseado em padrões de resposta a desastres
        # USA (Unidade de Suporte Avançado): 1 ambulância para cada 2 vítimas críticas
        usa = math.ceil(resultado["Vermelho (Imediato)"] / 2) if resultado["Vermelho (Imediato)"] > 0 else 0
        
        # USB (Unidade de Suporte Básico): 1 ambulância para cada 5 vítimas sérias
        usb = math.ceil(resultado["Amarelo (Retardado)"] / 5) if resultado["Amarelo (Retardado)"] > 0 else 0
        
        # Vagas de UTI: Cada vítima vermelha requer vaga de UTI
        vagas_uti = resultado["Vermelho (Imediato)"]
        
        # Kits de triagem: Um kit por pessoa exposta (para triagem inicial)
        kits_triage = total_expostos
        
        col_log1, col_log2 = st.columns(2)
        with col_log1:
            st.markdown("**Recursos de Transporte:**")
            st.metric("Ambulâncias UTI (USA)", usa, 
                     help="Unidades de Suporte Avançado necessárias para transporte de vítimas críticas")
            st.metric("Ambulâncias Básicas (USB)", usb,
                     help="Unidades de Suporte Básico necessárias para transporte de vítimas sérias")
        
        with col_log2:
            st.markdown("**Recursos Hospitalares:**")
            st.metric("Vagas de UTI Estimadas", vagas_uti,
                     help="Número de vagas de UTI necessárias para vítimas críticas")
            st.metric("Kits de Triagem/Óbito", kits_triage,
                     help="Kits necessários para triagem inicial e manejo de óbitos")

        # Alertas e recomendações
        st.markdown("---")
        st.markdown("#### Análise de Capacidade e Recomendações")
        
        if resultado["Vermelho (Imediato)"] > 20:
            st.error("**ALERTA DE DESASTRE:** A capacidade hospitalar local provavelmente será excedida. "
                    "Recomenda-se acionar sistema de ajuda mútua e evacuação para hospitais regionais.")
        elif resultado["Vermelho (Imediato)"] > 10:
            st.warning("**ATENÇÃO:** Número significativo de vítimas críticas. Verifique a capacidade local "
                      "e prepare-se para ativação de recursos adicionais se necessário.")
        else:
            st.info("**Situação Controlada:** O número de vítimas críticas está dentro da capacidade típica "
                   "de resposta local. Monitore a situação e ajuste conforme necessário.")
        
        # Recomendações operacionais
        with st.expander("Recomendações Operacionais", expanded=False):
            st.markdown(f"""
            **Cenário Estimado:**
            - **Total de Pessoas Expostas:** {total_expostos}
            - **Área Afetada:** {area_afetada_m2:,.0f} m² ({area_km2:.4f} km²)
            - **Gravidade do Incidente:** {nivel_perigo:.2f} ({(nivel_perigo*100):.0f}%)
            
            **Distribuição de Vítimas:**
            - **Vermelho (Imediato):** {resultado["Vermelho (Imediato)"]} vítimas críticas
            - **Amarelo (Retardado):** {resultado["Amarelo (Retardado)"]} vítimas sérias
            - **Verde (Leve):** {resultado["Verde (Leve)"]} vítimas leves
            - **Preto (Expectante/Óbito):** {resultado["Preto (Expectante/Óbito)"]} vítimas fatais/expectantes
            
            **Ações Recomendadas:**
            
            1. **Ativação de Recursos:**
               - Mobilizar {usa} ambulâncias UTI (USA) para vítimas críticas
               - Mobilizar {usb} ambulâncias básicas (USB) para vítimas sérias
               - Preparar {vagas_uti} vagas de UTI em hospitais receptores
            
            2. **Organização da Cena:**
               - Estabelecer área de triagem (zona segura)
               - Organizar áreas de tratamento por categoria (Vermelho, Amarelo, Verde)
               - Designar área para óbitos (Preto)
            
            3. **Priorização de Transporte:**
               - Prioridade 1: Vítimas Vermelhas (críticas) - transporte imediato
               - Prioridade 2: Vítimas Amarelas (sérias) - transporte após críticas
               - Prioridade 3: Vítimas Verdes (leves) - transporte ou tratamento no local
            
            4. **Coordenação Hospitalar:**
               - Notificar hospitais receptores sobre número estimado de vítimas
               - Distribuir vítimas entre múltiplos hospitais se necessário
               - Ativar sistema de ajuda mútua se capacidade local for excedida
            
            5. **Documentação:**
               - Registrar todas as vítimas triadas
               - Manter controle de vítimas transportadas
               - Documentar óbitos para fins legais e estatísticos
            
            **Importante:** Esta é uma estimativa baseada em modelos estatísticos. A distribuição real pode variar. 
            Ajuste os recursos conforme informações reais se tornem disponíveis através de triagem de campo.
            """)