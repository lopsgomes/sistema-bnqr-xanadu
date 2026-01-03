import streamlit as st
from modulos import (
    quimico_outdoor,
    radiologico,
    quimico_indoor,
    pool_fire,
    explosao,
    biologico,
    nuclear_rdd,
    blindagem,
    bleve,
    jet_fire,
    vce,
    agua,
    decon,
    triage,
    drone,
    toxicidade_avancada,
    flash_fire,
    gases_densos,
    bio_avancado,
    rad_tatica,
    fluxo_humano,
    colapso_hospitalar
)

# Configuração da página
st.set_page_config(
    page_title="Sistema Unificado de Simulação BNQR - Tecnologia Nacional para Gestão de Crises",
    page_icon="🇧🇷",
    layout="wide"
)

# Menu lateral
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
    <div style="width: 40px; height: 25px; background: linear-gradient(to bottom, #009739 0%, #009739 50%, #FEDD00 50%, #FEDD00 100%);
                border: 1px solid #000; border-radius: 3px; flex-shrink: 0;"></div>
    <h1 style="margin: 0; font-size: 1.5rem;">Sistema BNQR</h1>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Inicializar módulo selecionado na sessão
if 'modulo_selecionado' not in st.session_state:
    st.session_state.modulo_selecionado = None

# 1. ☢️ AMBIENTE RADIOLÓGICO E NUCLEAR
with st.sidebar.expander("☢️ AMBIENTE RADIOLÓGICO E NUCLEAR", expanded=False):
    if st.button("Irradiação Direta (Ponto Fixo)", key="radiologico", use_container_width=True):
        st.session_state.modulo_selecionado = ("Irradiação Direta (Ponto Fixo)", radiologico)
    if st.button("Blindagem Radiológica (HVL)", key="blindagem", use_container_width=True):
        st.session_state.modulo_selecionado = ("Blindagem Radiológica (HVL)", blindagem)
    if st.button("Dose Tática (Fallout)", key="rad_tatica", use_container_width=True):
        st.session_state.modulo_selecionado = ("Dose Tática (Fallout)", rad_tatica)
    if st.button("RDD - Bomba Suja", key="nuclear_rdd", use_container_width=True):
        st.session_state.modulo_selecionado = ("RDD - Bomba Suja", nuclear_rdd)

# 2. 🧪 DINÂMICA QUÍMICA E GASES
with st.sidebar.expander("🧪 DINÂMICA QUÍMICA E GASES", expanded=False):
    if st.button("Dispersão Atmosférica (Gaussian Plume)", key="quimico_outdoor", use_container_width=True):
        st.session_state.modulo_selecionado = ("Dispersão Atmosférica (Gaussian Plume)", quimico_outdoor)
    if st.button("Contaminação Indoor (Box Model)", key="quimico_indoor", use_container_width=True):
        st.session_state.modulo_selecionado = ("Contaminação Indoor (Box Model)", quimico_indoor)
    if st.button("Gases Densos (Dense Gas)", key="gases_densos", use_container_width=True):
        st.session_state.modulo_selecionado = ("Gases Densos (Dense Gas)", gases_densos)
    if st.button("Toxicidade Avançada (IDLH/APF)", key="toxicidade_avancada", use_container_width=True):
        st.session_state.modulo_selecionado = ("Toxicidade Avançada (IDLH/APF)", toxicidade_avancada)

# 3. 🔥 INCÊNDIOS E EXPLOSÕES
with st.sidebar.expander("🔥 INCÊNDIOS E EXPLOSÕES", expanded=False):
    if st.button("Pool Fire", key="pool_fire", use_container_width=True):
        st.session_state.modulo_selecionado = ("Pool Fire", pool_fire)
    if st.button("Jet Fire", key="jet_fire", use_container_width=True):
        st.session_state.modulo_selecionado = ("Jet Fire", jet_fire)
    if st.button("Flash Fire", key="flash_fire", use_container_width=True):
        st.session_state.modulo_selecionado = ("Flash Fire", flash_fire)
    if st.button("VCE (Vapor Cloud Explosion)", key="vce", use_container_width=True):
        st.session_state.modulo_selecionado = ("VCE (Vapor Cloud Explosion)", vce)
    if st.button("Explosão (Blast Wave)", key="explosao", use_container_width=True):
        st.session_state.modulo_selecionado = ("Explosão (Blast Wave)", explosao)
    if st.button("BLEVE (Boiling Liquid Expanding Vapor Explosion)", key="bleve", use_container_width=True):
        st.session_state.modulo_selecionado = ("BLEVE (Boiling Liquid Expanding Vapor Explosion)", bleve)

# 4. ☣️ AMEAÇAS BIOLÓGICAS E EPIDEMIAS
with st.sidebar.expander("☣️ AMEAÇAS BIOLÓGICAS E EPIDEMIAS", expanded=False):
    if st.button("Epidemiologia (SIR/SEIR-A)", key="biologico", use_container_width=True):
        st.session_state.modulo_selecionado = ("Epidemiologia (SIR/SEIR-A)", biologico)
    if st.button("Persistência de Patógenos (Fômites)", key="bio_avancado", use_container_width=True):
        st.session_state.modulo_selecionado = ("Persistência de Patógenos (Fômites)", bio_avancado)
    if st.button("Segurança Hídrica (Water Security)", key="agua", use_container_width=True):
        st.session_state.modulo_selecionado = ("Segurança Hídrica (Water Security)", agua)

