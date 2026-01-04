import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import math

# =============================================================================
# 1. FUNÇÕES MATEMÁTICAS (TEORIA DAS FILAS M/M/s)
# =============================================================================
# Baseado em: Teoria das Filas (Queueing Theory), Modelo M/M/s de Erlang
# O modelo M/M/s assume:
# - M (Markovian): Chegadas seguem processo de Poisson (exponencial)
# - M (Markovian): Tempos de serviço seguem distribuição exponencial
# - s: Número de servidores (leitos/equipes) em paralelo
# Referências: Gross & Harris (1998), Hillier & Lieberman (2015)

def calcular_probabilidade_espera(s, rho):
    """
    Calcula a probabilidade de um paciente encontrar todos os leitos ocupados.
    
    Baseado na fórmula de Erlang-C (Erlang's C Formula), que é a probabilidade
    de espera em um sistema M/M/s quando todos os servidores estão ocupados.
    
    Parâmetros:
    - s: Número de servidores (leitos/equipes) disponíveis
    - rho: Taxa de ocupação do sistema (taxa_chegada / capacidade_total)
    
    Retorna:
    - Probabilidade de espera (0-1)
    """
    if rho >= 1: 
        return 1.0  # Sistema saturado, probabilidade de espera é 100%
    
    # Fórmula de Erlang-C simplificada
    # P(W > 0) = (rho^s) / (s! * (1 - rho)) / [soma de (rho^n)/n! para n=0 até s-1 + termo acima]
    pw = (rho ** s) / (math.factorial(s) * (1 - rho))
    divisor = sum([(rho ** n) / math.factorial(n) for n in range(s)]) + pw
    return min(pw / divisor, 1.0)

def simular_fila_hospitalar(taxa_chegada, cap_atendimento, num_leitos):
    """
    Simula o comportamento de uma fila hospitalar usando teoria das filas M/M/s.
    
    Parâmetros:
    - taxa_chegada: Taxa de chegada de vítimas (vítimas/hora)
    - cap_atendimento: Capacidade de atendimento por leito/equipe (vítimas/hora)
    - num_leitos: Número de leitos/equipes disponíveis
    
    Retorna:
    - Dicionário com status, ocupação, tempo de espera e probabilidade de espera
    """
    # rho = taxa de ocupação do sistema (utilização)
    # rho = taxa_chegada / capacidade_total
    # rho < 1: sistema estável
    # rho >= 1: sistema instável (colapso)
    capacidade_total = num_leitos * cap_atendimento
    rho = taxa_chegada / capacidade_total if capacidade_total > 0 else float('inf')
    
    if rho >= 1:
        return {
            "status": "COLAPSO TOTAL",
            "ocupacao": rho,
            "espera_min": float('inf'),
            "prob_espera": 100.0,
            "capacidade_total": capacidade_total,
            "deficit": taxa_chegada - capacidade_total
        }
    
    # Calcular probabilidade de espera usando Erlang-C
    pw = calcular_probabilidade_espera(num_leitos, rho)
    
    # Tempo médio de espera na fila (Wq) em horas
    # Fórmula: Wq = P(W>0) / (s*mu - lambda)
    # Onde: s = num_leitos, mu = cap_atendimento, lambda = taxa_chegada
    if (capacidade_total - taxa_chegada) > 0:
        espera_horas = pw / (capacidade_total - taxa_chegada)
    else:
        espera_horas = float('inf')
    
    # Determinar status baseado na ocupação
    if rho < 0.7:
        status = "OPERACIONAL"
    elif rho < 0.85:
        status = "ATENÇÃO"
    elif rho < 0.95:
        status = "SATURAÇÃO IMINENTE"
    else:
        status = "CRÍTICO"
    
    return {
        "status": status,
        "ocupacao": rho,
        "espera_min": espera_horas * 60,  # Converter para minutos
        "prob_espera": pw * 100,  # Converter para percentual
        "capacidade_total": capacidade_total,
        "deficit": 0
    }

