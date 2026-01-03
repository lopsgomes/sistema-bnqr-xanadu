import streamlit as st
import folium
from streamlit_folium import st_folium
import math

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
    }
}

# --- 2. MOTOR DE CÁLCULO (Hopkinson-Cranz) ---
def calcular_raios_destruicao(massa_kg, fator_tnt, eficiencia_perc):
    """
    Calcula zonas de sobrepressão baseadas na Equivalência TNT.
    """
    # 1. Massa Efetiva: Nem todo o gás explode. A eficiência ajusta isso.
    massa_tnt_efetiva = massa_kg * fator_tnt * (eficiencia_perc / 100.0)
    
    # 2. Constantes de Distância Escalonada (Z) para Detonação em Superfície
    # Fonte: Manuais de Engenharia Militar / TNO Green Book
    
    # Z = 14.8 -> 1 psi (Vidros/Janelas)
    # Z = 5.6  -> 5 psi (Tímpanos/Tijolos)
    # Z = 2.5  -> 20 psi (Demolição/Pulmões)
    
    raiz_cubica_w = math.pow(massa_tnt_efetiva, 1/3)
    
    raio_vidro = 14.8 * raiz_cubica_w
    raio_lesao = 5.6 * raiz_cubica_w
    raio_letal = 2.5 * raiz_cubica_w
    
    return raio_letal, raio_lesao, raio_vidro, massa_tnt_efetiva

