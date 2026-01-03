import streamlit as st
import folium
from streamlit_folium import st_folium
import math

# =============================================================================
# 1. BANCO DE DADOS (CONSTANTES GAMA ESPECÍFICAS)
# =============================================================================
# A Constante Gama (Γ) define a taxa de dose a 1 metro por Curie.
# Unidade usada: mSv·m²/h·Ci (Milisievert por hora a 1 metro por Curie)
# Fonte: Manuais de Proteção Radiológica (CNEN/IAEA)
ISOTOPOS_FONTE = {
    "Amerício-241 (Am-241)": {
        "gama": 0.1, 
        "meia_vida": "432 anos",
        "desc": "Emitem nêutrons se misturado com Berílio. Sozinho emite gama fraco. Comum em poços de petróleo.",
        "uso": "Perfilagem de Poços (Oil & Gas)"
    },
    "Antimônio-124 (Sb-124)": {
        "gama": 9.8, 
        "meia_vida": "60 dias",
        "desc": "Gama de alta energia. Usado misturado com Berílio para 'ligar' reatores nucleares (fonte de nêutrons de partida).",
        "uso": "Start-up de Reatores"
    },
    "Bário-133 (Ba-133)": {
        "gama": 2.4, 
        "meia_vida": "10.5 anos",
        "desc": "Padrão de calibração. Simula a energia do Iodo-131 mas dura muito mais tempo.",
        "uso": "Calibração de Detectores"
    },
    "Césio-134 (Cs-134)": {
        "gama": 8.7, 
        "meia_vida": "2 anos",
        "desc": "Irmão mais 'agressivo' do Cs-137. Encontrado em resíduos de reatores nucleares e acidentes de criticalidade.",
        "uso": "Resíduo de Fissão"
    },
    "Césio-137 (Cs-137)": {
        "gama": 3.3, 
        "meia_vida": "30 anos",
        "desc": "O isótopo de Goiânia. Pó (cloreto) ou cerâmica. Perigo de contaminação se aberto, mas aqui calculamos ele LACRADO.",
        "uso": "Medidores de Nível / Densidade"
    },
    "Cobalto-57 (Co-57)": {
        "gama": 0.9, 
        "meia_vida": "271 dias",
        "desc": "O 'primo fraco' do Co-60. Usado para testar gama-câmeras em hospitais antes do uso diário.",
        "uso": "Controle de Qualidade Hospitalar"
    },
    "Cobalto-60 (Co-60)": {
        "gama": 13.0, 
        "meia_vida": "5.2 anos",
        "desc": "Muito energético. Usado em esterilização de alimentos e radioterapia antiga. Brilha muito forte (gama alto).",
        "uso": "Irradiadores de Grande Porte"
    },
    "Crômio-51 (Cr-51)": {
        "gama": 0.16, 
        "meia_vida": "27 dias",
        "desc": "Baixíssima energia (raios-X moles). Usado para marcar hemácias e medir volume sanguíneo.",
        "uso": "Hematologia"
    },
    "Európio-152 (Eu-152)": {
        "gama": 5.8, 
        "meia_vida": "13.5 anos",
        "desc": "Fonte de referência com múltiplas energias de gama. Comum em laboratórios de física.",
        "uso": "Pesquisa / Calibração"
    },
    "Ferro-59 (Fe-59)": {
        "gama": 6.4, 
        "meia_vida": "44 dias",
        "desc": "Alta energia gama. Usado para estudar a formação de sangue (hematologia) e desgaste de motores.",
        "uso": "Estudos Metabólicos / Engenharia"
    },
    "Iodo-125 (I-125)": {
        "gama": 0.7, 
        "meia_vida": "60 dias",
        "desc": "Sementes minúsculas implantadas em próstatas. Baixa energia, fácil de blindar, mas perigoso se ingerido.",
        "uso": "Braquiterapia (Sementes)"
    },
    "Iodo-131 (I-131)": {
        "gama": 2.2, 
        "meia_vida": "8 dias",
        "desc": "Muito volátil. Produto de fissão nuclear (risco em reatores) e tratamento de tireoide. Acumula na tireoide humana.",
        "uso": "Terapia de Câncer / Radioproteção"
    },
    "Irídio-192 (Ir-192)": {
        "gama": 4.8, 
        "meia_vida": "74 dias",
        "desc": "O 'Vilão' da Gamagrafia. Usado para tirar Raio-X de soldas de tubulação. Causa 90% dos acidentes industriais.",
        "uso": "Gamagrafia Industrial"
    },
    "Manganês-54 (Mn-54)": {
        "gama": 4.7, 
        "meia_vida": "312 dias",
        "desc": "Produto de ativação em aços de reatores. Pode ser encontrado em sucata radioativa reciclada incorretamente.",
        "uso": "Contaminação de Sucata / Pesquisa"
    },
    "Ouro-198 (Au-198)": {
        "gama": 2.3, 
        "meia_vida": "2.7 dias",
        "desc": "Usado na indústria de petróleo para marcar o fluxo de óleo e em braquiterapia antiga.",
        "uso": "Indústria Petrolífera"
    },
    "Rádio-226 (Ra-226)": {
        "gama": 8.25, 
        "meia_vida": "1.600 anos",
        "desc": "O pai da radioatividade. Encontrado em para-raios antigos, ponteiros de relógios vintage e tintas luminescentes antigas.",
        "uso": "Histórico / Fontes Órfãs"
    },
    "Selênio-75 (Se-75)": {
        "gama": 2.0, 
        "meia_vida": "120 dias",
        "desc": "Substituto moderno do Irídio. Menor energia, mas ainda perigoso em curtas distâncias.",
        "uso": "Gamagrafia Industrial (Espaços Confinados)"
    },
    "Sódio-24 (Na-24)": {
        "gama": 18.4, 
        "meia_vida": "15 horas",
        "desc": "GAMA ULTRA FORTE. Brilha mais que o Cobalto e atravessa muito concreto. Usado para achar vazamentos em dutos enterrados.",
        "uso": "Traçador Industrial / Detecção de Vazamentos"
    },
    "Tecnécio-99m (Tc-99m)": {
        "gama": 0.78, 
        "meia_vida": "6 horas",
        "desc": "O isótopo mais comum da medicina. Baixa energia, mas usado em quantidades enormes (Curies altos) em hospitais.",
        "uso": "Medicina Nuclear (Cintilografia)"
    },
    "Zinco-65 (Zn-65)": {
        "gama": 2.7, 
        "meia_vida": "244 dias",
        "desc": "Emissor gama duro. Usado em estudos de desgaste de ligas metálicas e biologia marinha.",
        "uso": "Metalurgia / Biologia"
    }
}

