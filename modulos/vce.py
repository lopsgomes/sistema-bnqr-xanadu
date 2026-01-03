import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import numpy as np
import pandas as pd

# =============================================================================
# BANCO DE DADOS: SUBSTÂNCIAS VOLÁTEIS PARA VCE
# =============================================================================
# VCE (Vapor Cloud Explosion) ocorre quando uma nuvem de vapor inflamável
# encontra uma fonte de ignição e explode, gerando sobrepressão.
# Propriedades necessárias: LFL, UFL, Hc (calor de combustão), densidade
SUBSTANCIAS_VCE = {
    "Gás Natural (Metano)": {
        "tipo": "Gás Combustível",
        "LFL": 5.0,  # % volume
        "UFL": 15.0,  # % volume
        "Hc": 50.0,  # MJ/kg
        "densidade_ar": 0.55,  # mais leve que ar
        "reatividade": "Média",
        "desc": "Principal componente do gás encanado. Mais leve que o ar, dissipa rapidamente em ambientes abertos."
    },
    "GLP (Propano/Butano)": {
        "tipo": "Gás Liquefeito",
        "LFL": 2.1,
        "UFL": 9.5,
        "Hc": 46.0,
        "densidade_ar": 1.55,  # mais pesado que ar
        "reatividade": "Média",
        "desc": "Gás de cozinha (P-13, P-45). Mais pesado que o ar, acumula em baixadas e porões."
    },
    "Hidrogênio (H2)": {
        "tipo": "Gás Combustível",
        "LFL": 4.0,
        "UFL": 75.0,
        "Hc": 120.0,
        "densidade_ar": 0.07,  # muito mais leve
        "reatividade": "Alta",
        "desc": "Alto poder calorífico. Amplo intervalo de inflamabilidade. Chama quase invisível."
    },
    "Acetileno": {
        "tipo": "Gás Instável",
        "LFL": 2.5,
        "UFL": 100.0,
        "Hc": 48.0,
        "densidade_ar": 0.90,
        "reatividade": "Alta",
        "desc": "Usado em solda. Pode detonar sem oxigênio externo. Extremamente instável sob pressão."
    },
    "Etileno": {
        "tipo": "Gás Combustível",
        "LFL": 2.7,
        "UFL": 36.0,
        "Hc": 47.0,
        "densidade_ar": 0.97,
        "reatividade": "Alta",
        "desc": "Usado em indústria petroquímica. Amplo intervalo de inflamabilidade."
    },
    "Acetona": {
        "tipo": "Vapor Orgânico",
        "LFL": 2.5,
        "UFL": 12.8,
        "Hc": 29.0,
        "densidade_ar": 2.0,
        "reatividade": "Média",
        "desc": "Solvente comum. Vapor mais pesado que o ar, acumula próximo ao solo."
    },
    "Gasolina (Vapor)": {
        "tipo": "Vapor de Combustível",
        "LFL": 1.4,
        "UFL": 7.6,
        "Hc": 44.0,
        "densidade_ar": 3.0,
        "reatividade": "Alta",
        "desc": "Vapor de gasolina de tanques ou derramamentos. Muito volátil e inflamável."
    },
    "Etanol (Vapor)": {
        "tipo": "Vapor Orgânico",
        "LFL": 3.3,
        "UFL": 19.0,
        "Hc": 26.8,
        "densidade_ar": 1.59,
        "reatividade": "Média",
        "desc": "Vapor de álcool etílico. Usado como combustível e solvente."
    },
    "Benzeno": {
        "tipo": "Vapor Aromático",
        "LFL": 1.2,
        "UFL": 7.8,
        "Hc": 40.0,
        "densidade_ar": 2.7,
        "reatividade": "Média",
        "desc": "Hidrocarboneto aromático. Carcinogênico. Vapor pesado, acumula em baixadas."
    },
    "Tolueno": {
        "tipo": "Vapor Aromático",
        "LFL": 1.2,
        "UFL": 7.0,
        "Hc": 40.5,
        "densidade_ar": 3.1,
        "reatividade": "Média",
        "desc": "Solvente aromático comum. Vapor mais pesado que o ar."
    },
    "Xileno": {
        "tipo": "Vapor Aromático",
        "LFL": 1.0,
        "UFL": 7.0,
        "Hc": 40.8,
        "densidade_ar": 3.7,
        "reatividade": "Média",
        "desc": "Isômeros de xileno. Solventes industriais. Vapor muito pesado."
    },
    "Metanol": {
        "tipo": "Vapor Orgânico",
        "LFL": 6.0,
        "UFL": 36.5,
        "Hc": 19.9,
        "densidade_ar": 1.11,
        "reatividade": "Média",
        "desc": "Álcool metílico. Combustível alternativo. Tóxico por ingestão."
    },
    "Éter Dietílico": {
        "tipo": "Vapor Orgânico",
        "LFL": 1.9,
        "UFL": 36.0,
        "Hc": 33.9,
        "densidade_ar": 2.55,
        "reatividade": "Alta",
        "desc": "Solvente altamente volátil. Amplo intervalo de inflamabilidade. Forma peróxidos perigosos."
    },
    "Acetaldeído": {
        "tipo": "Vapor Orgânico",
        "LFL": 4.0,
        "UFL": 57.0,
        "Hc": 24.0,
        "densidade_ar": 1.52,
        "reatividade": "Alta",
        "desc": "Aldeído volátil. Amplo intervalo de inflamabilidade. Usado em síntese química."
    },
    "Hexano": {
        "tipo": "Vapor de Hidrocarboneto",
        "LFL": 1.2,
        "UFL": 7.5,
        "Hc": 44.7,
        "densidade_ar": 2.97,
        "reatividade": "Média",
        "desc": "Hidrocarboneto alifático. Solvente comum. Vapor pesado."
    },
    "Heptano": {
        "tipo": "Vapor de Hidrocarboneto",
        "LFL": 1.1,
        "UFL": 6.7,
        "Hc": 44.6,
        "densidade_ar": 3.46,
        "reatividade": "Média",
        "desc": "Componente de gasolina. Vapor muito pesado, acumula próximo ao solo."
    },
    "Octano": {
        "tipo": "Vapor de Hidrocarboneto",
        "LFL": 1.0,
        "UFL": 6.0,
        "Hc": 44.4,
        "densidade_ar": 3.94,
        "reatividade": "Média",
        "desc": "Componente de gasolina. Vapor extremamente pesado."
    },
    "Metil Etil Cetona (MEK)": {
        "tipo": "Vapor de Cetona",
        "LFL": 1.8,
        "UFL": 10.0,
        "Hc": 31.0,
        "densidade_ar": 2.48,
        "reatividade": "Média",
        "desc": "Solvente cetônico industrial. Vapor pesado."
    },
    "Cloreto de Metileno": {
        "tipo": "Vapor Clorado",
        "LFL": 12.0,
        "UFL": 19.0,
        "Hc": 8.5,
        "densidade_ar": 2.93,
        "reatividade": "Baixa",
        "desc": "Solvente clorado. Menor poder calorífico, mas ainda inflamável."
    },
    "Amoníaco (NH3)": {
        "tipo": "Gás Tóxico/Combustível",
        "LFL": 15.0,
        "UFL": 28.0,
        "Hc": 18.6,
        "densidade_ar": 0.59,
        "reatividade": "Média",
        "desc": "Gás tóxico e corrosivo. Pode queimar em altas concentrações. Mais leve que o ar."
    },
    "Monóxido de Carbono (CO)": {
        "tipo": "Gás Tóxico/Combustível",
        "LFL": 12.5,
        "UFL": 74.0,
        "Hc": 10.1,
        "densidade_ar": 0.97,
        "reatividade": "Média",
        "desc": "Gás tóxico incolor e inodoro. Pode queimar formando CO2. Principalmente risco tóxico."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "tipo": "Gás Tóxico/Combustível",
        "LFL": 4.0,
        "UFL": 44.0,
        "Hc": 16.5,
        "densidade_ar": 1.19,
        "reatividade": "Média",
        "desc": "Gás tóxico com odor característico. Pode queimar. Mais pesado que o ar."
    }
}