# --- 3. INTERFACE VISUAL (FRONT-END) ---
def renderizar():
    st.markdown("### 💥 Onda de Choque (Explosão / Blast)")
    st.markdown("Modelagem de danos por sobrepressão atmosférica (psi) usando Equivalência TNT.")
    st.markdown("---")

    # --- GUIA DIDÁTICO EXPANSÍVEL (Igual ao Nuclear) ---
    with st.expander("📖 Guia Didático: Entendendo a Explosão", expanded=True):
        st.markdown("""
        **O que mata numa explosão?**
        Além do fogo e estilhaços, existe a **Onda de Choque**: uma parede de ar comprimido que viaja mais rápido que o som. Ela esmaga órgãos ocos (pulmões, ouvidos) e derruba prédios.

        **Como preencher:**
        1. **Material:** Selecione o combustível. O sistema converte tudo para "Quilos de TNT" para padronizar o cálculo.
        2. **Massa (kg):** Quanto combustível vazou?
           * *Botijão de Cozinha (P-13):* 13 kg.
           * *Cilindro Industrial (P-45):* 45 kg.
           * *Caminhão Tanque:* 10.000 a 30.000 kg.
        3. **Eficiência (%):** * **TNT/C4 (Sólidos):** Use **100%**. Eles já carregam o oxigênio dentro deles.
           * **Gás/Vapor (GLP/Gasolina):** Use **10% a 30%**. O gás precisa se misturar com o ar antes. Nunca a nuvem inteira explode perfeitamente.

        **Interpretação das Zonas (Círculos):**
        * 🔴 **Vermelho (20 psi):** Zona Letal. Prédios colapsam, pulmões sofrem hemorragia grave.
        * 🟠 **Laranja (5 psi):** Tímpanos estouram, pessoas são arremessadas, paredes de tijolo caem.
        * 🟡 **Amarelo (1 psi):** Zona de Estilhaços. Janelas quebram e voam como navalhas. **80% dos feridos em cidades estão aqui.**
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Localização")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f", help="Botão direito no Google Maps -> Copie o primeiro número.")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f", help="Botão direito no Google Maps -> Copie o segundo número.")
        
        st.info("💡 Dica: Se não souber a massa exata, estime pelo tamanho do tanque (veja o Guia acima).")

    with col2:
        st.subheader("🔥 Fonte da Explosão")
        
        # Seleção com descrição dinâmica
        nome_material = st.selectbox("Material Envolvido", list(MATERIAIS.keys()), index=5, help="Escolha o produto químico.")
        dados_mat = MATERIAIS[nome_material]
        
        # Mostra a descrição técnica do material escolhido
        st.caption(f"ℹ️ **Info:** {dados_mat['desc']} (Fator TNT: {dados_mat['fator']})")
        
        massa = st.number_input("Massa Total (kg)", min_value=1.0, value=50.0, step=10.0, help="Massa total de combustível disponível.")
        
        # Lógica inteligente para sugerir eficiência
        if "TNT" in nome_material or "C4" in nome_material or "ANFO" in nome_material:
            eficiencia_default = 100
            help_eficiencia = "Explosivos militares/industriais detonam completamente."
        else:
            eficiencia_default = 20
            help_eficiencia = "Nuvens de gás (VCE) raramente detonam 100%. Geralmente apenas 20% da massa participa da explosão real."
            
        eficiencia = st.slider("Eficiência da Detonação (%)", 1, 100, eficiencia_default, help=help_eficiencia)

    # Controle de Estado (Session State)
    if 'blast_calculado' not in st.session_state:
        st.session_state['blast_calculado'] = False

    if st.button("🚀 CALCULAR RAIOS DE DESTRUIÇÃO", type="primary", use_container_width=True):
        st.session_state['blast_calculado'] = True

    # Resultados
    if st.session_state['blast_calculado']:
        
        fator = dados_mat['fator']
        r_letal, r_lesao, r_vidro, tnt_eq = calcular_raios_destruicao(massa, fator, eficiencia)
        
        st.success(f"SIMULAÇÃO CONCLUÍDA. Energia liberada equivale a **{tnt_eq:.2f} kg de TNT**.")
        
        # Métricas com explicações curtas (Tooltips embutidos nos deltas)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Zona Letal (20 psi)", f"{r_letal:.1f} m", delta="Colapso Estrutural", delta_color="inverse", help="Morte provável e destruição total de concreto armado.")
        with c2:
            st.metric("Zona Lesão (5 psi)", f"{r_lesao:.1f} m", delta="Tímpanos/Ossos", delta_color="off", help="Ruptura de tímpanos e fraturas por arremesso.")
        with c3:
            st.metric("Zona Vidros (1 psi)", f"{r_vidro:.1f} m", delta="Estilhaços", help="Limite onde janelas quebram. Causa muitos cortes.")

        # Mapa Folium
        m = folium.Map(location=[lat, lon], zoom_start=17, tiles="OpenStreetMap")

        # Marcador Customizado
        folium.Marker(
            [lat, lon], 
            tooltip=f"<b>EPICENTRO</b><br>{nome_material}",
            icon=folium.Icon(color="black", icon="fire", prefix="fa")
        ).add_to(m)

        # Círculos Concêntricos (Do maior para o menor para garantir o clique no tooltip)
        # Amarelo (Vidros)
        folium.Circle(
            [lat, lon], radius=r_vidro, color="#FFD700", fill=True, fill_opacity=0.2,
            tooltip=f"<b>Zona de Vidros (1 psi)</b><br>Raio: {r_vidro:.1f}m<br>Janelas estilhaçadas."
        ).add_to(m)
        
        # Laranja (Lesão)
        folium.Circle(
            [lat, lon], radius=r_lesao, color="#FF8C00", fill=True, fill_opacity=0.3,
            tooltip=f"<b>Zona de Lesão (5 psi)</b><br>Raio: {r_lesao:.1f}m<br>Tímpanos rompidos."
        ).add_to(m)
        
        # Vermelho (Letal)
        folium.Circle(
            [lat, lon], radius=r_letal, color="#FF0000", fill=True, fill_opacity=0.4,
            tooltip=f"<b>Zona Letal (20 psi)</b><br>Raio: {r_letal:.1f}m<br>Colapso estrutural."
        ).add_to(m)

        st_folium(m, width=None, height=550)