# =============================================================================
# 2. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.title("Gestão de Colapso Hospitalar")
    st.markdown("**Simulação de fluxo de vítimas e análise de saturação da infraestrutura de saúde**")
    st.markdown("---")

    with st.expander("Fundamentos da Teoria das Filas em Sistemas de Saúde", expanded=True):
        st.markdown("""
        #### Modelo M/M/s (Teoria das Filas)
        
        O modelo M/M/s é amplamente utilizado para analisar sistemas de atendimento em saúde, 
        especialmente em situações de emergência e desastres. O modelo assume:
        
        **Características do Modelo:**
        - **M (Markovian - Chegadas):** As chegadas seguem um processo de Poisson, 
          onde os intervalos entre chegadas são exponenciais
        - **M (Markovian - Serviço):** Os tempos de atendimento seguem distribuição exponencial
        - **s (Servidores):** Número de servidores (leitos/equipes) operando em paralelo
        
        **Parâmetros do Modelo:**
        - **λ (Lambda) - Taxa de Chegada:** Número de vítimas que chegam ao sistema por hora
        - **μ (Mu) - Taxa de Serviço:** Número de vítimas que cada leito/equipe atende por hora
        - **s - Número de Servidores:** Número de leitos/equipes disponíveis
        - **ρ (Rho) - Taxa de Ocupação:** ρ = λ / (s × μ)
        
        #### Quando Ocorre o Colapso?
        
        O colapso do sistema ocorre quando:
        - **ρ ≥ 1:** A taxa de chegada supera ou iguala a capacidade total de processamento
        - A fila cresce indefinidamente (teoricamente até infinito)
        - O tempo de espera torna-se indeterminado
        - O sistema não consegue processar todas as chegadas
        
        #### Indicadores de Performance
        
        **Taxa de Ocupação (ρ):**
        - ρ < 0.7: Sistema operacional com margem de segurança
        - 0.7 ≤ ρ < 0.85: Sistema em atenção, monitorar de perto
        - 0.85 ≤ ρ < 0.95: Saturação iminente, preparar medidas de contingência
        - ρ ≥ 0.95: Sistema crítico, risco de colapso
        - ρ ≥ 1.0: Colapso total, sistema não consegue processar todas as chegadas
        
        **Probabilidade de Espera:**
        - Probabilidade de um paciente encontrar todos os leitos ocupados ao chegar
        - Calculada usando a fórmula de Erlang-C
        - Quanto maior, maior a necessidade de recursos adicionais
        
        **Tempo Médio de Espera:**
        - Tempo médio que um paciente aguarda antes de ser atendido
        - Aumenta exponencialmente quando ρ se aproxima de 1
        """)

    st.subheader("Parâmetros do Sistema")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Entrada de Vítimas**")
        taxa_vimas = st.number_input(
            "Taxa de Chegada (vítimas/hora)", 
            min_value=1, 
            value=20, 
            step=1,
            help="Número de vítimas que chegam ao sistema por hora. Este dado pode vir do módulo de Triagem ou de estimativas de campo."
        )
        tempo_atendimento = st.slider(
            "Tempo Médio de Atendimento (minutos)", 
            10, 
            180, 
            30,
            step=5,
            help="Tempo médio necessário para atender uma vítima (inclui triagem, tratamento, estabilização)."
        )
        # Converte tempo em capacidade por hora (mu)
        # Se tempo_atendimento = 30 min, então cap_mu = 60/30 = 2 vítimas/hora
        cap_mu = 60 / tempo_atendimento if tempo_atendimento > 0 else 0
        st.caption(f"**Capacidade por leito/equipe:** {cap_mu:.2f} vítimas/hora")

    with col2:
        st.markdown("**Capacidade do Hospital**")
        leitos_disponiveis = st.number_input(
            "Número de Leitos/Equipes Disponíveis", 
            min_value=1, 
            value=10,
            step=1,
            help="Número total de leitos ou equipes de atendimento disponíveis simultaneamente."
        )
        reserva_emergencia = st.checkbox(
            "Ativar Reserva de Contingência (+20%)",
            help="Considera uma reserva adicional de 20% da capacidade para situações de emergência. "
                 "Esta reserva pode ser ativada cancelando procedimentos eletivos e mobilizando equipes extras."
        )
        
        if reserva_emergencia:
            leitos_efetivos = int(leitos_disponiveis * 1.2)
            st.info(f"**Capacidade com reserva:** {leitos_efetivos} leitos/equipes")
        else:
            leitos_efetivos = leitos_disponiveis
        
        # Mostrar capacidade total
        capacidade_total = leitos_efetivos * cap_mu
        st.metric("Capacidade Total do Sistema", f"{capacidade_total:.1f} vítimas/hora",
                 help="Capacidade máxima de processamento do sistema (leitos × capacidade por leito)")

    st.markdown("---")
    
    # --- PROCESSAMENTO ---
    resultado = simular_fila_hospitalar(taxa_vimas, cap_mu, leitos_efetivos)

    # --- DASHBOARD DE RESULTADOS ---
    st.subheader("Análise do Sistema")
    
    col_status1, col_status2 = st.columns([1, 3])
    with col_status1:
        st.markdown(f"### {resultado['status']}")
    with col_status2:
        if resultado['ocupacao'] >= 1.0:
            st.error("**COLAPSO TOTAL:** O sistema não consegue processar todas as chegadas. A fila crescerá indefinidamente.")
        elif resultado['ocupacao'] >= 0.95:
            st.error("**SISTEMA CRÍTICO:** O sistema está extremamente sobrecarregado. Colapso iminente.")
        elif resultado['ocupacao'] >= 0.85:
            st.warning("**SATURAÇÃO IMINENTE:** O sistema está próximo do limite. Pequenas oscilações causarão filas longas.")
        elif resultado['ocupacao'] >= 0.7:
            st.info("**ATENÇÃO:** O sistema está operando em níveis elevados. Monitorar de perto.")
        else:
            st.success("**OPERACIONAL:** O sistema está operando dentro da capacidade com margem de segurança.")
    
    st.markdown("---")
    
    # Métricas principais
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric(
        "Taxa de Ocupação (ρ)", 
        f"{resultado['ocupacao']*100:.1f}%",
        help="Razão entre taxa de chegada e capacidade total. ρ ≥ 1 indica colapso."
    )
    
    if resultado['espera_min'] != float('inf'):
        espera = f"{resultado['espera_min']:.1f} min"
        if resultado['espera_min'] > 60:
            espera += f" ({resultado['espera_min']/60:.1f} horas)"
    else:
        espera = "Indeterminado"
    
    m2.metric(
        "Tempo Médio de Espera", 
        espera,
        help="Tempo médio que uma vítima aguarda antes de ser atendida."
    )
    
    m3.metric(
        "Probabilidade de Espera", 
        f"{resultado['prob_espera']:.1f}%",
        help="Probabilidade de um paciente encontrar todos os leitos ocupados ao chegar."
    )
    
    if resultado['deficit'] > 0:
        m4.metric(
            "Déficit de Capacidade",
            f"{resultado['deficit']:.1f} vítimas/hora",
            help="Diferença entre taxa de chegada e capacidade total. Indica quantas vítimas/hora não podem ser atendidas."
        )
    else:
        m4.metric(
            "Margem de Segurança",
            f"{resultado['capacidade_total'] - taxa_vimas:.1f} vítimas/hora",
            help="Capacidade adicional disponível antes do colapso."
        )

    # --- GRÁFICO DE PROJEÇÃO ---
    st.markdown("---")
    st.markdown("#### Projeção de Acúmulo de Fila (Próximas 12 Horas)")
    
    horas = np.arange(0, 13, 1)
    
    # Simulação de acúmulo de fila ao longo do tempo
    # Se taxa_chegada > capacidade_total, a fila cresce linearmente
    # Se taxa_chegada <= capacidade_total, a fila se estabiliza ou diminui
    capacidade_total = resultado['capacidade_total']
    deficit = taxa_vimas - capacidade_total
    
    pacientes_aguardando = []
    for h in horas:
        if deficit > 0:
            # Sistema em colapso: fila cresce linearmente
            acumulo = deficit * h
        else:
            # Sistema estável: fila se estabiliza (usando modelo de fila M/M/s)
            # Aproximação: fila se estabiliza em um valor baseado na probabilidade de espera
            if resultado['prob_espera'] > 0:
                # Fila média em regime estacionário
                fila_media = (resultado['prob_espera'] / 100) * (taxa_vimas / (capacidade_total - taxa_vimas)) if (capacidade_total - taxa_vimas) > 0 else 0
                # Simulação de convergência exponencial
                acumulo = fila_media * (1 - np.exp(-h / 2))  # Converge em ~6 horas
            else:
                acumulo = 0
        pacientes_aguardando.append(max(0, acumulo))
    
    df_projecao = pd.DataFrame({
        'Horas após o Início': horas,
        'Pacientes Aguardando': pacientes_aguardando,
        'Capacidade Total': [capacidade_total * h for h in horas],
        'Chegadas Acumuladas': [taxa_vimas * h for h in horas]
    })
    
    # Gráfico com múltiplas linhas
    base = alt.Chart(df_projecao).transform_fold(
        ['Pacientes Aguardando', 'Chegadas Acumuladas', 'Capacidade Total'],
        as_=['Tipo', 'Valor']
    )
    
    chart = base.mark_line(point=True).encode(
        x=alt.X('Horas após o Início:Q', title='Horas após o Início do Incidente'),
        y=alt.Y('Valor:Q', title='Número de Pacientes'),
        color=alt.Color('Tipo:N', 
                       scale=alt.Scale(domain=['Pacientes Aguardando', 'Chegadas Acumuladas', 'Capacidade Total'],
                                      range=['red', 'blue', 'green'])),
        strokeDash=alt.condition(
            alt.datum.Tipo == 'Capacidade Total',
            alt.value([5, 5]),
            alt.value([0])
        ),
        tooltip=['Horas após o Início:Q', 'Tipo:N', 'Valor:Q']
    ).properties(
        height=400,
        title="Evolução Temporal do Sistema"
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    st.caption("**Interpretação:** A linha vermelha mostra o acúmulo de pacientes aguardando. "
              "A linha azul mostra as chegadas acumuladas. A linha verde tracejada mostra a capacidade total de processamento. "
              "Quando a linha vermelha cresce indefinidamente, o sistema está em colapso.")

    # --- RECOMENDAÇÕES OPERACIONAIS ---
    st.markdown("---")
    st.markdown("### Recomendações Operacionais")
    
    if resultado['ocupacao'] >= 1.0:
        st.error("**ALERTA CRÍTICO DE COLAPSO:** A taxa de chegada excede a capacidade de processamento.")
        st.markdown("""
        **AÇÕES IMEDIATAS:**
        1. **Ativar Protocolo de Transbordo Regional:** Estabelecer rotas de evacuação para hospitais da região
        2. **Converter Espaços:** Transformar áreas de triagem, corredores e salas de espera em leitos de observação
        3. **Reavaliar Critérios de Triagem:** Implementar Protocolo de Catástrofe (modificação do START)
        4. **Mobilizar Recursos:** Ativar todas as equipes de plantão e chamar equipes de folga
        5. **Cancelar Procedimentos Eletivos:** Liberar todos os recursos possíveis para emergências
        6. **Estabelecer Hospitais de Campanha:** Preparar estruturas temporárias se disponíveis
        7. **Coordenação Regional:** Ativar centro de coordenação para distribuição de vítimas
        8. **Comunicação:** Informar autoridades e população sobre a situação crítica
        """)
    elif resultado['ocupacao'] >= 0.95:
        st.error("**SISTEMA CRÍTICO:** O sistema está extremamente sobrecarregado. Colapso iminente.")
        st.markdown("""
        **AÇÕES URGENTES:**
        1. **Preparar Transbordo:** Estabelecer contatos com hospitais da região para evacuação
        2. **Ativar Reservas:** Mobilizar todas as equipes de reserva e plantonistas
        3. **Otimizar Fluxo:** Reduzir tempo de permanência através de alta precoce quando seguro
        4. **Cancelar Eletivos:** Suspender cirurgias e procedimentos não urgentes
        5. **Expandir Capacidade:** Converter espaços não utilizados em áreas de atendimento
        6. **Monitoramento Contínuo:** Acompanhar a situação em tempo real
        """)
    elif resultado['ocupacao'] >= 0.85:
        st.warning("**RISCO DE SATURAÇÃO:** O sistema está operando próximo ao limite.")
        st.markdown("""
        **AÇÕES PREVENTIVAS:**
        1. **Preparar Equipes Extras:** Ter equipes de plantão prontas para ativação rápida
        2. **Otimizar Processos:** Reduzir tempos de atendimento através de protocolos simplificados
        3. **Considerar Cancelamento de Eletivos:** Avaliar suspensão de procedimentos não urgentes
        4. **Estabelecer Contatos:** Preparar lista de hospitais para possível transbordo
        5. **Monitorar de Perto:** Acompanhar indicadores de ocupação a cada hora
        6. **Comunicação Interna:** Informar equipes sobre a situação e preparação necessária
        """)
    elif resultado['ocupacao'] >= 0.7:
        st.info("**ATENÇÃO:** O sistema está operando em níveis elevados.")
        st.markdown("""
        **AÇÕES DE MONITORAMENTO:**
        1. **Monitorar Indicadores:** Acompanhar taxa de ocupação e tempos de espera
        2. **Preparar Contingências:** Ter planos prontos para ativação se necessário
        3. **Otimizar Recursos:** Garantir que todos os recursos estejam sendo utilizados eficientemente
        4. **Comunicação:** Manter equipes informadas sobre a situação
        """)
    else:
        st.success("**SISTEMA RESILIENTE:** A infraestrutura atual suporta o fluxo de vítimas com margem de segurança.")
        st.markdown("""
        **SITUAÇÃO ESTÁVEL:**
        - O sistema está operando dentro da capacidade
        - Há margem de segurança para absorver picos temporários
        - Continue monitorando a situação para detectar mudanças
        """)
    
    # Recomendações adicionais baseadas em tempo de espera
    if resultado['espera_min'] != float('inf') and resultado['espera_min'] > 120:
        st.warning("**TEMPO DE ESPERA ELEVADO:** O tempo médio de espera é superior a 2 horas. "
                  "Considere medidas adicionais para reduzir a fila, como aumento de capacidade ou transbordo.")
    
    if resultado['prob_espera'] > 50:
        st.warning("**ALTA PROBABILIDADE DE ESPERA:** Mais de 50% dos pacientes encontrarão todos os leitos ocupados. "
                  "Isso indica necessidade urgente de aumentar a capacidade do sistema.")
    
    st.markdown("---")
    st.markdown("### Considerações Técnicas")
    st.info("""
    **Limitações do Modelo:**
    - O modelo M/M/s assume chegadas e atendimentos exponenciais, o que é uma simplificação
    - Não considera variações sazonais ou picos súbitos de chegadas
    - Assume que todos os leitos têm a mesma capacidade de atendimento
    - Não modela diferentes tipos de vítimas (leves, moderadas, graves) com tempos de atendimento distintos
    - Não considera tempo de preparação de leitos entre atendimentos
    
    **Interpretação dos Resultados:**
    - Os resultados são projeções baseadas em parâmetros médios
    - Condições reais podem variar significativamente
    - Use os resultados como guia para planejamento, não como previsão exata
    - Combine com dados reais de campo para validação
    - Considere modelos mais complexos (M/G/s, redes de filas) para análises detalhadas
    
    **Referências:**
    - Gross, D., & Harris, C. M. (1998). Fundamentals of Queueing Theory
    - Hillier, F. S., & Lieberman, G. J. (2015). Introduction to Operations Research
    - WHO Guidelines for Mass Casualty Management
    """)