# Limites de Sobrepressão (Overpressure) - PSI e BAR
# Fonte: CCPS Guidelines, TNO Yellow Book, EPA
LIMITES_BLAST = {
    "Destruição Total / Ruptura Pulmão (10 psi)": {
        "psi": 10.0,
        "bar": 0.69,
        "cor": "#000000",
        "desc": "Demolição de prédios de concreto. Morte provável por trauma e hemorragia pulmonar."
    },
    "Danos Graves / Ruptura Tímpano (5 psi)": {
        "psi": 5.0,
        "bar": 0.34,
        "cor": "#e74c3c",
        "desc": "Paredes de alvenaria caem. Tímpanos estouram. Árvores arrancadas. Lesões graves."
    },
    "Danos Médios / Derruba Pessoas (2 psi)": {
        "psi": 2.0,
        "bar": 0.14,
        "cor": "#f39c12",
        "desc": "Estruturas metálicas entortam. Pessoas são arremessadas. Destelhamento generalizado."
    },
    "Quebra de Vidros / Janelas (0.5 psi)": {
        "psi": 0.5,
        "bar": 0.03,
        "cor": "#f1c40f",
        "desc": "Janelas quebram e voam como estilhaços. 80% dos feridos em explosões urbanas estão nesta zona."
    }
}

