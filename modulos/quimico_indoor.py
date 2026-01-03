import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# 1. BANCO DE DADOS (REFERÊNCIA DIDÁTICA)
# =============================================================================
SUBSTANCIAS_INDOOR = {
    "2-Mercaptoetanol (Beta)": {
        "mw": 78.13, "idlh": 150, "lel": 2.3, "volatilidade": 0.1, 
        "desc": "Cheiro de peixe podre. Fatal se inalado em alta dose. Evapora devagar, mas satura o ar."
    },
    "Acetato de Etila": {
        "mw": 88.11, "idlh": 2000, "lel": 2.0, "volatilidade": 0.8, 
        "desc": "Solvente comum (cheiro de removedor de esmalte). Muito inflamável, vapores viajam pelo chão."
    },
    "Acetona": {
        "mw": 58.08, "idlh": 2500, "lel": 2.5, "volatilidade": 0.6, 
        "desc": "Solvente padrão. Risco de incêndio alto, toxicidade aguda moderada."
    },
    "Acetonitrila": {
        "mw": 41.05, "idlh": 500, "lel": 3.0, "volatilidade": 0.7, 
        "desc": "Solvente de HPLC. Metaboliza-se em CIANETO no corpo horas após exposição."
    },
    "Ácido Acético (Solução)": {
        "mw": 60.05, "idlh": 50, "lel": 4.0, "volatilidade": 0.2, 
        "desc": "Vinagre concentrado. Vapores irritantes para olhos e nariz. Corrosivo."
    },
    "Ácido Acético Glacial": {
        "mw": 60.05, "idlh": 50, "lel": 4.0, "volatilidade": 0.4, 
        "desc": "Puro (>99%). Vapores sufocantes e inflamáveis acima de 39°C. Queimaduras severas."
    },
    "Ácido Clorídrico (Vapores HCl)": {
        "mw": 36.46, "idlh": 50, "lel": 0.0, "volatilidade": 0.8, 
        "desc": "Vapores brancos corrosivos. Destrói tecido pulmonar e corrói metais/eletrônicos."
    },
    "Ácido Nítrico (Fumegante)": {
        "mw": 63.01, "idlh": 25, "lel": 0.0, "volatilidade": 0.6, 
        "desc": "Oxidante enérgico. Inicia fogo em madeira/pano. Vapores vermelhos (NOx) causam edema pulmonar."
    },
    "Ácido Sulfúrico": {
        "mw": 98.08, "idlh": 15, "lel": 0.0, "volatilidade": 0.01, 
        "desc": "Não volátil. O perigo é contato direto ou névoa (spray). Gera calor violento com água."
    },
    "Acroleína": {
        "mw": 56.06, "idlh": 2, "lel": 2.8, "volatilidade": 0.9, 
        "desc": "Subproduto de incêndios. Lacrimogêneo potente e letal em dose ínfima."
    },
    "Amônia (25% ou Gás)": {
        "mw": 17.03, "idlh": 300, "lel": 15.0, "volatilidade": 0.9, 
        "desc": "Gás corrosivo. Perigo respiratório imediato (sufocamento). LEL alto, mas possível em espaços pequenos."
    },
    "Benzeno": {
        "mw": 78.11, "idlh": 500, "lel": 1.2, "volatilidade": 0.3, 
        "desc": "Carcinogênico Classe 1. Risco de explosão mesmo em vazamentos pequenos."
    },
    "Bromo (Líquido)": {
        "mw": 159.80, "idlh": 3, "lel": 0.0, "volatilidade": 0.7, 
        "desc": "Líquido vermelho fumegante. Queimaduras químicas graves. Toxidez aguda altíssima."
    },
    "Cianeto de Hidrogênio (HCN)": {
        "mw": 27.03, "idlh": 50, "lel": 5.6, "volatilidade": 1.0, 
        "desc": "EXTREMAMENTE TÓXICO. Cheiro de amêndoas. Ação fulminante (asfixia química)."
    },
    "Cloro Gás (Cl2)": {
        "mw": 70.90, "idlh": 10, "lel": 0.0, "volatilidade": 1.0, 
        "desc": "Oxidante forte. Corroi vias aéreas instantaneamente. Vapores verdes/amarelos."
    },
    "Clorofórmio": {
        "mw": 119.38, "idlh": 500, "lel": 0.0, "volatilidade": 0.5, 
        "desc": "Narcótico perigoso. Não explode, mas causa desmaio e morte silenciosa."
    },
    "Diclorometano (DCM)": {
        "mw": 84.93, "idlh": 2300, "lel": 13.0, "volatilidade": 0.9, 
        "desc": "Removedor de tintas. Metaboliza em Monóxido de Carbono no sangue. Narcótico."
    },
    "Disulfeto de Carbono": {
        "mw": 76.14, "idlh": 500, "lel": 1.3, "volatilidade": 1.0, 
        "desc": "PERIGO EXTREMO DE FOGO. Inflama a 90°C (lâmpada quente). Neurotóxico."
    },
    "Etanol (Álcool Etílico)": {
        "mw": 46.07, "idlh": 3300, "lel": 3.3, "volatilidade": 0.7, 
        "desc": "Inflamável comum. Risco principal é incêndio."
    },
    "Éter Etílico": {
        "mw": 74.12, "idlh": 1900, "lel": 1.9, "volatilidade": 1.0, 
        "desc": "Referência de evaporação. Vapores pesados descem para o chão e buscam tomadas."
    },
    "Formaldeído (Formol 37%)": {
        "mw": 30.03, "idlh": 20, "lel": 7.0, "volatilidade": 0.5, 
        "desc": "Fixador de tecidos. Irritante severo, sensibilizante e carcinogênico."
    },
    "Hidrazina": {
        "mw": 32.05, "idlh": 50, "lel": 4.7, "volatilidade": 0.2, 
        "desc": "Combustível de foguete. Hepatotóxico, carcinogênico e absorvido pela pele."
    },
    "Hidróxido de Sódio (Solução)": {
        "mw": 40.00, "idlh": 10, "lel": 0.0, "volatilidade": 0.01, 
        "desc": "Não volátil. Perigo é contato direto/respingo (Corrosivo). Não gera gás tóxico na sala."
    },
    "Isopropanol (IPA)": {
        "mw": 60.10, "idlh": 2000, "lel": 2.0, "volatilidade": 0.7, 
        "desc": "Álcool isopropílico. Vapores mais densos que o etanol."
    },
    "Mercúrio (Vapor)": {
        "mw": 200.59, "idlh": 1.2, "lel": 0.0, "volatilidade": 0.1, 
        "desc": "Metal líquido. Vapores invisíveis e inodoros causam danos neurológicos permanentes."
    },
    "Metanol": {
        "mw": 32.04, "idlh": 6000, "lel": 6.0, "volatilidade": 0.9, 
        "desc": "Chama invisível. Tóxico (cegueira) e absorvido pela pele."
    },
    "Metil Etil Cetona (MEK)": {
        "mw": 72.11, "idlh": 3000, "lel": 1.4, "volatilidade": 0.6, 
        "desc": "Similar à acetona, mas mais irritante. Vapores explosivos."
    },
    "Metil Isocianato (MIC)": {
        "mw": 57.05, "idlh": 3, "lel": 5.3, "volatilidade": 1.0, 
        "desc": "EXTREMO (Bhopal). Reage violentamente com água. Edema pulmonar em minutos."
    },
    "n-Hexano": {
        "mw": 86.18, "idlh": 1100, "lel": 1.1, "volatilidade": 0.9, 
        "desc": "Extremamente volátil. Vapores 'rastejam' longas distâncias (Flashback)."
    },
    "Óxido de Etileno": {
        "mw": 44.05, "idlh": 800, "lel": 3.0, "volatilidade": 1.0, 
        "desc": "Gás esterilizante. Cancerígeno, mutagênico e explosivo."
    },
    "Piridina": {
        "mw": 79.10, "idlh": 1000, "lel": 1.8, "volatilidade": 0.3, 
        "desc": "Odor nauseante. Afeta fígado e sistema nervoso. Inflamável."
    },
    "Sulfeto de Hidrogênio (H2S)": {
        "mw": 34.08, "idlh": 100, "lel": 4.0, "volatilidade": 1.0, 
        "desc": "Gás de esgoto. Cheiro de ovo podre que desaparece (anestesia olfativa) antes de matar."
    },
    "Tetrahidrofurano (THF)": {
        "mw": 72.11, "idlh": 2000, "lel": 2.0, "volatilidade": 0.9, 
        "desc": "Solvente de polímeros. Altamente inflamável. Forma peróxidos explosivos se seco."
    },
    "Tolueno": {
        "mw": 92.14, "idlh": 500, "lel": 1.1, "volatilidade": 0.5, 
        "desc": "Solvente de tintas. Narcótico forte, causa confusão mental rápida."
    },
    "Xileno": {
        "mw": 106.16, "idlh": 900, "lel": 1.1, "volatilidade": 0.4, 
        "desc": "Solvente aromático. Inflamável e neurotóxico."
    }
}


    


