import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import pandas as pd

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
    },
    "Tálio-201 (Tl-201)": {
        "gama": 0.5,
        "meia_vida": "73 horas",
        "desc": "Isótopo médico usado em cintilografia cardíaca. Baixa energia gama, mas requer cuidados devido ao uso em grandes quantidades.",
        "uso": "Medicina Nuclear (Cardiologia)"
    },
    "Xenônio-133 (Xe-133)": {
        "gama": 0.1,
        "meia_vida": "5.2 dias",
        "desc": "Gás nobre radioativo. Usado em estudos de ventilação pulmonar. Volátil, pode se dispersar rapidamente se vazar.",
        "uso": "Medicina Nuclear (Pneumologia)"
    },
    "Túlio-170 (Tm-170)": {
        "gama": 0.03,
        "meia_vida": "128 dias",
        "desc": "Baixa energia gama. Usado em radiografia portátil e calibração de detectores de baixa energia.",
        "uso": "Radiografia Portátil / Calibração"
    },
    "Ítrio-90 (Y-90)": {
        "gama": 0.0,
        "meia_vida": "64 horas",
        "desc": "Emissor beta puro (sem gama). Usado em medicina nuclear para terapia. Risco de contaminação interna se ingerido.",
        "uso": "Medicina Nuclear (Terapia)"
    },
    "Estrôncio-90 (Sr-90)": {
        "gama": 0.0,
        "meia_vida": "28.8 anos",
        "desc": "Produto de fissão nuclear. Emissor beta puro. Acumula em ossos. Risco em acidentes nucleares e fontes órfãs.",
        "uso": "Produto de Fissão / Fontes Órfãs"
    },
    "Plutônio-239 (Pu-239)": {
        "gama": 0.06,
        "meia_vida": "24.100 anos",
        "desc": "Material físsil usado em armas nucleares e reatores. Emite principalmente alfa (perigoso se inalado). Gama fraco.",
        "uso": "Combustível Nuclear / Armas"
    },
    "Urânio-238 (U-238)": {
        "gama": 0.3,
        "meia_vida": "4.47 bilhões de anos",
        "desc": "Urânio natural. Emite principalmente alfa. Gama fraco. Risco químico e radiológico se inalado ou ingerido.",
        "uso": "Combustível Nuclear / Fontes Órfãs"
    },
    "Tório-232 (Th-232)": {
        "gama": 0.1,
        "meia_vida": "14 bilhões de anos",
        "desc": "Tório natural. Emite principalmente alfa. Gama fraco. Usado em mantas de gás e fontes órfãs antigas.",
        "uso": "Combustível Nuclear / Fontes Órfãs"
    },
    "Polônio-210 (Po-210)": {
        "gama": 0.0,
        "meia_vida": "138 dias",
        "desc": "Emissor alfa puro. Extremamente tóxico se inalado ou ingerido. Usado em fontes de nêutrons e fontes órfãs.",
        "uso": "Fontes de Nêutrons / Fontes Órfãs"
    },
    "Carbono-14 (C-14)": {
        "gama": 0.0,
        "meia_vida": "5.730 anos",
        "desc": "Emissor beta puro. Usado em datação por carbono e rastreamento biológico. Baixo risco externo, mas perigoso se ingerido.",
        "uso": "Datação / Rastreamento Biológico"
    },
    "Fósforo-32 (P-32)": {
        "gama": 0.0,
        "meia_vida": "14 dias",
        "desc": "Emissor beta puro de alta energia. Usado em medicina nuclear e pesquisa biológica. Acumula em ossos.",
        "uso": "Medicina Nuclear / Pesquisa"
    },
    "Enxofre-35 (S-35)": {
        "gama": 0.0,
        "meia_vida": "87 dias",
        "desc": "Emissor beta puro. Usado em rastreamento biológico e pesquisa. Baixo risco externo.",
        "uso": "Rastreamento Biológico / Pesquisa"
    },
    "Trítio (H-3)": {
        "gama": 0.0,
        "meia_vida": "12.3 anos",
        "desc": "Isótopo de hidrogênio. Emissor beta puro de baixa energia. Usado em sinais de saída de emergência e pesquisa.",
        "uso": "Sinais de Emergência / Pesquisa"
    },
    "Níquel-63 (Ni-63)": {
        "gama": 0.0,
        "meia_vida": "100 anos",
        "desc": "Emissor beta puro. Usado em detectores de ionização em fumaça e fontes de elétrons.",
        "uso": "Detectores / Fontes de Elétrons"
    }
}

