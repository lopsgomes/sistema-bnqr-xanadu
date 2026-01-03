import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import pandas as pd

# --- 1. BANCO DE DADOS DIDÁTICO (Física + Contexto) ---
# Além do fator matemático, adicionamos descrições para educar o usuário
MATERIAIS = {
    "TNT (Trinitrotolueno)": {
        "fator": 1.00, 
        "tipo": "Explosivo Sólido",
        "desc": "Padrão mundial de referência. Detonação ideal e supersônica."
    },
    "C4 (Militar)": {
        "fator": 1.37, 
        "tipo": "Explosivo Sólido",
        "desc": "Explosivo plástico de alta velocidade. 37% mais forte que o TNT."
    },
    "ANFO (Nitrato de Amônio)": {
        "fator": 0.74, 
        "tipo": "Explosivo Industrial",
        "desc": "Usado em mineração. Requer 'booster' para detonar."
    },
    "Hidrogênio (H2)": {
        "fator": 2.04, 
        "tipo": "Gás / VCE",
        "desc": "Energia altíssima por kg. Chama invisível e detonação rápida."
    },
    "Gás Natural (Metano)": {
        "fator": 1.12, 
        "tipo": "Gás / VCE",
        "desc": "Gás encanado de rua. Mais leve que o ar (se dissipa rápido)."
    },
    "GLP (Gás de Cozinha)": {
        "fator": 1.15, 
        "tipo": "Gás / VCE",
        "desc": "Gás liquefeito (P-13). Mais pesado que o ar (acumula em baixadas/porões)."
    },
    "Acetileno": {
        "fator": 1.68, 
        "tipo": "Gás Instável",
        "desc": "Usado em solda. Extremamente instável e potente."
    },
    "Vapor de Gasolina": {
        "fator": 1.10, 
        "tipo": "Vapor Inflamável",
        "desc": "Explosão ocorre quando o líquido evapora e mistura com ar."
    },
    "RDX (Ciclotrimetilenotrinitramina)": {
        "fator": 1.60,
        "tipo": "Explosivo Militar",
        "desc": "Componente principal do C4. Explosivo de alta velocidade. Muito estável até detonação."
    },
    "PETN (Pentaeritritol Tetranitrato)": {
        "fator": 1.66,
        "tipo": "Explosivo Militar",
        "desc": "Explosivo secundário de alta velocidade. Usado em detonadores e cordas detonantes."
    },
    "HMX (Octogen)": {
        "fator": 1.70,
        "tipo": "Explosivo Militar",
        "desc": "Um dos explosivos mais potentes conhecidos. Usado em ogivas militares e aplicações espaciais."
    },
    "Nitroglicerina": {
        "fator": 1.50,
        "tipo": "Explosivo Líquido",
        "desc": "Explosivo líquido extremamente sensível. Componente da dinamite. Muito instável."
    },
    "Dinamite (Gelatina)": {
        "fator": 1.20,
        "tipo": "Explosivo Industrial",
        "desc": "Nitroglicerina estabilizada com absorvente. Usada em mineração e demolição."
    },
    "Etileno": {
        "fator": 1.30,
        "tipo": "Gás Combustível",
        "desc": "Gás petroquímico. Amplo intervalo de inflamabilidade. Muito reativo."
    },
    "Propano (Puro)": {
        "fator": 1.18,
        "tipo": "Gás Liquefeito",
        "desc": "Componente do GLP. Gás pressurizado, mais pesado que o ar. Acumula em baixadas."
    },
    "Butano (Puro)": {
        "fator": 1.16,
        "tipo": "Gás Liquefeito",
        "desc": "Componente do GLP. Similar ao propano, mas com pressão de vapor menor."
    },
    "Etanol (Vapor)": {
        "fator": 1.05,
        "tipo": "Vapor Orgânico",
        "desc": "Vapor de álcool etílico. Combustível e solvente. Menos energético que hidrocarbonetos."
    },
    "Acetona (Vapor)": {
        "fator": 1.08,
        "tipo": "Vapor Orgânico",
        "desc": "Vapor de cetona. Solvente comum. Vapor mais pesado que o ar."
    },
    "Hexano (Vapor)": {
        "fator": 1.12,
        "tipo": "Vapor de Hidrocarboneto",
        "desc": "Vapor de hidrocarboneto alifático. Solvente industrial. Vapor muito pesado."
    },
    "Benzeno (Vapor)": {
        "fator": 1.10,
        "tipo": "Vapor Aromático",
        "desc": "Vapor de hidrocarboneto aromático. Carcinogênico. Usado em petroquímica."
    },
    "Pólvora Negra": {
        "fator": 0.55,
        "tipo": "Explosivo Deflagrante",
        "desc": "Explosivo antigo. Queima rapidamente mas não detona como TNT. Baixa eficiência."
    },
    "Cloreto de Polivinila (PVC)": {
        "fator": 0.40,
        "tipo": "Material Combustível",
        "desc": "Plástico comum. Quando queima em condições confinadas pode gerar sobrepressão limitada."
    }
}