# =============================================================================
# 2. MOTOR DE CÁLCULO (BOX MODEL / EDO)
# =============================================================================
def simular_vazamento_indoor(vol_sala, ach, massa_derramada_kg, area_poca, volat_fator):
    """
    Simula a concentração (Balanço de Massa: Entra Gás - Sai Gás).
    """
    massa_total_g = massa_derramada_kg * 1000.0
    
    # Estimativa de Taxa de Evaporação (Modelo Kawamura simplificado)
    # 5.0 g/s/m2 é a taxa base para produtos muito voláteis (fator 1.0)
    taxa_evap_base = 5.0 * volat_fator 
    
    # Vazão do exaustor (m3/s)
    q_vent = (ach * vol_sala) / 3600.0
    
    # Configuração do tempo
    dt = 1.0       
    t_max = 1800   # 30 minutos
    tempo = np.arange(0, t_max, dt)
    
    concentracao_hist = [] 
    conc_atual = 0.0
    massa_restante = massa_total_g
    
    # Loop Euler
    for t in tempo:
        # 1. Geração (Evaporação)
        if massa_restante > 0:
            geracao = taxa_evap_base * area_poca * dt
            if geracao > massa_restante: geracao = massa_restante
            massa_restante -= geracao
        else:
            geracao = 0.0
            
        # 2. Remoção (Ventilação)
        remocao = conc_atual * q_vent * dt
        
        # 3. Novo Estado
        conc_atual += (geracao - remocao) / vol_sala
        if conc_atual < 0: conc_atual = 0
        concentracao_hist.append(conc_atual)
        
    return tempo, np.array(concentracao_hist)

