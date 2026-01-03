import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import math
import altair as alt

# =============================================================================
# 1. MOTOR DE ROTEAMENTO (ALGORITMO DE BUSCA PONDERADA)
# =============================================================================
# Baseado em: Algoritmos de Roteamento em Grafos (Dijkstra, A*), NetworkX
# O algoritmo encontra o caminho de menor custo considerando:
# - Distância física
# - Zonas de perigo (plumas tóxicas, radiação, etc.)
# - Gargalos logísticos (pontes estreitas, obstruções, trânsito)
# Referências: Dijkstra (1959), Hart et al. (1968) - A* algorithm

def simular_evacuacao(tamanho_grade, ponto_origem, pontos_seguros, zonas_perigo, gargalos):
    """
    Simula evacuação calculando a rota de menor risco usando algoritmo de caminho mais curto.
    
    Cria uma grade de grafos onde cada célula é um nó e as conexões adjacentes são arestas.
    O algoritmo de Dijkstra encontra o caminho de menor custo ponderado, onde o custo
    considera distância, risco de zonas de perigo e gargalos logísticos.
    
    Parâmetros:
    - tamanho_grade: Tamanho da grade (N x N)
    - ponto_origem: Coordenadas (x, y) do ponto de origem
    - pontos_seguros: Lista de coordenadas (x, y) de pontos seguros (destinos)
    - zonas_perigo: Lista de dicionários com {'x', 'y', 'raio', 'intensidade'}
    - gargalos: Lista de coordenadas (x, y) que representam gargalos logísticos
    
    Retorna:
    - melhor_rota: Lista de coordenadas (x, y) representando a rota ótima
    - grafo: Objeto NetworkX Graph com a estrutura da grade
    """
    # Criar grafo de grade 2D (cada célula é um nó, conectado aos 4 vizinhos)
    G = nx.grid_2d_graph(tamanho_grade, tamanho_grade)
    
    # Adicionar pesos às arestas baseados no risco e gargalos
    # O peso representa o "custo" de atravessar uma aresta
    for u, v in G.edges():
        # Custo base é a distância (1 unidade por célula)
        custo = 1.0
        
        # Aumentar custo se o ponto estiver em zona de perigo
        # Quanto mais próximo do centro da zona de perigo, maior o custo
        for zona in zonas_perigo:
            dist_u = math.sqrt((u[0]-zona['x'])**2 + (u[1]-zona['y'])**2)
            if dist_u <= zona['raio']:
                # Penalidade pesada para risco: intensidade × 50
                # Isso faz com que o algoritmo evite zonas de perigo
                custo += zona['intensidade'] * 50
        
        # Aumentar custo se houver gargalo (ex: trânsito, ponte estreita, obstrução)
        # Gargalos reduzem a velocidade de evacuação mas não são letais
        if v in gargalos:
            custo += 10.0  # Penalidade moderada para gargalos
            
        G.add_edge(u, v, weight=custo)

    # Encontrar a rota para o ponto seguro mais próximo usando algoritmo de Dijkstra
    # O algoritmo encontra o caminho de menor custo total (não necessariamente menor distância)
    melhor_rota = []
    menor_custo = float('inf')
    
    for destino in pontos_seguros:
        try:
            # Calcular caminho mais curto usando Dijkstra
            rota = nx.shortest_path(G, source=ponto_origem, target=destino, weight='weight')
            custo_rota = nx.shortest_path_length(G, source=ponto_origem, target=destino, weight='weight')
            
            # Manter a rota com menor custo
            if custo_rota < menor_custo:
                menor_custo = custo_rota
                melhor_rota = rota
        except nx.NetworkXNoPath:
            # Se não houver caminho para este destino, tentar o próximo
            continue
    
    # Se nenhuma rota foi encontrada, retornar rota vazia
    if melhor_rota == []:
        melhor_rota = [ponto_origem]  # Pelo menos manter o ponto de origem
            
    return melhor_rota, G