# Limites de Sobrepressão (Overpressure) - PSI e BAR
# Fonte: TNO Green Book, CCPS Guidelines, Manuais de Engenharia Militar
LIMITES_BLAST = {
    "Zona Letal (20 psi)": {
        "psi": 20.0,
        "bar": 1.38,
        "z": 2.5,
        "cor": "#e74c3c",
        "desc": "Morte provável. Colapso total de estruturas de concreto armado. Hemorragia pulmonar severa."
    },
    "Zona de Lesão Grave (5 psi)": {
        "psi": 5.0,
        "bar": 0.34,
        "z": 5.6,
        "cor": "#f39c12",
        "desc": "Ruptura de tímpanos. Fraturas por arremesso. Paredes de alvenaria colapsam. Árvores arrancadas."
    },
    "Zona de Estilhaços (1 psi)": {
        "psi": 1.0,
        "bar": 0.07,
        "z": 14.8,
        "cor": "#f1c40f",
        "desc": "Janelas e vidros quebram, gerando estilhaços perigosos. 80% dos feridos em explosões urbanas estão nesta zona."
    }
}

# --- 2. MOTOR DE CÁLCULO (Hopkinson-Cranz) ---
def calcular_raios_destruicao(massa_kg, fator_tnt, eficiencia_perc):
    """
    Calcula zonas de sobrepressão baseadas na Equivalência TNT usando a Lei de Escala de Hopkinson-Cranz.
    
    Parâmetros:
        massa_kg: Massa total do material explosivo (kg)
        fator_tnt: Fator de equivalência TNT do material
        eficiencia_perc: Eficiência da detonação (0-100%)
    
    Retorna:
        Dicionário com raios de cada zona de dano e equivalente TNT
    """
    # 1. Massa Efetiva: Nem todo o material explode completamente
    # A eficiência ajusta a fração que realmente participa da detonação
    massa_tnt_efetiva = massa_kg * fator_tnt * (eficiencia_perc / 100.0)
    
    # 2. Lei de Escala de Hopkinson-Cranz
    # A distância escalonada Z = R / W^(1/3) relaciona a distância R com a massa W
    # Para cada nível de sobrepressão, existe um valor de Z característico
    # Rearranjando: R = Z × W^(1/3)
    
    if massa_tnt_efetiva > 0:
        raiz_cubica_w = math.pow(massa_tnt_efetiva, 1/3)
    else:
        raiz_cubica_w = 0
    
    # Calcular raios para cada zona de dano
    raios = {}
    for nome, dados in LIMITES_BLAST.items():
        z = dados['z']
        raio = z * raiz_cubica_w
        raios[nome] = raio
    
    return raios, massa_tnt_efetiva