def converter_limites(mw, idlh_ppm, lel_perc):
    """
    Converte os dados da FISPQ (PPM e %) para g/m³ para podermos plotar no gráfico.
    """
    # Conversão IDLH (ppm -> g/m3)
    limite_idlh_gm3 = (idlh_ppm * mw) / 24450.0 * 1000 if idlh_ppm > 0 else None
    
    # Conversão LEL (% -> g/m3) -> 1% = 10,000 ppm
    limite_lel_gm3 = (lel_perc * 10000.0 * mw) / 24450.0 * 1000 if lel_perc > 0 else None
    
    return limite_idlh_gm3, limite_lel_gm3

# =============================================================================
# 3. INTERFACE VISUAL (FRONT-END)
# =============================================================================
def renderizar():
    st.markdown("### 🏚️ Químico Indoor (Box Model)")
    st.markdown("Modelagem de saturação de ambientes confinados (Salas/Laboratórios).")
    st.markdown("---")

    # --- O CABEÇALHO MEGA EXPLICATIVO ---
    with st.expander("📖 GUIA DE OPERAÇÃO: Ventilação, Riscos e FISPQ (Leia com Atenção)", expanded=True):
        st.markdown("""
        #### 1. O Conceito: A Corrida contra o Tempo
        Imagine uma banheira enchendo (o vazamento evaporando) com o ralo aberto (o exaustor puxando ar).
        * Se o ralo for pequeno (**Ventilação Ruim**), a banheira transborda (**Explosão/Morte**).
        * Se o ralo for grande (**Ventilação Boa**), o nível se mantém baixo e seguro.

        #### 2. Entendendo os Parâmetros Críticos
        * **ACH (Trocas de Ar por Hora):** É a força do seu exaustor.
            * ❄️ **0.5 ACH:** Sala fechada, ar condicionado split (Péssimo). O gás fica preso.
            * 🏢 **2.0 a 4.0 ACH:** Escritório com janelas abertas ou ar central comum.
            * 🧪 **10.0 a 20.0 ACH:** Laboratório Químico com exaustão profissional ligada (Padrão Ouro).
        * 🔴 **LEL (Limite de Explosão):** Se a curva tocar a linha vermelha, a sala vira uma bomba. Acender a luz detona tudo.
        * 🟠 **IDLH (Risco de Morte):** Limite de toxidez aguda. Acima disso, só entra com máscara de oxigênio (ERA).

        #### 3. Como usar dados da FISPQ (Modo Personalizado)
        Se o seu produto não está na lista, selecione **"➕ Outro (Personalizado)"** e busque na ficha técnica:
        * **Peso Molecular (MW):** Seção 9 (Propriedades Físicas).
        * **LEL (%):** Seção 9. Se for "Não Aplicável", coloque 0.
        * **IDLH (ppm):** Seção 11 (Toxicológica).
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Geometria e Ventilação")
        vol = st.number_input("Volume da Sala (m³)", value=40.0, min_value=1.0, help="Largura x Comprimento x Altura. Ex: 4x4x2.5 = 40m³.")
        ach = st.number_input("Ventilação (ACH)", value=2.0, min_value=0.0, step=0.5, help="Quantas vezes o ar é renovado por hora? (0.5=Ruim, 10=Ótimo).")
        
        # Seleção Híbrida (Lista ou Manual)
        lista_opcoes = list(SUBSTANCIAS_INDOOR.keys()) + ["➕ Outro (Personalizado)"]
        selecao = st.selectbox("Substância Vazada", lista_opcoes, help="Escolha da lista ou use dados da FISPQ.")

    with col2:
        st.subheader("💧 Detalhes do Vazamento")
        massa_kg = st.number_input("Massa Derramada (kg ou Litros)", value=1.0, min_value=0.1, step=0.1, help="Quantidade total que caiu no chão.")
        area = st.number_input("Área da Poça (m²)", value=2.0, min_value=0.1, step=0.5, help="Poça espalhada (área grande) evapora muito mais rápido que poça contida.")

    # --- LÓGICA DE INPUT MANUAL VS AUTOMÁTICO ---
    if selecao == "➕ Outro (Personalizado)":
        st.info("📝 **Modo Manual:** Insira os dados da Seção 9 e 11 da FISPQ do produto.")
        c_a, c_b, c_c, c_d = st.columns(4)
        mw_in = c_a.number_input("Peso Molecular (g/mol)", value=100.0, min_value=1.0)
        lel_in = c_b.number_input("LEL (%)", value=0.0, step=0.1, help="Coloque 0 se não explode.")
        idlh_in = c_c.number_input("IDLH (ppm)", value=500.0, step=50.0)
        volat_in = c_d.slider("Volatilidade (Fator)", 0.1, 1.0, 0.5, help="1.0=Muito Volátil (Éter/Acetona); 0.1=Pouco Volátil (Óleo/Diesel).")
        
        # Consolida dados manuais
        dados_ativos = {"mw": mw_in, "lel": lel_in, "idlh": idlh_in, "volatilidade": volat_in, "nome": "Substância Personalizada"}
    else:
        # Busca dados do dicionário
        d = SUBSTANCIAS_INDOOR[selecao]
        dados_ativos = {"mw": d['mw'], "lel": d['lel'] if d['lel'] else 0, "idlh": d['idlh'], "volatilidade": d['volatilidade'], "nome": selecao}
        st.caption(f"ℹ️ **Info:** {d['desc']} (MW: {d['mw']}, LEL: {d['lel']}%)")

    # Botão de Execução
    if 'indoor_calc' not in st.session_state: st.session_state['indoor_calc'] = False
    if st.button("📉 Simular Evolução da Atmosfera", type="primary", use_container_width=True):
        st.session_state['indoor_calc'] = True

    # =========================================================================
    # 4. RESULTADOS E DIAGNÓSTICO
    # =========================================================================
    if st.session_state['indoor_calc']:
        # Extrair dados para cálculo
        fator_volat = dados_ativos['volatilidade']
        mw_val = dados_ativos['mw']
        lel_val = dados_ativos['lel']
        idlh_val = dados_ativos['idlh']
        nome_display = dados_ativos['nome']

        # Rodar Simulação
        t_seg, conc_gm3 = simular_vazamento_indoor(vol, ach, massa_kg, area, fator_volat)
        lim_idlh, lim_lel = converter_limites(mw_val, idlh_val, lel_val)
        
        t_min = t_seg / 60.0
        max_conc = np.max(conc_gm3)

        # --- A. DIAGNÓSTICO (Texto vem ANTES do gráfico) ---
        st.markdown("#### 📋 Diagnóstico Operacional")
        
        cruzou_lel = lim_lel and max_conc > lim_lel
        cruzou_idlh = lim_idlh and max_conc > lim_idlh
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**Risco de Explosão:**")
            if cruzou_lel:
                tempo = t_min[np.argmax(conc_gm3 > lim_lel)]
                st.error(f"🚨 **CRÍTICO: EXPLOSIVO**\nOcorre em **{tempo:.1f} min**.\nVentilação INSUFICIENTE.")
            elif lim_lel:
                st.success("✅ **Seguro (Não atinge LEL)**")
            else:
                st.info("Substância não explosiva.")

        with col_d2:
            st.markdown("**Risco Toxicológico:**")
            if cruzou_idlh:
                tempo = t_min[np.argmax(conc_gm3 > lim_idlh)]
                st.error(f"💀 **LETAL (IDLH)**\nAmbiente mortal em **{tempo:.1f} min**.\nEntrada proibida sem ERA.")
            elif lim_idlh and max_conc > (lim_idlh*0.1):
                st.warning("⚠️ **Alerta (Tóxico)**\nUso obrigatório de máscara.")
            else:
                st.success("✅ **Respirável**")

        # --- B. GRÁFICO ---
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(t_min, conc_gm3, color='#000080', linewidth=3, label="Concentração na Sala")
        ax.fill_between(t_min, conc_gm3, alpha=0.15, color='#000080')
        
        # Linha LEL
        if lim_lel:
            ax.axhline(lim_lel, color='red', linestyle='--', linewidth=2)
            ax.text(0.5, lim_lel*1.02, f' Limite de Explosão (LEL): {lim_lel:.1f} g/m³', color='red', fontweight='bold')
            
        # Linha IDLH
        if lim_idlh:
            ax.axhline(lim_idlh, color='orange', linestyle='--', linewidth=2)
            offset = 1.02 if not lim_lel or abs(lim_lel - lim_idlh) > (lim_lel*0.1) else 0.95
            ax.text(0.5, lim_idlh*offset, f' Perigo à Vida (IDLH): {lim_idlh:.1f} g/m³', color='#CC7000', fontweight='bold')

        ax.set_xlabel('Tempo (minutos)'); ax.set_ylabel('Concentração (g/m³)')
        ax.set_title(f'Curva de Saturação: {nome_display} ({vol}m³, {ach} ACH)')
        ax.grid(True, linestyle='--', alpha=0.4); ax.legend()
        
        # Ajuste de escala Y para não cortar os textos
        max_y = max(max_conc, lim_lel if lim_lel else 0, lim_idlh if lim_idlh else 0)
        ax.set_ylim(0, max_y * 1.25)

        st.pyplot(fig)