# Limites de Dose Acumulada (Baseado em normas CNEN NN 3.01)
LIMITES_DOSE = {
    "Zona Quente (Perigo Agudo)": {
        "dose_mSv": 100.0, 
        "cor": "#FF0000", # Vermelho
        "desc": "Limite de intervenção para bombeiros. Risco de efeitos determinísticos (mudança no sangue) acima disso."
    },
    "Zona Controlada (Trabalhador)": {
        "dose_mSv": 20.0, 
        "cor": "#FF8C00", # Laranja
        "desc": "Limite anual para trabalhador nuclear. Área restrita apenas a pessoal monitorado (com dosímetro)."
    },
    "Zona Livre (Público)": {
        "dose_mSv": 1.0, 
        "cor": "#FFD700", # Amarelo
        "desc": "Limite anual para o público geral. Área segura para evacuação da população."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (LEI DO INVERSO DO QUADRADO)
# =============================================================================
def calcular_zonas_radiacao(atividade_ci, tempo_exposicao_min, gama_factor):
    """
    Calcula o raio (distância) onde a dose acumulada atinge os limites.
    Fórmula: D1 * d1^2 = D2 * d2^2  (Lei do Inverso do Quadrado)
    Dose_Total = (Gama * Atividade * Tempo_h) / Distancia^2
    Logo: Distancia = Raiz((Gama * Atividade * Tempo_h) / Dose_Limite)
    """
    # Conversão de tempo (minutos -> horas)
    tempo_h = tempo_exposicao_min / 60.0
    
    # Potencial de Dose Total a 1 metro (mSv)
    # Ex: Se tenho 10 Ci de Co-60 (Gama 13) por 1 hora:
    # Dose a 1m = 13 * 10 * 1 = 130 mSv.
    dose_a_1m = gama_factor * atividade_ci * tempo_h
    
    raios = {}
    
    for nome, dados in LIMITES_DOSE.items():
        limite = dados['dose_mSv']
        
        # Evitar divisão por zero se a dose for muito baixa
        if dose_a_1m > 0:
            # Isolando a Distância na fórmula
            distancia_m = math.sqrt(dose_a_1m / limite)
        else:
            distancia_m = 0
            
        # Travas de segurança visual (para o mapa não bugar com 0.0001m)
        if distancia_m < 0.5: distancia_m = 0 # Menor que meio metro consideramos zero para o mapa
        
        raios[nome] = distancia_m
        
    return raios, dose_a_1m

# =============================================================================
# 3. INTERFACE VISUAL
# =============================================================================
def renderizar():
    st.markdown("### ☢️ Radiológico (Fonte Pontual)")
    st.markdown("Cálculo de exposição direta a fontes seladas (Lei do Inverso do Quadrado).")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("📖 Entendendo a Exposição Radiológica (Sem Explosão)", expanded=True):
        st.markdown("""
        **Cenário:** Uma fonte radioativa (cápsula metálica) caiu de um caminhão ou foi esquecida num laboratório. Não há fumaça, não há cheiro.
        
        **A Lei da Sobrevivência (Tempo e Distância):**
        1.  **Afastamento:** A radiação cai drasticamente com a distância. Se você dobrar a distância, a dose cai para 1/4.
        2.  **Tempo:** A dose acumula. Ficar 1 minuto é ruim. Ficar 1 hora é 60x pior. O mapa abaixo mostra o risco acumulado pelo tempo que você definir.
        
        **Cores do Mapa:**
        * 🔴 **Vermelho (100 mSv):** Zona de Emergência. Risco imediato à saúde. Apenas resgate rápido.
        * 🟠 **Laranja (20 mSv):** Zona Controlada. Equivalente a 1 ano de trabalho nuclear recebido em poucos minutos.
        * 🟡 **Amarelo (1 mSv):** Zona Pública. Onde a população pode ficar esperando.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Local e Fonte")
        lat = st.number_input("Latitude", value=-22.8625, format="%.5f")
        lon = st.number_input("Longitude", value=-43.2245, format="%.5f")
        
        fonte_nome = st.selectbox("Isótopo da Fonte", list(ISOTOPOS_FONTE.keys()))
        dados_fonte = ISOTOPOS_FONTE[fonte_nome]
        
        st.info(f"ℹ️ **{fonte_nome}**\n\n{dados_fonte['desc']}\n\n*Meia-vida: {dados_fonte['meia_vida']}*")

    with col2:
        st.subheader("⚙️ Parâmetros do Incidente")
        
        atividade = st.number_input(
            "Atividade da Fonte (Curies - Ci)", 
            value=10.0, 
            min_value=0.1, 
            step=1.0, 
            help="A 'força' da fonte. Gamagrafia usa ~50 Ci. Radioterapia usa ~2.000 Ci."
        )
        
        tempo = st.number_input(
            "Tempo de Exposição (Minutos)", 
            value=60, 
            min_value=1, 
            step=10, 
            help="Quanto tempo a pessoa/equipe vai ficar parada perto da fonte? O mapa cresce conforme o tempo aumenta."
        )
        
        st.caption("Nota: O cálculo assume fonte nua (sem blindagem de chumbo).")

    # Estado
    if 'radio_calc' not in st.session_state: st.session_state['radio_calc'] = False
    
    if st.button("☢️ Calcular Zonas de Exposição", type="primary", use_container_width=True):
        st.session_state['radio_calc'] = True

    # Resultados
    if st.session_state['radio_calc']:
        
        raios, dose_1m = calcular_zonas_radiacao(atividade, tempo, dados_fonte['gama'])
        
        st.success(f"Cálculo Realizado. Dose potencial a 1 metro: **{dose_1m:.1f} mSv** em {tempo} minutos.")
        
        # Métricas visuais
        c1, c2, c3 = st.columns(3)
        c1.metric("Raio Vermelho (100 mSv)", f"{raios['Zona Quente (Perigo Agudo)']:.1f} m", "Perigo Agudo", delta_color="inverse")
        c2.metric("Raio Laranja (20 mSv)", f"{raios['Zona Controlada (Trabalhador)']:.1f} m", "Restrito", delta_color="off")
        c3.metric("Raio Amarelo (1 mSv)", f"{raios['Zona Livre (Público)']:.1f} m", "Segurança")

        # Mapa
        m = folium.Map(location=[lat, lon], zoom_start=18, tiles="OpenStreetMap")
        
        # Marcador do ponto quente
        folium.Marker(
            [lat, lon], 
            tooltip=f"Fonte: {fonte_nome} ({atividade} Ci)",
            icon=folium.Icon(color="purple", icon="radiation", prefix="fa")
        ).add_to(m)
        
        # Desenhar Círculos (Do maior para o menor)
        zonas_ordem = [
            ("Zona Livre (Público)", LIMITES_DOSE["Zona Livre (Público)"]),
            ("Zona Controlada (Trabalhador)", LIMITES_DOSE["Zona Controlada (Trabalhador)"]),
            ("Zona Quente (Perigo Agudo)", LIMITES_DOSE["Zona Quente (Perigo Agudo)"])
        ]
        
        for nome, dados in zonas_ordem:
            r = raios[nome]
            if r > 0.5:
                folium.Circle(
                    [lat, lon],
                    radius=r,
                    color=dados['cor'],
                    fill=True,
                    fill_opacity=0.3,
                    tooltip=f"{nome}: {r:.1f}m (Dose > {dados['dose_mSv']} mSv)"
                ).add_to(m)
        
        st_folium(m, width=None, height=600)