# --- 3. INTERFACE DO USUÁRIO ---
def renderizar():
    st.title("Ondas de Choque e VCE")
    st.markdown("**Modelagem de Explosões: Análise de Sobrepressão e Zonas de Dano por Onda de Choque**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Modelagem de Explosões e Ondas de Choque", expanded=True):
        st.markdown("""
        **O que é uma Onda de Choque?**
        
        Uma onda de choque é uma parede de ar comprimido que se propaga a velocidades supersônicas a partir 
        do ponto de uma explosão. Diferente do fogo e estilhaços, a onda de choque causa danos estruturais 
        e lesões humanas mesmo a distâncias significativas do epicentro.
        
        **Mecanismos de Dano:**
        
        1. **Sobrepressão Estática:** A pressão instantânea esmaga estruturas e órgãos ocos (pulmões, ouvidos).
        2. **Vento de Explosão:** O movimento do ar resultante arremessa pessoas e objetos.
        3. **Reflexão:** A onda reflete em superfícies sólidas, aumentando a sobrepressão localmente.
        4. **Estilhaços Secundários:** Vidros e estruturas quebram, gerando projéteis perigosos.
        
        **Lei de Escala de Hopkinson-Cranz:**
        
        A distância de dano de uma explosão escala com a raiz cúbica da massa de TNT equivalente:
        **R = Z × W^(1/3)**
        
        Onde:
        - R = raio de dano (m)
        - Z = distância escalonada (constante para cada nível de sobrepressão)
        - W = massa equivalente de TNT (kg)
        
        **Equivalência TNT:**
        
        Diferentes materiais têm diferentes potências explosivas. O fator de equivalência TNT converte a 
        massa de qualquer material para sua massa equivalente em TNT. Por exemplo:
        - 1 kg de C4 ≈ 1.37 kg de TNT
        - 1 kg de Hidrogênio ≈ 2.04 kg de TNT
        - 1 kg de GLP ≈ 1.15 kg de TNT
        
        **Eficiência de Detonação:**
        
        Nem toda a massa de um material participa efetivamente da explosão:
        - **Explosivos sólidos (TNT, C4, ANFO):** Eficiência próxima de 100% (já contêm o oxidante)
        - **Gases e vapores (VCE):** Eficiência típica de 10-30% (precisam se misturar com o ar)
        
        **Zonas de Dano:**
        
        - **20 psi (1.38 bar):** Zona letal. Colapso total de estruturas. Morte provável.
        - **5 psi (0.34 bar):** Zona de lesão grave. Ruptura de tímpanos. Fraturas. Colapso de alvenaria.
        - **1 psi (0.07 bar):** Zona de estilhaços. Quebra de vidros. 80% dos feridos em explosões urbanas.
        
        **Limitações do Modelo:**
        
        Este modelo assume detonação pontual em superfície e distribuição uniforme de energia. Em cenários 
        reais, fatores como geometria da explosão, confinamento, topografia e múltiplas fontes podem alterar 
        significativamente os resultados.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros da Fonte Explosiva")
        
        nome_material = st.selectbox("Material Explosivo", list(MATERIAIS.keys()), index=0, 
                                     help="Selecione o material envolvido na explosão.")
        dados_mat = MATERIAIS[nome_material]
        
        st.info(f"**{nome_material}**\n\n**Tipo:** {dados_mat['tipo']}\n\n**Descrição:** {dados_mat['desc']}\n\n"
               f"**Fator de Equivalência TNT:** {dados_mat['fator']:.2f}")
        
        massa = st.number_input("Massa Total (kg)", min_value=0.1, value=50.0, step=1.0, 
                               help="Massa total do material explosivo disponível. "
                                   "Exemplos: Botijão P-13 = 13 kg, Cilindro P-45 = 45 kg, "
                                   "Caminhão tanque = 10.000-30.000 kg.")
        
        # Lógica para sugerir eficiência baseada no tipo de material
        if any(x in nome_material for x in ["TNT", "C4", "ANFO", "RDX", "PETN", "HMX", "Dinamite", "Nitroglicerina", "Pólvora"]):
            eficiencia_default = 100
            help_eficiencia = "Explosivos sólidos e líquidos detonam quase completamente (eficência próxima de 100%)."
        else:
            eficiencia_default = 20
            help_eficiencia = ("Gases e vapores (VCE) raramente detonam completamente. Apenas 10-30% da massa "
                             "geralmente participa da explosão real devido à necessidade de mistura com o ar.")
            
        eficiencia = st.slider("Eficiência da Detonação (%)", 1, 100, eficiencia_default, 
                              help=help_eficiencia)

    with col2:
        st.subheader("Georreferenciamento")
        
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f",
                             help="Coordenada de latitude do ponto de origem da explosão.")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f",
                             help="Coordenada de longitude do ponto de origem da explosão.")
        
        st.caption("Coordenadas do epicentro da explosão (ponto de origem).")

    # Controle de Estado
    if 'blast_calculado' not in st.session_state:
        st.session_state['blast_calculado'] = False

    if st.button("Calcular Zonas de Dano", type="primary", use_container_width=True):
        st.session_state['blast_calculado'] = True

    # Resultados
    if st.session_state['blast_calculado']:
        fator = dados_mat['fator']
        raios, tnt_eq = calcular_raios_destruicao(massa, fator, eficiencia)
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Métricas principais
        m1, m2 = st.columns(2)
        m1.metric("Equivalente TNT", f"{tnt_eq:.2f} kg", f"{tnt_eq/1000:.3f} toneladas")
        m2.metric("Massa Original", f"{massa:.1f} kg", f"Eficiência: {eficiencia}%")
        
        st.markdown("---")
        st.markdown("#### Zonas de Dano por Sobrepressão")
        
        # Métricas das zonas
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Zona Letal (20 psi)", f"{raios['Zona Letal (20 psi)']:.1f} m", 
                     "1.38 bar", delta_color="inverse",
                     help="Morte provável. Colapso total de estruturas de concreto armado.")
        with c2:
            st.metric("Zona de Lesão Grave (5 psi)", f"{raios['Zona de Lesão Grave (5 psi)']:.1f} m", 
                     "0.34 bar", delta_color="off",
                     help="Ruptura de tímpanos. Fraturas por arremesso. Colapso de alvenaria.")
        with c3:
            st.metric("Zona de Estilhaços (1 psi)", f"{raios['Zona de Estilhaços (1 psi)']:.1f} m", 
                     "0.07 bar",
                     help="Janelas quebram gerando estilhaços. 80% dos feridos em explosões urbanas.")

        # Mapa Folium
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")

        # Marcador do Epicentro
        folium.Marker(
            [lat, lon],
            popup=f"<b>Epicentro da Explosão</b><br>Material: {nome_material}<br>Massa: {massa:.1f} kg<br>Equivalente TNT: {tnt_eq:.2f} kg",
            tooltip="Ponto de Origem",
            icon=folium.Icon(color="black", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)

        # Círculos concêntricos (do maior para o menor)
        zonas_ordem = [
            ("Zona de Estilhaços (1 psi)", LIMITES_BLAST["Zona de Estilhaços (1 psi)"]),
            ("Zona de Lesão Grave (5 psi)", LIMITES_BLAST["Zona de Lesão Grave (5 psi)"]),
            ("Zona Letal (20 psi)", LIMITES_BLAST["Zona Letal (20 psi)"])
        ]
        
        for nome_zona, dados_limite in zonas_ordem:
            raio = raios[nome_zona]
            if raio > 0:
                folium.Circle(
                    [lat, lon],
                    radius=raio,
                    popup=f"<b>{nome_zona}</b><br>Raio: {raio:.1f} m<br>Sobrepressão: {dados_limite['psi']} psi ({dados_limite['bar']:.2f} bar)<br><br>{dados_limite['desc']}",
                    tooltip=f"{nome_zona}: {raio:.1f} m",
                    color=dados_limite['cor'],
                    fill=True,
                    fillColor=dados_limite['cor'],
                    fillOpacity=0.25,
                    weight=2
                ).add_to(m)

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
            
            - **Material:** {nome_material} ({dados_mat['tipo']})
            - **Massa Total:** {massa:.1f} kg
            - **Fator de Equivalência TNT:** {fator:.2f}
            - **Eficiência de Detonação:** {eficiencia}%
            - **Equivalente TNT:** {tnt_eq:.2f} kg ({tnt_eq/1000:.3f} toneladas)
            """)
            
            st.markdown("""
            **Zonas de Risco:**
            """)
            
            for nome_zona, dados_limite in zonas_ordem:
                r = raios[nome_zona]
                st.markdown(f"- **{nome_zona}:** Raio de {r:.1f} m ({dados_limite['bar']:.2f} bar / {dados_limite['psi']:.1f} psi)")
                st.markdown(f"  - {dados_limite['desc']}")
            
            st.markdown("""
            
            **Recomendações Operacionais:**
            
            1. **Evacuação Imediata:** Todas as pessoas dentro da zona de 1 psi devem ser evacuadas imediatamente. 
               Esta zona representa risco de estilhaços mesmo que a sobrepressão não seja letal.
            
            2. **Zona de Exclusão:** Estabelecer perímetro de segurança mínimo igual ao maior raio calculado, 
               considerando possíveis reflexões e efeitos de confinamento.
            
            3. **Proteção de Estruturas Críticas:** Identificar estruturas críticas (hospitais, escolas, usinas, 
               tanques adjacentes) dentro das zonas de dano. Estruturas dentro da zona letal (20 psi) sofrerão 
               colapso total.
            
            4. **Planejamento de Resposta:** Coordenar com equipes de emergência para estabelecer rotas de fuga 
               que evitem todas as zonas de impacto identificadas.
            
            5. **Monitoramento:** Implementar sistema de detecção e alerta para mudanças nas condições que possam 
               alterar o cenário (múltiplas explosões, confinamento adicional).
            
            6. **Avaliação Pós-Evento:** Após o evento, avaliar estruturas dentro da zona de 5 psi para danos 
               estruturais que possam causar colapso secundário.
            
            **Aviso Importante:** Este modelo assume detonação pontual em superfície. Em cenários reais, fatores 
            como geometria da explosão, confinamento, topografia, reflexões em superfícies próximas e múltiplas 
            fontes podem alterar significativamente os resultados. A sobrepressão pode ser amplificada por 
            confinamento (edifícios, túneis) ou reduzida por obstáculos que dispersam a onda. Sempre valide com 
            observações de campo e considere múltiplos cenários.
            """)