# =============================================================================
# 2. INTERFACE VISUAL
# =============================================================================

def renderizar():
    st.title("Evacuação Dinâmica e Fluxo Humano")
    st.markdown("**Cálculo de rotas de evacuação otimizadas com desvio de zonas de perigo e gargalos logísticos**")
    st.markdown("---")
    
    with st.expander("Fundamentos do Roteamento de Evacuação", expanded=True):
        st.markdown("""
        #### Algoritmo de Roteamento Ótimo
        
        Este módulo utiliza algoritmos de grafos para calcular rotas de evacuação que minimizam
        o risco e o tempo de fuga, considerando múltiplos fatores:
        
        **1. Algoritmo de Dijkstra:**
        - Encontra o caminho de menor custo em um grafo ponderado
        - Garante a solução ótima quando todos os custos são não-negativos
        - Eficiente para grafos com muitos nós e arestas
        
        **2. Modelo de Custo Ponderado:**
        O custo de atravessar uma célula considera:
        - **Distância Base:** 1 unidade por célula (custo mínimo)
        - **Zonas de Perigo:** Penalidade alta (intensidade × 50) para evitar exposição
        - **Gargalos Logísticos:** Penalidade moderada (+10) para reduzir velocidade mas permitir passagem
        
        **3. Por que o Caminho Mais Longo Pode Ser o Mais Seguro?**
        - O algoritmo prioriza o menor "custo de vida", não a menor distância
        - Um caminho mais longo que evita zonas de perigo pode ter menor custo total
        - Às vezes, o único caminho seguro é o que contorna completamente a zona de perigo
        
        **4. Gargalos Logísticos:**
        - Representam obstruções físicas (pontes estreitas, portas, corredores)
        - Ou congestionamento (trânsito, multidões)
        - Aumentam o tempo de evacuação mas não são letais
        - O algoritmo pode escolher passar por gargalos se for a única rota segura
        
        **5. Limitações do Modelo:**
        - Assume movimento em grade (4 direções: norte, sul, leste, oeste)
        - Não considera terreno irregular ou elevações
        - Assume que todas as pessoas se movem na mesma velocidade
        - Não modela comportamento de pânico ou multidões
        - Não considera mudanças dinâmicas nas zonas de perigo ao longo do tempo
        """)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Configuração do Cenário")
        
        st.markdown("**Localização da População**")
        st.caption("Coordenadas do ponto de origem (onde as pessoas estão)")
        origem_x = st.slider(
            "Posição X da População", 
            0, 19, 2,
            help="Coordenada X na grade (0-19)"
        )
        origem_y = st.slider(
            "Posição Y da População", 
            0, 19, 2,
            help="Coordenada Y na grade (0-19)"
        )
        
        st.markdown("---")
        st.markdown("**Zonas de Perigo (Pluma Tóxica/Radiação)**")
        st.caption("Áreas que devem ser evitadas devido a risco letal")
        perigo_x = st.slider(
            "Centro da Zona de Perigo (X)", 
            0, 19, 10,
            help="Coordenada X do centro da zona de perigo"
        )
        perigo_y = st.slider(
            "Centro da Zona de Perigo (Y)", 
            0, 19, 10,
            help="Coordenada Y do centro da zona de perigo"
        )
        raio_perigo = st.slider(
            "Raio de Perigo", 
            1, 8, 4,
            help="Raio da zona de perigo em células da grade"
        )
        intensidade_perigo = st.slider(
            "Intensidade do Perigo", 
            1, 20, 10,
            help="Intensidade do perigo (afeta o peso da penalidade no algoritmo)"
        )
        
        st.markdown("---")
        st.markdown("**Gargalos Logísticos**")
        st.caption("Obstruções físicas ou congestionamento que reduzem velocidade")
        tem_gargalo = st.checkbox(
            "Ativar Gargalo (Ponte Estreita / Obstrução)", 
            value=True,
            help="Simula uma obstrução física que reduz a velocidade de evacuação"
        )
        
        # Inicializar variáveis do gargalo com valores padrão
        gargalo_x = 10
        gargalo_y = 5
        tamanho_gargalo = 3
        
        if tem_gargalo:
            gargalo_x = st.slider(
                "Posição X do Gargalo", 
                0, 19, 10,
                help="Coordenada X do gargalo"
            )
            gargalo_y = st.slider(
                "Posição Y do Gargalo", 
                0, 19, 5,
                help="Coordenada Y do gargalo"
            )
            tamanho_gargalo = st.slider(
                "Tamanho do Gargalo (células)", 
                1, 5, 3,
                help="Número de células afetadas pelo gargalo"
            )
        
    with col2:
        st.subheader("Mapa Tático de Evacuação")
        
        # Definir pontos seguros (destinos de evacuação)
        # Normalmente seriam saídas, áreas de triagem, ou pontos de encontro
        pontos_seguros = [(19, 19), (19, 0), (0, 19), (0, 0)]
        
        # Definir gargalos baseado na configuração do usuário
        if tem_gargalo:
            gargalos = []
            for i in range(tamanho_gargalo):
                gargalos.append((gargalo_x, gargalo_y + i))
        else:
            gargalos = []
        
        # Definir zonas de perigo
        zonas_perigo = [{
            'x': perigo_x, 
            'y': perigo_y, 
            'raio': raio_perigo, 
            'intensidade': intensidade_perigo
        }]

        # Executar Simulação
        tamanho_grade = 20
        rota, grafo = simular_evacuacao(
            tamanho_grade, 
            (origem_x, origem_y), 
            pontos_seguros, 
            zonas_perigo, 
            gargalos
        )

        # Visualização usando Matriz (Heatmap)
        grade_visual = np.zeros((tamanho_grade, tamanho_grade))
        
        # Marcar Zonas de Perigo
        for x in range(tamanho_grade):
            for y in range(tamanho_grade):
                dist = math.sqrt((x-perigo_x)**2 + (y-perigo_y)**2)
                if dist <= raio_perigo:
                    grade_visual[y, x] = 2  # Área de Perigo
        
        # Marcar Gargalos
        for g in gargalos:
            if 0 <= g[0] < tamanho_grade and 0 <= g[1] < tamanho_grade:
                grade_visual[g[1], g[0]] = 1.5  # Obstrução

        # Marcar Rota
        for p in rota:
            if 0 <= p[0] < tamanho_grade and 0 <= p[1] < tamanho_grade:
                grade_visual[p[1], p[0]] = 1  # Caminho Calculado
            
        # Preparar dados para o gráfico Altair
        data = []
        for y in range(tamanho_grade):
            for x in range(tamanho_grade):
                tipo = "Livre"
                val = grade_visual[y, x]
                if val == 2: 
                    tipo = "Zona de Perigo"
                elif val == 1.5: 
                    tipo = "Gargalo / Obstrução"
                elif val == 1: 
                    tipo = "Rota de Evacuação"
                elif (x, y) in pontos_seguros: 
                    tipo = "Zona Segura"
                elif (x, y) == (origem_x, origem_y): 
                    tipo = "Ponto de Origem"
                
                data.append({'x': x, 'y': y, 'Status': tipo})

        df_mapa = pd.DataFrame(data)

        chart = alt.Chart(df_mapa).mark_rect(stroke='white', strokeWidth=0.5).encode(
            x=alt.X('x:O', title='Coordenada X', axis=alt.Axis(grid=False)),
            y=alt.Y('y:O', sort='descending', title='Coordenada Y', axis=alt.Axis(grid=False)),
            color=alt.Color('Status:N', 
                          scale=alt.Scale(
                              domain=['Livre', 'Zona de Perigo', 'Gargalo / Obstrução', 
                                     'Rota de Evacuação', 'Zona Segura', 'Ponto de Origem'],
                              range=['#f0f0f0', '#ff4b4b', '#ffa500', '#4b91ff', '#28a745', '#000000']
                          ),
                          legend=alt.Legend(title="Legenda")),
            tooltip=['x:O', 'y:O', 'Status:N']
        ).properties(
            width=600, 
            height=600,
            title="Mapa de Evacuação - Rota Ótima Calculada"
        )

        st.altair_chart(chart, use_container_width=True)

    # --- MÉTRICAS DE EVACUAÇÃO ---
    st.markdown("---")
    st.subheader("Métricas de Desempenho da Evacuação")
    
    # Calcular métricas
    distancia_rota = len(rota) - 1 if len(rota) > 1 else 0  # Número de arestas (não nós)
    
    # Tempo estimado: assumindo velocidade de caminhada normal
    # 1.5 minutos por célula (assumindo célula de ~100m e velocidade de 4 km/h)
    tempo_base = distancia_rota * 1.5
    
    # Verificar se a rota passa por zonas de perigo
    rota_passa_perigo = any(
        math.sqrt((p[0]-perigo_x)**2 + (p[1]-perigo_y)**2) <= raio_perigo 
        for p in rota
    )
    
    # Verificar se a rota passa por gargalos
    rota_passa_gargalo = any(p in gargalos for p in rota) if tem_gargalo else False
    
    # Aplicar penalidades de tempo
    tempo_estimado = tempo_base
    if rota_passa_gargalo:
        tempo_estimado *= 2  # Penalidade de tempo por gargalo (velocidade reduzida)
    
    # Calcular custo total da rota
    if len(rota) > 1:
        custo_total = 0
        for i in range(len(rota) - 1):
            u = rota[i]
            v = rota[i + 1]
            if grafo.has_edge(u, v):
                custo_total += grafo[u][v].get('weight', 1.0)
    else:
        custo_total = float('inf')
    
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric(
        "Distância da Rota", 
        f"{distancia_rota} células",
        help="Número de células percorridas na rota (distância em células da grade)"
    )
    
    if tempo_estimado < 60:
        tempo_str = f"{int(tempo_estimado)} min"
    else:
        tempo_str = f"{int(tempo_estimado/60)}h {int(tempo_estimado%60)} min"
    
    m2.metric(
        "Tempo Estimado de Evacuação", 
        tempo_str,
        help="Tempo estimado para completar a evacuação (assumindo velocidade de caminhada normal)"
    )
    
    if rota_passa_perigo:
        status_rota = "ALTO RISCO"
        status_delta = "Rota passa por zona de perigo"
        status_color = "inverse"
    else:
        status_rota = "SEGURA"
        status_delta = "Rota evita zonas de perigo"
        status_color = "normal"
    
    m3.metric(
        "Status da Rota", 
        status_rota,
        delta=status_delta,
        delta_color=status_color,
        help="Indica se a rota passa por zonas de perigo ou não"
    )
    
    m4.metric(
        "Custo Total da Rota",
        f"{custo_total:.1f}" if custo_total != float('inf') else "N/A",
        help="Custo total ponderado da rota (considera distância, perigo e gargalos)"
    )
    
    st.markdown("---")
    
    # Alertas e informações
    if rota_passa_perigo:
        st.error("**ALERTA:** A rota calculada passa por uma zona de perigo. "
                "Considere ajustar os parâmetros ou verificar se há alternativas mais seguras. "
                "Em situações reais, esta rota NÃO deve ser utilizada.")
    elif rota_passa_gargalo:
        st.warning("**ATENÇÃO:** A rota sugerida passa por um gargalo (ponte/obstrução). "
                  "O tempo de evacuação foi dobrado devido à redução de velocidade. "
                  "Esta pode ser a única rota segura disponível.")
    else:
        st.success("**ROTA SEGURA:** A rota calculada evita zonas de perigo e minimiza o tempo de evacuação.")
    
    if len(rota) == 1:
        st.error("**ERRO:** Nenhuma rota foi encontrada. Verifique se há caminho possível entre origem e destinos seguros.")
    
    st.markdown("---")
    st.markdown("### Interpretação dos Resultados")
    st.info("""
    **Algoritmo de Otimização:**
    - O algoritmo de Dijkstra prioriza o menor "custo de vida", não necessariamente a menor distância
    - Às vezes, o caminho mais longo é o único que garante zero exposição à zona de perigo
    - O algoritmo automaticamente balanceia distância, risco e gargalos para encontrar a rota ótima
    
    **Quando a Rota Passa por Gargalos:**
    - Gargalos aumentam o tempo de evacuação mas não são letais
    - Se a rota passa por gargalos, pode ser porque é a única rota segura disponível
    - Em situações reais, considere melhorar ou contornar gargalos se possível
    
    **Quando Nenhuma Rota é Encontrada:**
    - Pode indicar que a origem está completamente cercada por zonas de perigo
    - Verifique se há pontos seguros acessíveis
    - Considere reduzir o raio de perigo ou adicionar mais pontos seguros
    """)
    
    st.markdown("---")
    st.markdown("### Recomendações Operacionais")
    
    if rota_passa_perigo:
        st.error("""
        **AÇÕES IMEDIATAS:**
        1. **NÃO UTILIZE ESTA ROTA:** A rota passa por zona de perigo e não é segura
        2. **Reavaliar Cenário:** Verifique se há alternativas (outros pontos seguros, redução de perigo)
        3. **Aguardar:** Se possível, aguarde até que a zona de perigo se disperse ou se mova
        4. **Proteção:** Se a evacuação for absolutamente necessária, use EPIs apropriados
        5. **Comunicação:** Informe todas as pessoas sobre o risco da rota
        """)
    elif rota_passa_gargalo:
        st.warning("""
        **AÇÕES RECOMENDADAS:**
        1. **Gerenciar Gargalo:** Estabelecer controle de fluxo no gargalo para evitar congestionamento
        2. **Sinalização:** Marcar claramente a rota e o gargalo para orientar as pessoas
        3. **Equipes de Apoio:** Posicionar equipes no gargalo para auxiliar a evacuação
        4. **Tempo Extra:** Considerar o tempo adicional necessário devido ao gargalo
        5. **Alternativas:** Avaliar se há rotas alternativas que contornam o gargalo
        """)
    else:
        st.success("""
        **ROTA APROVADA:**
        1. **Implementar Imediatamente:** A rota é segura e pode ser utilizada
        2. **Sinalização:** Marcar claramente a rota no terreno
        3. **Comunicação:** Informar todas as pessoas sobre a rota de evacuação
        4. **Monitoramento:** Acompanhar a evacuação e ajustar se necessário
        5. **Pontos de Encontro:** Estabelecer pontos de encontro nas zonas seguras
        """)
    
    st.markdown("---")
    st.markdown("### Considerações Técnicas")
    st.info("""
    **Limitações do Modelo:**
    - Assume movimento em grade (4 direções: norte, sul, leste, oeste)
    - Não considera terreno irregular, elevações ou obstáculos naturais
    - Assume que todas as pessoas se movem na mesma velocidade
    - Não modela comportamento de pânico, multidões ou fluxo de massa
    - Não considera mudanças dinâmicas nas zonas de perigo ao longo do tempo
    - Assume que a zona de perigo é estática durante a evacuação
    
    **Interpretação dos Resultados:**
    - Os resultados são projeções baseadas em um modelo simplificado
    - Condições reais podem variar significativamente
    - Use os resultados como guia para planejamento, não como rota definitiva
    - Sempre valide a rota no terreno antes de implementar
    - Considere fatores adicionais (clima, visibilidade, condições físicas das pessoas)
    
    **Melhorias Futuras:**
    - Modelos de fluxo de multidões (Social Force Model)
    - Consideração de terreno e elevações
    - Modelagem dinâmica de zonas de perigo
    - Múltiplas rotas simultâneas para grandes grupos
    - Integração com dados de tráfego em tempo real
    """)