# 5. 🚑 INTELIGÊNCIA EM OPERAÇÕES E SAÚDE
with st.sidebar.expander("🚑 INTELIGÊNCIA EM OPERAÇÕES E SAÚDE", expanded=False):
    if st.button("START Triage", key="triage", use_container_width=True):
        st.session_state.modulo_selecionado = ("START Triage", triage)
    if st.button("DECON (Descontaminação)", key="decon", use_container_width=True):
        st.session_state.modulo_selecionado = ("DECON (Descontaminação)", decon)
    if st.button("Evacuação (Roteamento Ótimo)", key="fluxo_humano", use_container_width=True):
        st.session_state.modulo_selecionado = ("Evacuação (Roteamento Ótimo)", fluxo_humano)
    if st.button("Colapso Hospitalar (M/M/s)", key="colapso_hospitalar", use_container_width=True):
        st.session_state.modulo_selecionado = ("Colapso Hospitalar (M/M/s)", colapso_hospitalar)

# 6. 🛰️ COMANDO E TECNOLOGIA
with st.sidebar.expander("🛰️ COMANDO E TECNOLOGIA", expanded=False):
    if st.button("Reconhecimento Aéreo (UAV Survey)", key="drone", use_container_width=True):
        st.session_state.modulo_selecionado = ("Reconhecimento Aéreo (UAV Survey)", drone)

st.sidebar.markdown("---")
st.sidebar.markdown("**Desenvolvido por Xanadu P&D**")

# Renderizar o módulo selecionado
if st.session_state.modulo_selecionado:
    nome_modulo, modulo = st.session_state.modulo_selecionado
    modulo.renderizar()
else:
    # Página inicial institucional
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        <div style="width: 60px; height: 40px; background: linear-gradient(to bottom, #009739 0%, #009739 50%, #FEDD00 50%, #FEDD00 100%);
                    border: 2px solid #000; border-radius: 4px; flex-shrink: 0;"></div>
        <h1 style="margin: 0; font-size: 2.5rem;">Sistema Unificado de Simulação BNQR: Tecnologia Nacional para Gestão de Crises</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Bem-vindo à plataforma que redefine a resposta a emergências no Brasil. Desenvolvemos uma solução robusta e multidisciplinar, 
    projetada para oferecer soberania tecnológica e precisão científica em cenários de alta complexidade.
    """)
    
    st.caption("Versão beta. Em constante desenvolvimento")
    
    st.markdown("---")
    
    st.markdown("### O Poder dos Grandes Softwares em uma Única Interface")
    
    st.markdown("""
    Nossa plataforma integra funcionalidades que, globalmente, são fracionadas em softwares de alto custo ou acesso restrito. 
    Ao utilizar este sistema, você tem ao seu alcance capacidades equivalentes a padrões internacionais:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Dispersão e Toxicidade:** Modelagens de plumas tóxicas e gases densos comparáveis ao ALOHA (EPA/NOAA) e PHAST (DNV).
        
        **Termodinâmica e Explosões:** Cálculos de BLEVE, Jet Fire e VCE seguindo as rigorosas diretrizes do TNO Yellow Book.
        
        **Defesa Nuclear:** Estimativas de dose e blindagem alinhadas ao HotSpot e MicroShield.
        """)
    
    with col2:
        st.markdown("""
        **Epidemiologia e Bio:** Modelagem SEIR avançada e contaminação de redes de água (padrão EPANET).
        
        **Logística e Fluxo:** Algoritmos de evacuação dinâmica e teoria das filas para gestão hospitalar (padrão Pathfinder e WebEOC).
        """)
    
    st.markdown("---")
    
    st.markdown("### Institucional e Acesso")
    
    st.markdown("""
    Este projeto nasceu da necessidade de fornecer ferramentas de elite para quem está na linha de frente. Por isso, garantimos que o sistema é:
    """)
    
    st.markdown("""
    - **Totalmente Nacional:** Desenvolvido no Brasil, com interface em português e adaptado à nossa realidade geográfica e climática.
    
    - **Soberania Tecnológica:** Uma ferramenta de Estado para o cidadão, ideal para agentes de Defesa Civil, Militares, Especialistas em Produtos Perigosos e Universidades.
    
    - **Acesso Universal:** Disponível para qualquer brasileiro que necessite de suporte técnico para salvar vidas e proteger o meio ambiente.
    """)
    
    st.markdown("---")
    
    st.markdown("### Construção Colaborativa: Rede Nacional de Resposta a Emergências")
    
    st.markdown("""
    A Xanadu P&D lidera a estruturação de uma proposta estratégica para a Chamada Pública MCTI/FINEP Centros Temáticos 2025. 
    Estamos unindo Universidades, Corpos de Bombeiros e Defesa Civil para criar uma solução de soberania em defesa QBRN.
    
    Você bombeiro (militar ou civil), engenheiro ambiental, químico ou especialista em HazMat é peça fundamental. 
    Sua experiência de campo pode moldar essa tecnologia. Para contribuir tecnicamente ou institucionalmente, entre em contato: 
    **contato@xanadupesquisa.com.br**
    """)
    
    st.markdown("---")
    
    st.markdown("### Compromisso com o Brasil e Propriedade Intelectual")
    
    st.markdown("""
    **Este software foi desenvolvido e é propriedade intelectual da Xanadu Pesquisa e Desenvolvimento.**
    
    Em um gesto de compromisso com a segurança nacional e o fortalecimento das instituições brasileiras, a Xanadu se compromete 
    formalmente a manter este serviço **gratuito para sempre** para todos os seus usuários. Acreditamos que o acesso a ferramentas 
    de proteção à vida não deve ser limitado por barreiras financeiras.
    """)
    
    st.markdown("---")
    
    st.warning("""
    **Aviso de Segurança:** Este sistema é uma ferramenta de apoio à decisão. Seus resultados devem ser cruzados com medições de campo 
    e protocolos oficiais das autoridades competentes.
    """)
    
    st.markdown("---")
    
    st.markdown("### Selecione um módulo no menu lateral para começar")