# Limites de Dose Acumulada (Baseado em normas CNEN NN 3.01, ICRP 103, IAEA Safety Standards)
LIMITES_DOSE = {
    "Zona Quente (Perigo Agudo)": {
        "dose_mSv": 100.0,
        "cor": "#e74c3c",
        "desc": "Limite de intervenção para bombeiros e equipes de emergência. Risco de efeitos determinísticos "
               "(alterações no sangue, náusea, fadiga) acima deste nível. Exposição deve ser limitada ao mínimo necessário."
    },
    "Zona Controlada (Trabalhador)": {
        "dose_mSv": 20.0,
        "cor": "#f39c12",
        "desc": "Limite anual para trabalhador nuclear (CNEN NN 3.01). Área restrita apenas a pessoal radiologicamente "
               "qualificado e monitorado (com dosímetro). Requer controle de acesso e monitoramento contínuo."
    },
    "Zona Livre (Público)": {
        "dose_mSv": 1.0,
        "cor": "#f1c40f",
        "desc": "Limite anual para o público geral (CNEN NN 3.01). Área segura para evacuação da população e "
               "permanência prolongada. Acima deste limite, recomenda-se evacuação ou restrição de acesso."
    }
}

# =============================================================================
# 2. MOTOR DE CÁLCULO (LEI DO INVERSO DO QUADRADO)
# =============================================================================
def calcular_zonas_radiacao(atividade_ci, tempo_exposicao_min, gama_factor):
    """
    Calcula o raio (distância) onde a dose acumulada atinge os limites usando a Lei do Inverso do Quadrado.
    
    A Lei do Inverso do Quadrado estabelece que a intensidade da radiação diminui proporcionalmente ao 
    quadrado da distância da fonte. Para uma fonte pontual:
    
    Dose = (Gama * Atividade * Tempo) / Distância²
    
    Onde:
    - Gama: Constante gama do isótopo (mSv·m²/h·Ci)
    - Atividade: Atividade da fonte em Curies (Ci)
    - Tempo: Tempo de exposição em horas
    - Distância: Distância da fonte em metros
    
    Rearranjando para encontrar a distância onde a dose atinge um limite:
    Distância = √((Gama * Atividade * Tempo) / Dose_Limite)
    
    Parâmetros:
        atividade_ci: Atividade da fonte em Curies
        tempo_exposicao_min: Tempo de exposição em minutos
        gama_factor: Constante gama do isótopo (mSv·m²/h·Ci)
    
    Retorna:
        Tupla: (dicionário com raios de cada zona, dose a 1 metro)
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
    st.title("Irradiação de Ponto Fixo")
    st.markdown("**Cálculo de Exposição Radiológica: Análise de Zonas de Dose para Fontes Pontuais Seladas**")
    st.markdown("---")

    # --- GUIA DIDÁTICO ---
    with st.expander("Fundamentos da Exposição Radiológica e Lei do Inverso do Quadrado", expanded=True):
        st.markdown("""
        **O Cenário de Fonte Pontual:**
        
        Uma fonte radioativa selada (cápsula metálica contendo material radioativo) pode ser encontrada em diversos 
        contextos: acidentes de transporte, fontes órfãs abandonadas, laboratórios, instalações industriais, ou 
        equipamentos médicos. Diferente de uma explosão ou dispersão, a fonte permanece em um local fixo, emitindo 
        radiação continuamente.
        
        **Características Importantes:**
        
        - **Sem Dispersão:** O material radioativo permanece contido na cápsula. Não há contaminação do ar ou do solo 
          (a menos que a cápsula seja danificada).
        - **Invisível e Inodoro:** A radiação não pode ser detectada pelos sentidos humanos. Requer equipamentos de 
          detecção (contadores Geiger, dosímetros).
        - **Efeito Contínuo:** A fonte emite radiação constantemente enquanto estiver presente. A dose acumula com o tempo.
        
        **A Lei do Inverso do Quadrado:**
        
        A intensidade da radiação gama diminui proporcionalmente ao quadrado da distância da fonte. Esta é uma das 
        leis fundamentais da física da radiação:
        
        ```
        Dose ∝ 1 / Distância²
        ```
        
        **Implicações Práticas:**
        
        1. **Afastamento:** Se você dobrar a distância da fonte, a dose cai para 1/4 (25%). Se triplicar, cai para 1/9 (11%).
           O afastamento é a forma mais eficaz de reduzir a exposição.
        
        2. **Tempo:** A dose acumula linearmente com o tempo. Ficar 1 minuto próximo à fonte resulta em uma dose. 
           Ficar 1 hora resulta em 60 vezes essa dose. Minimizar o tempo de exposição é crucial.
        
        3. **Blindagem:** Materiais densos (chumbo, concreto) podem reduzir significativamente a radiação, mas este 
           modelo assume fonte "nua" (sem blindagem adicional).
        
        **Zonas de Dose:**
        
        Este módulo calcula três zonas baseadas em limites de dose acumulada:
        
        - **Zona Quente (100 mSv):** Limite de intervenção para equipes de emergência. Risco de efeitos determinísticos 
          (alterações no sangue, náusea, fadiga) acima deste nível. Exposição deve ser limitada ao mínimo necessário.
        
        - **Zona Controlada (20 mSv):** Limite anual para trabalhadores nuclear (CNEN NN 3.01). Área restrita a pessoal 
          radiologicamente qualificado e monitorado. Requer controle de acesso e monitoramento contínuo.
        
        - **Zona Livre (1 mSv):** Limite anual para o público geral. Área segura para evacuação da população e 
          permanência prolongada.
        
        **Limitações do Modelo:**
        
        Este modelo assume:
        - Fonte pontual (tamanho desprezível comparado à distância)
        - Sem blindagem adicional (fonte "nua")
        - Sem obstruções ou reflexões
        - Ar livre (sem confinamento)
        - Apenas radiação gama (não considera alfa, beta ou nêutrons)
        
        Em cenários reais, fatores como geometria da fonte, blindagem, obstruções, confinamento e outros tipos de 
        radiação podem alterar significativamente os resultados. Sempre valide com medições de campo.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parâmetros da Fonte Radioativa")
        
        fonte_nome = st.selectbox("Isótopo da Fonte", 
                                  list(ISOTOPOS_FONTE.keys()),
                                  help="Selecione o isótopo radioativo presente na fonte.")
        dados_fonte = ISOTOPOS_FONTE[fonte_nome]
        
        st.info(f"**{fonte_nome}**\n\n**Descrição:** {dados_fonte['desc']}\n\n"
               f"**Uso Típico:** {dados_fonte['uso']}\n\n"
               f"**Meia-vida:** {dados_fonte['meia_vida']}\n\n"
               f"**Constante Gama:** {dados_fonte['gama']} mSv·m²/h·Ci")
        
        if dados_fonte['gama'] == 0.0:
            st.warning("**Atenção:** Este isótopo não emite radiação gama significativa (emissor alfa/beta puro). "
                      "O risco principal é de contaminação interna se inalado ou ingerido, não exposição externa.")
        
        st.subheader("Georreferenciamento")
        lat = st.number_input("Latitude", value=-22.9068, format="%.6f",
                             help="Coordenada de latitude da localização da fonte.")
        lon = st.number_input("Longitude", value=-43.1729, format="%.6f",
                             help="Coordenada de longitude da localização da fonte.")

    with col2:
        st.subheader("Parâmetros de Exposição")
        
        atividade = st.number_input(
            "Atividade da Fonte (Curies - Ci)", 
            value=10.0, 
            min_value=0.1, 
            step=1.0,
            format="%.1f",
            help="A 'força' da fonte radioativa. Exemplos: Gamagrafia industrial usa ~50 Ci, "
                 "Radioterapia usa ~2.000 Ci, Fontes de calibração usam ~0.1-1 Ci.")
        
        tempo = st.number_input(
            "Tempo de Exposição (Minutos)", 
            value=60, 
            min_value=1, 
            step=10,
            help="Quanto tempo a pessoa ou equipe permanecerá próximo à fonte? "
                 "A dose acumula linearmente com o tempo. O mapa mostra as zonas para este tempo de exposição.")
        
        st.caption("**Nota:** O cálculo assume fonte 'nua' (sem blindagem adicional de chumbo ou concreto). "
                  "Se a fonte estiver blindada, as zonas de risco serão menores.")

    # Estado
    if 'radio_calc' not in st.session_state:
        st.session_state['radio_calc'] = False
    
    if st.button("Calcular Zonas de Exposição", type="primary", use_container_width=True):
        st.session_state['radio_calc'] = True

    # Resultados
    if st.session_state['radio_calc']:
        
        raios, dose_1m = calcular_zonas_radiacao(atividade, tempo, dados_fonte['gama'])
        
        st.markdown("---")
        st.markdown("### Resultados da Análise")
        
        # Alerta se isótopo não emite gama
        if dados_fonte['gama'] == 0.0:
            st.warning("**Atenção:** Este isótopo não emite radiação gama significativa. As zonas calculadas são "
                      "para exposição externa. O risco principal é de contaminação interna se o material for liberado "
                      "e inalado ou ingerido.")
        
        st.info(f"**Dose Potencial a 1 Metro:** {dose_1m:.2f} mSv em {tempo} minutos de exposição.")
        
        # Métricas visuais
        st.markdown("#### Zonas de Dose por Distância")
        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Quente (100 mSv)", f"{raios['Zona Quente (Perigo Agudo)']:.1f} m", 
                 "Perigo Agudo", delta_color="inverse",
                 help="Limite de intervenção para equipes de emergência")
        c2.metric("Zona Controlada (20 mSv)", f"{raios['Zona Controlada (Trabalhador)']:.1f} m", 
                 "Restrito a Trabalhadores", delta_color="off",
                 help="Limite anual para trabalhadores nuclear")
        c3.metric("Zona Livre (1 mSv)", f"{raios['Zona Livre (Público)']:.1f} m", 
                 "Seguro para Público",
                 help="Limite anual para público geral")

        # Mapa
        st.markdown("---")
        st.markdown("#### Visualização Geográfica das Zonas de Dose")
        
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
        
        # Marcador da fonte
        folium.Marker(
            [lat, lon],
            popup=f"<b>Fonte Radioativa</b><br>Isótopo: {fonte_nome}<br>Atividade: {atividade:.1f} Ci<br>"
                 f"Tempo de Exposição: {tempo} min<br>Dose a 1m: {dose_1m:.2f} mSv",
            tooltip="Localização da Fonte",
            icon=folium.Icon(color="purple", icon="exclamation-triangle", prefix="fa")
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
                    popup=f"<b>{nome}</b><br>Raio: {r:.1f} m<br>Dose Limite: {dados['dose_mSv']} mSv<br><br>{dados['desc']}",
                    tooltip=f"{nome}: {r:.1f} m ({dados['dose_mSv']} mSv)",
                    color=dados['cor'],
                    fill=True,
                    fillColor=dados['cor'],
                    fillOpacity=0.25,
                    weight=2
                ).add_to(m)
        
        st_folium(m, width=700, height=500)
        
        # Tabela de resultados
        st.markdown("#### Tabela de Zonas de Dose")
        
        df_resultados = pd.DataFrame({
            'Zona de Dose': list(raios.keys()),
            'Dose Limite (mSv)': [LIMITES_DOSE[nome]['dose_mSv'] for nome in raios.keys()],
            'Raio (m)': [raios[nome] for nome in raios.keys()],
            'Descrição': [LIMITES_DOSE[nome]['desc'] for nome in raios.keys()]
        })
        
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)
        
        # Recomendações operacionais
        st.markdown("---")
        with st.expander("Recomendações Operacionais", expanded=False):
            st.markdown(f"""
            **Cenário Analisado:**
            - **Isótopo:** {fonte_nome}
            - **Atividade:** {atividade:.1f} Ci
            - **Tempo de Exposição:** {tempo} minutos
            - **Dose a 1 Metro:** {dose_1m:.2f} mSv
            
            **Zonas de Risco:**
            """)
            
            for nome, dados in zonas_ordem:
                r = raios[nome]
                st.markdown(f"- **{nome}:** Raio de {r:.1f} m (Dose limite: {dados['dose_mSv']} mSv)")
                st.markdown(f"  - {dados['desc']}")
            
            st.markdown("""
            
            **Ações Recomendadas:**
            
            1. **Isolamento Imediato:**
               - Estabelecer perímetro de segurança mínimo igual ao maior raio calculado
               - Restringir acesso à zona controlada apenas a pessoal radiologicamente qualificado
               - Evacuar público geral da zona livre se tempo de exposição for prolongado
            
            2. **Proteção de Equipes:**
               - Equipes de emergência devem usar dosímetros pessoais
               - Limitar tempo de exposição na zona quente ao mínimo necessário
               - Implementar sistema de rotação de pessoal para evitar exposição excessiva
               - Usar blindagem portátil (escudos de chumbo) se disponível
            
            3. **Recuperação da Fonte:**
               - Usar ferramentas de longo alcance para manipular a fonte
               - Transportar em recipiente blindado apropriado
               - Verificar integridade da cápsula antes do transporte
               - Notificar autoridades competentes (CNEN, órgãos ambientais)
            
            4. **Monitoramento:**
               - Verificar níveis de radiação com contadores Geiger em múltiplos pontos
               - Confirmar que não há contaminação (fonte deve estar selada)
               - Monitorar pessoal exposto após o incidente
            
            5. **Documentação:**
               - Registrar doses recebidas por cada membro da equipe
               - Documentar localização e condições da fonte
               - Reportar incidente às autoridades competentes
            
            **Importante:** Este modelo assume fonte pontual sem blindagem. Se a fonte estiver blindada ou em 
            recipiente de transporte, as zonas de risco serão menores. Sempre valide com medições de campo usando 
            equipamentos de detecção apropriados.
            """)