import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import math
import altair as alt

# =============================================================================
# 1. MOTOR DE ROTEAMENTO (ALGORITMO DE BUSCA PONDERADA)
# =============================================================================

def simular_evacuacao(tamanho_grade, ponto_origem, pontos_seguros, zonas_perigo, gargalos):
    """
    Cria uma grade de grafos e calcula a rota de menor risco usando Dijkstra/A*.
    """
    G = nx.grid_2d_graph(tamanho_grade, tamanho_grade)
    
    # Adicionar pesos às arestas baseados no risco e gargalos
    for u, v in G.edges():
        # Custo base é a distância (1 unidade)
        custo = 1.0
        
        # Aumentar custo se o ponto estiver em zona de perigo
        for zona in zonas_perigo:
            dist_u = math.sqrt((u[0]-zona['x'])**2 + (u[1]-zona['y'])**2)
            if dist_u <= zona['raio']:
                custo += zona['intensidade'] * 50 # Penalidade pesada para risco
        
        # Aumentar custo se houver gargalo (ex: trânsito, ponte estreita)
        if v in gargalos:
            custo += 10.0 # Reduz a prioridade da rota
            
        G.add_edge(u, v, weight=custo)

    # Encontrar a rota para o ponto seguro mais próximo
    melhor_rota = []
    menor_custo = float('inf')
    
    for destino in pontos_seguros:
        try:
            rota = nx.shortest_path(G, source=ponto_origem, target=destino, weight='weight')
            custo_rota = nx.shortest_path_length(G, source=ponto_origem, target=destino, weight='weight')
            if custo_rota < menor_custo:
                menor_custo = custo_rota
                melhor_rota = rota
        except nx.NetworkXNoPath:
            continue
            
    return melhor_rota, G

# =============================================================================
# 2. INTERFACE VISUAL
# =============================================================================

def renderizar():
    st.markdown("### 🏃 Evacuação Dinâmica e Fluxo Humano")
    st.markdown("Cálculo de rotas de fuga otimizadas com desvio de plumas e gargalos logísticos.")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📍 Configuração do Cenário")
        
        # Simulação de coordenadas em uma grade 20x20
        origem_x = st.slider("Posição X da População", 0, 19, 2)
        origem_y = st.slider("Posição Y da População", 0, 19, 2)
        
        st.divider()
        st.markdown("**☣️ Zonas de Perigo (Pluma)**")
        perigo_x = st.slider("Centro do Perigo (X)", 0, 19, 10)
        perigo_y = st.slider("Centro do Perigo (Y)", 0, 19, 10)
        raio_perigo = st.slider("Raio de Letalidade", 1, 8, 4)
        
        st.divider()
        st.markdown("**🌉 Gargalos Logísticos**")
        tem_gargalo = st.checkbox("Simular Ponte Estreita / Obstrução", value=True)
        
    with col2:
        st.subheader("🗺️ Mapa Tático de Evacuação")
        
        # Definições fixas para o exemplo
        pontos_seguros = [(19, 19), (19, 0)]
        gargalos = [(10, 5), (10, 6), (10, 7)] if tem_gargalo else []
        zonas_perigo = [{'x': perigo_x, 'y': perigo_y, 'raio': raio_perigo, 'intensidade': 10}]

        # Executar Simulação
        rota, grafo = simular_evacuacao(20, (origem_x, origem_y), pontos_seguros, zonas_perigo, gargalos)

        # Visualização usando Matriz (Heatmap)
        grade_visual = np.zeros((20, 20))
        
        # Marcar Perigo
        for x in range(20):
            for y in range(20):
                dist = math.sqrt((x-perigo_x)**2 + (y-perigo_y)**2)
                if dist <= raio_perigo:
                    grade_visual[y, x] = 2 # Área Quente
        
        # Marcar Gargalos
        for g in gargalos:
            grade_visual[g[1], g[0]] = 1.5 # Obstrução

        # Marcar Rota
        for p in rota:
            grade_visual[p[1], p[0]] = 1 # Caminho Calculado
            
        # Preparar dados para o gráfico Altair
        data = []
        for y in range(20):
            for x in range(20):
                tipo = "Livre"
                val = grade_visual[y, x]
                if val == 2: tipo = "PERIGO (PLUMA)"
                elif val == 1.5: tipo = "GARGALO / TRÂNSITO"
                elif val == 1: tipo = "ROTA DE FUGA"
                elif (x, y) in pontos_seguros: tipo = "ZONA SEGURA"
                elif (x, y) == (origem_x, origem_y): tipo = "VOCÊ ESTÁ AQUI"
                
                data.append({'x': x, 'y': y, 'Status': tipo})

        df_mapa = pd.DataFrame(data)

        chart = alt.Chart(df_mapa).mark_rect().encode(
            x='x:O',
            y=alt.Y('y:O', sort='descending'),
            color=alt.Color('Status:N', scale=alt.Scale(
                domain=['Livre', 'PERIGO (PLUMA)', 'GARGALO / TRÂNSITO', 'ROTA DE FUGA', 'ZONA SEGURA', 'VOCÊ ESTÁ AQUI'],
                range=['#f0f0f0', '#ff4b4b', '#ffa500', '#4b91ff', '#28a745', '#000000']
            )),
            tooltip=['x', 'y', 'Status']
        ).properties(width=500, height=500)

        st.altair_chart(chart, use_container_width=True)

    # --- MÉTRICAS DE EVACUAÇÃO ---
    st.markdown("---")
    st.subheader("📊 Métricas de Desempenho da Fuga")
    
    m1, m2, m3 = st.columns(3)
    
    tempo_estimado = len(rota) * 1.5 # 1.5 min por célula de grade
    if tem_gargalo and any(p in gargalos for p in rota):
        tempo_estimado *= 2 # Penalidade de tempo por gargalo
        
    m1.metric("Distância da Rota", f"{len(rota)} unidades")
    m2.metric("Tempo Est. de Evacuação", f"{int(tempo_estimado)} min")
    m3.metric("Status da Rota", "SEGURA" if not any(math.sqrt((p[0]-perigo_x)**2 + (p[1]-perigo_y)**2) <= raio_perigo for p in rota) else "ALTO RISCO")

    if any(p in gargalos for p in rota):
        st.warning("⚠️ **Atenção:** A rota sugerida passa por um gargalo (ponte/obstrução). O tempo de evacuação foi dobrado.")

    st.info("💡 **Dica de Comando:** O algoritmo A* prioriza o menor 'custo de vida'. Às vezes, o caminho mais longo é o único que garante zero exposição à pluma tóxica.")