# =============================================================================
# MOTOR DE CÁLCULO: VCE (TNO YELLOW BOOK / CCPS)
# =============================================================================
def calcular_vce(massa_kg, gas_props, grau_confinamento):
    """
    Calcula os raios de sobrepressão baseado na massa da nuvem e no confinamento.
    Método: Equivalência TNT Ajustada por Eficiência (Yield Factor).
    
    Parâmetros:
        massa_kg: Massa total da nuvem de vapor (kg)
        gas_props: Dicionário com propriedades do gás (Hc, reatividade)
        grau_confinamento: String indicando o nível de confinamento
    
    Retorna:
        Dicionário com raios de dano para cada nível de sobrepressão
    """
    # 1. Definir Fator de Eficiência (Yield) baseado no cenário
    # Quanto mais obstáculos (tubos, paredes), maior a turbulência e a explosão.
    # Em campo aberto, a eficiência é quase zero (só fogo, sem blast).
    
    tabela_eficiencia = {
        "Campo Aberto (Sem Obstáculos)": 0.03,      # 3% (Quase só Flash Fire)
        "Urbano / Floresta (Obstáculos Médios)": 0.10, # 10% (Padrão industrial leve)
        "Refinaria / Processo (Muitos Tubos)": 0.20,   # 20% (Alta turbulência)
        "Confinado (Túnel / Bunker)": 0.40          # 40% (Devastador)
    }
    
    eficiencia = tabela_eficiencia[grau_confinamento]
    
    # Ajuste por reatividade química (Gases instáveis explodem melhor)
    if gas_props['reatividade'] == "Alta":
        eficiencia *= 1.3
    elif gas_props['reatividade'] == "Baixa":
        eficiencia *= 0.8
        
    # Trava de física (máximo teórico ~50% para nuvens de vapor)
    eficiencia = min(eficiencia, 0.5)

    # 2. Calcular Energia Equivalente em TNT
    # Energia = Massa * Hc * Eficiencia
    # 1 kg TNT = 4680 kJ
    energia_explosiva_kj = massa_kg * gas_props['Hc'] * eficiencia
    kg_tnt = energia_explosiva_kj / 4680.0
    
    # 3. Calcular Raios usando Lei de Escala de Hopkinson-Cranz
    # Z = R / W^(1/3)  -->  R = Z * W^(1/3)
    # Z é o "Scaled Distance" para cada sobrepressão.
    # Valores aproximados de Z para TNT (em m/kg^1/3):
    # 10 psi (0.69 bar) -> Z ~ 2.8
    # 5 psi (0.34 bar)  -> Z ~ 4.3
    # 2 psi (0.14 bar)  -> Z ~ 7.5
    # 0.5 psi (0.03 bar)-> Z ~ 22.0
    
    mapa_z = {
        10.0: 2.8,
        5.0: 4.3,
        2.0: 7.5,
        0.5: 22.0
    }
    
    raios = {}
    for nome, dados in LIMITES_BLAST.items():
        psi = dados['psi']
        z = mapa_z[psi]
        raiz_cubica_w = math.pow(kg_tnt, 1/3) if kg_tnt > 0 else 0
        raio_m = z * raiz_cubica_w
        raios[nome] = raio_m
    
    return raios, kg_tnt, eficiencia

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def renderizar():
    st.title("Ondas de Choque e VCE")
    st.markdown("**Modelagem de Explosão de Nuvem de Vapor: Análise de Sobrepressão e Zonas de Dano**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de VCE (Vapor Cloud Explosion)", expanded=True):
        st.markdown("""
        **O que é uma VCE?**
        
        Uma Explosão de Nuvem de Vapor (VCE) ocorre quando uma nuvem de gás ou vapor inflamável encontra uma 
        fonte de ignição e explode, gerando uma onda de choque de sobrepressão atmosférica. Diferente de um 
        incêndio comum, a VCE produz efeitos destrutivos mesmo a distâncias significativas.
        
        **Princípios Físicos:**
        
        1. **Formação da Nuvem:** Um vazamento de gás ou líquido volátil forma uma nuvem de vapor que se mistura 
           com o ar. A nuvem deve estar dentro dos limites de inflamabilidade (LFL-UFL) para explodir.
        
        2. **Ignição:** Quando a nuvem encontra uma fonte de ignição (faísca, chama, superfície quente), 
           a combustão se propaga através da nuvem.
        
        3. **Confinamento e Turbulência:** A presença de obstáculos (edifícios, equipamentos, tubulações) 
           aumenta a turbulência e o confinamento, fazendo com que mais energia seja convertida em sobrepressão 
           ao invés de apenas radiação térmica.
        
        4. **Onda de Choque:** A sobrepressão gerada cria uma onda de choque que se propaga radialmente, 
           causando danos estruturais e lesões humanas.
        
        **Metodologia de Cálculo:**
        
        Este módulo utiliza o método de Equivalência TNT ajustado por eficiência de explosão:
        - A energia química disponível (massa × calor de combustão) é convertida em equivalente TNT
        - A eficiência de explosão depende do grau de confinamento e turbulência
        - A lei de escala de Hopkinson-Cranz relaciona a massa de TNT equivalente com os raios de dano
        - Diferentes níveis de sobrepressão correspondem a diferentes severidades de dano
        
        **Limitações do Modelo:**
        
        Este modelo assume detonação pontual e distribuição uniforme de energia. Em cenários reais, fatores como 
        geometria da nuvem, direção do vento, topografia e presença de múltiplas fontes de ignição podem alterar 
        significativamente os resultados.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros do Cenário")
        
        # Seleção de substância
        substancia = st.selectbox("Substância", list(SUBSTANCIAS_VCE.keys()))
        dados_substancia = SUBSTANCIAS_VCE[substancia]
        
        st.info(f"**{substancia}**\n\n**Tipo:** {dados_substancia['tipo']}\n\n**Descrição:** {dados_substancia['desc']}\n\n"
               f"**LFL:** {dados_substancia['LFL']}% vol | **UFL:** {dados_substancia['UFL']}% vol\n"
               f"**Calor de Combustão:** {dados_substancia['Hc']} MJ/kg\n"
               f"**Densidade relativa ao ar:** {dados_substancia['densidade_ar']:.2f}\n"
               f"**Reatividade:** {dados_substancia['reatividade']}")
        
        # Massa da nuvem
        massa = st.number_input("Massa da Nuvem de Vapor (kg)", value=1000.0, min_value=1.0, step=100.0, format="%.1f")
        
        # Grau de confinamento
        confinamento = st.selectbox(
            "Grau de Confinamento / Obstáculos",
            ["Campo Aberto (Sem Obstáculos)",
             "Urbano / Floresta (Obstáculos Médios)",
             "Refinaria / Processo (Muitos Tubos)",
             "Confinado (Túnel / Bunker)"],
            index=1
        )
        
        st.caption("**Nota:** O confinamento afeta a eficiência da explosão. Ambientes com mais obstáculos "
                  "geram maior sobrepressão devido ao aumento da turbulência.")

    with col2:
        st.subheader("Georreferenciamento")
        
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f")
        
        st.caption("Coordenadas do ponto de origem da explosão (centro da nuvem de vapor).")

    # Botão de cálculo
    if 'vce_calc' not in st.session_state:
        st.session_state['vce_calc'] = False
    
    if st.button("Calcular Zonas de Dano", type="primary", use_container_width=True):
        st.session_state['vce_calc'] = True

    if st.session_state['vce_calc']:
        # Calcular VCE
        raios, kg_tnt, eficiencia = calcular_vce(massa, dados_substancia, confinamento)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        m1, m2, m3 = st.columns(3)
        m1.metric("Equivalente TNT", f"{kg_tnt:.2f} kg", "Massa equivalente")
        m2.metric("Eficiência de Explosão", f"{eficiencia*100:.1f}%", "Fator de conversão")
        m3.metric("Energia Liberada", f"{massa * dados_substancia['Hc'] * eficiencia:.0f} MJ", "Energia total")
        
        # Zonas de dano
        st.markdown("#### Zonas de Dano por Sobrepressão")
        
        # Criar mapa
        m = folium.Map(location=[lat, lon], zoom_start=15)
        
        # Adicionar círculos de dano (do maior para o menor)
        cores_ordem = ["#f1c40f", "#f39c12", "#e74c3c", "#000000"]
        nomes_ordem = list(raios.keys())[::-1]  # Inverter para desenhar do maior para o menor
        
        for nome in nomes_ordem:
            raio = raios[nome]
            dados_limite = LIMITES_BLAST[nome]
            cor = dados_limite['cor']
            
            folium.Circle(
                location=[lat, lon],
                radius=raio,
                popup=f"{nome}<br>Sobrepressão: {dados_limite['psi']} psi ({dados_limite['bar']:.2f} bar)<br>Raio: {raio:.1f} m",
                tooltip=f"{nome} - {raio:.1f} m",
                color=cor,
                fill=True,
                fillColor=cor,
                fillOpacity=0.3,
                weight=2
            ).add_to(m)
        
        # Marcador do ponto de origem
        folium.Marker(
            [lat, lon],
            popup=f"Origem da Explosão<br>Substância: {substancia}<br>Massa: {massa:.1f} kg",
            tooltip="Ponto de Origem",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)
        
        # Exibir mapa
        st_folium(m, width=700, height=500)
        
        # Tabela de resultados
        st.markdown("#### Tabela de Zonas de Dano")
        
        df_resultados = pd.DataFrame({
            'Zona de Dano': list(raios.keys()),
            'Sobrepressão (psi)': [LIMITES_BLAST[nome]['psi'] for nome in raios.keys()],
            'Sobrepressão (bar)': [LIMITES_BLAST[nome]['bar'] for nome in raios.keys()],
            'Raio (m)': [raios[nome] for nome in raios.keys()],
            'Descrição': [LIMITES_BLAST[nome]['desc'] for nome in raios.keys()]
        })
        
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)
        
        # Interpretação e recomendações
        with st.expander("Interpretação dos Resultados e Recomendações Operacionais", expanded=False):
            st.markdown(f"""
            **Análise do Cenário:**
            
            - **Substância:** {substancia} ({dados_substancia['tipo']})
            - **Massa da Nuvem:** {massa:.1f} kg
            - **Energia Equivalente:** {kg_tnt:.2f} kg de TNT
            - **Eficiência de Explosão:** {eficiencia*100:.1f}% (afetada pelo confinamento: {confinamento})
            
            **Zonas de Risco:**
            
            """)
            
            for nome in nomes_ordem:
                raio = raios[nome]
                dados_limite = LIMITES_BLAST[nome]
                st.markdown(f"- **{nome}:** Raio de {raio:.1f} m ({dados_limite['bar']:.2f} bar / {dados_limite['psi']:.1f} psi)")
                st.markdown(f"  - {dados_limite['desc']}")
            
            st.markdown("""
            
            **Recomendações Operacionais:**
            
            1. **Evacuação Imediata:** Todas as pessoas dentro da zona de 0.5 psi devem ser evacuadas imediatamente.
            
            2. **Zona de Exclusão:** Estabelecer perímetro de segurança mínimo igual ao maior raio calculado.
            
            3. **Proteção de Estruturas Críticas:** Identificar estruturas críticas (hospitais, escolas, usinas) 
               dentro das zonas de dano e avaliar necessidade de reforço ou evacuação preventiva.
            
            4. **Planejamento de Resposta:** Coordenar com equipes de emergência para estabelecer rotas de fuga 
               que evitem as zonas de maior risco.
            
            5. **Monitoramento:** Implementar sistema de detecção de gás e monitoramento meteorológico para 
               avaliar mudanças nas condições que possam alterar o cenário.
            
            **Aviso Importante:** Este modelo é uma ferramenta de apoio à decisão. Os resultados devem ser 
            validados com medições de campo e considerações específicas do local. Fatores como topografia, 
            condições meteorológicas e geometria real da nuvem podem alterar significativamente os resultados.
            """)
