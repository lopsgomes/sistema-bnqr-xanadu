import streamlit as st
from dotenv import load_dotenv
import os
import pathlib

# Carregar variáveis de ambiente do arquivo .env antes de importar módulos
# Especifica o caminho explícito do arquivo .env
env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
# Fallback: tenta carregar do diretório atual
load_dotenv()

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
    colapso_hospitalar,
    agente_quimico
)

# Configuração da página
st.set_page_config(
    page_title="Sistema Unificado de Simulação BNQR - Tecnologia Nacional para Gestão de Crises",
    page_icon="🇧🇷",
    layout="wide"
)

# Menu lateral - Logo BNQR (Dark Mode)
st.sidebar.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

.bnqr-logo-container {
    display: flex;
    align-items: center;
    background-color: #1a1a1a;
    padding: 15px 25px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border-left: 4px solid #3385ff;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
}

.bnqr-icon-unified {
    width: 40px;
    height: 40px;
    position: relative;
    margin-right: 15px;
}

.node {
    width: 10px;
    height: 10px;
    background-color: #3385ff;
    position: absolute;
    border-radius: 2px;
    box-shadow: 0 0 5px rgba(51, 133, 255, 0.3);
}
.n1 { top: 0; left: 0; }
.n2 { top: 0; right: 0; background-color: #66a3ff; }
.n3 { bottom: 0; left: 0; background-color: #005ce6; }
.n4 { bottom: 0; right: 0; }

.bnqr-icon-unified::before, .bnqr-icon-unified::after {
    content: '';
    position: absolute;
    background-color: #444444;
    z-index: 0;
    opacity: 0.7;
}
.bnqr-icon-unified::before {
    height: 2px;
    width: 100%;
    top: 50%;
    transform: translateY(-50%);
}
.bnqr-icon-unified::after {
    width: 2px;
    height: 100%;
    left: 50%;
    transform: translateX(-50%);
}

.bnqr-text-block {
    display: flex;
    flex-direction: column;
}

.bnqr-acronym-b {
    font-size: 1.8rem;
    font-weight: 900;
    color: #e0e0e0;
    line-height: 1;
    letter-spacing: -0.02em;
}

.bnqr-system-name-b {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: #a0a0a0;
    font-weight: 700;
    letter-spacing: 0.05em;
    margin-top: 4px;
}

.highlight-sim {
    color: #3385ff;
}
</style>
<div class="bnqr-logo-container">
    <div class="bnqr-icon-unified">
        <div class="node n1"></div>
        <div class="node n2"></div>
        <div class="node n3"></div>
        <div class="node n4"></div>
    </div>
    <div class="bnqr-text-block">
        <span class="bnqr-acronym-b">BNQR</span>
        <span class="bnqr-system-name-b">Sistema Unificado de <span class="highlight-sim">Simulação</span></span>
    </div>
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
    if st.button("Compatibilidade Química (Foto e/ou Excel)", key="agente_quimico", use_container_width=True):
        st.session_state.modulo_selecionado = ("Compatibilidade Química (Foto e/ou Excel)", agente_quimico)

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
    # Página inicial institucional - Banner BNQR
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');

    .bnqr-banner-container {
        position: relative;
        width: 100%;
        max-width: 1000px;
        height: 280px;
        background: linear-gradient(135deg, #050a1f, #0f1f15);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2a2a6a;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 60px rgba(0, 255, 100, 0.1);
        display: flex;
        align-items: center;
        padding: 0 40px;
        margin-bottom: 30px;
        font-family: 'Rajdhani', sans-serif;
    }

    .simulation-grid-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(0, 255, 150, 0.07) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 150, 0.07) 1px, transparent 1px);
        background-size: 30px 30px;
        mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
        z-index: 1;
        opacity: 0.6;
    }

    .data-pulse {
        position: absolute;
        left: 15%;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(150, 255, 0, 0.2) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        z-index: 2;
        animation: pulse 4s infinite ease-in-out;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.2); opacity: 0.8; }
    }

    .bnqr-content {
        position: relative;
        z-index: 3;
        text-transform: uppercase;
        padding-left: 160px;
    }

    .bnqr-subtitle {
        font-size: 1.1rem;
        color: #a0c0ff;
        letter-spacing: 0.2em;
        font-weight: 600;
        margin-bottom: 0px;
        display: block;
    }

    .bnqr-title-wrapper {
        display: flex;
        align-items: baseline;
    }

    .bnqr-main-title {
        font-size: 2.5rem;
        color: #ffffff;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .bnqr-acronym-highlight {
        font-size: 4rem;
        font-weight: 700;
        margin-left: 15px;
        background: linear-gradient(90deg, #00ff6a, #f2ff00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(136, 255, 0, 0.5));
        position: relative;
        top: 4px;
    }

    .bnqr-full-meaning {
        display: block;
        font-size: 0.95rem;
        color: #d0ffd0;
        letter-spacing: 0.15em;
        font-weight: 600;
        margin-top: 8px;
        opacity: 0.9;
    }

    .geo-icon {
        position: absolute;
        left: 50px;
        width: 80px;
        height: 80px;
        border: 2px solid rgba(0, 255, 150, 0.5);
        transform: rotate(45deg);
        z-index: 3;
    }
    .geo-icon::after {
         content: '';
         position: absolute;
         top: 15px; left: 15px; right: 15px; bottom: 15px;
         border: 2px solid rgba(229, 255, 0, 0.5);
    }
    </style>
    <div class="bnqr-banner-container">
        <div class="simulation-grid-bg"></div>
        <div class="data-pulse"></div>
        <div class="geo-icon"></div>
        <div class="bnqr-content">
            <span class="bnqr-subtitle">Sistema Unificado de</span>
            <div class="bnqr-title-wrapper">
                <h1 class="bnqr-main-title">Simulação</h1>
                <span class="bnqr-acronym-highlight">BNQR</span>
            </div>
            <span class="bnqr-full-meaning">Defesa Nuclear, Biológica, Química e Radiológica</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Bem-vindo à plataforma que busca redefinir a resposta a emergências no Brasil. Desenvolvemos uma solução robusta e multidisciplinar, 
    projetada para oferecer soberania tecnológica e precisão científica em cenários de alta complexidade.
    
    Acreditamos que o Brasil precisa fundar linhas de pesquisa e desenvolvimento na área BNQR. Hoje, existem poucos grupos de PD&I dedicados 
    ao tema nas ICTs e nas forças de segurança estaduais e federais. Esta plataforma visa oferecer gratuitamente o estado da arte em simulações 
    matemáticas de BNQR e fomentar a integração desses grupos dispersos pelo Brasil, visando construir uma Rede Nacional de Resposta a Emergências. 
    Continue lendo para mais informações.
    """)
    
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
        
        **Compatibilidade Química:** Análise inteligente de inventários químicos e matrizes de compatibilidade usando IA, 
        comparável ao CAMEO (EPA) e WISER (NIOSH).
        """)
    
    with col2:
        st.markdown("""
        **Epidemiologia e Bio:** Modelagem SEIR avançada e contaminação de redes de água (padrão EPANET).
        
        **Logística e Fluxo:** Algoritmos de evacuação dinâmica e teoria das filas para gestão hospitalar (padrão Pathfinder e WebEOC).
        """)
    
    st.markdown("""
    **Como usar:** No menu lateral esquerdo, você encontrará os módulos organizados por categorias (Radiológico, Químico, Incêndios, 
    Biológico, Operações e Tecnologia). Clique nos botões dentro de cada categoria para acessar as ferramentas de simulação. 
    Cada módulo possui parâmetros configuráveis e resultados detalhados com visualizações interativas.
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
    A Xanadu P&D propõe a estruturação de uma proposta estratégica para a Chamada Pública MCTI/FINEP Centros Temáticos 2025. 
    Estamos unindo Universidades, Corpos de Bombeiros e Defesa Civil para criar uma solução de soberania em defesa QBRN através 
    do uso de tecnologias e pela implementação de Brigadas de Produtos Perigosos em todas as universidades públicas do país.
    
    Você, bombeiro (militar ou civil), engenheiro ambiental, militar, biólogo, físico, químico ou especialista em HazMat é peça fundamental. 
    Sua experiência de campo pode moldar essa tecnologia. Para contribuir tecnicamente ou institucionalmente, entre em contato através do 
    e-mail **contato@xanadupesquisa.com.br** ou acessando **www.xanadupesquisa.com.br**
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
