import streamlit as st
import pandas as pd
import numpy as np
import json
import base64
import io
import datetime
import time
from typing import TypedDict, List, Dict, Optional, Literal, Tuple
import google.genai as genai
from PIL import Image
import os
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    RetryError,
    RetryCallState
)

# =============================================================================
# 1. CONFIGURAÇÃO E TIPAGEM (PREPARAÇÃO DO TERRENO)
# =============================================================================

# Carregar variáveis de ambiente do arquivo .env
# Tenta carregar do diretório do módulo e do diretório pai
import pathlib
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
# Também tenta carregar do diretório atual (fallback)
load_dotenv()

# Configuração da API Google Gemini
# Modelo estável para produção (baseado no diagnóstico: gemini-2.5-flash é o mais recente estável)
MODEL_NAME = "gemini-2.5-flash"  # Modelo mais recente e estável disponível

# System instruction para o modelo
SYSTEM_INSTRUCTION = """Você é um Especialista em Segurança Química com conhecimento profundo de:
- Sistema GHS (Globally Harmonized System)
- Incompatibilidades químicas (EPA, NFPA, UN Purple Book)
- Regras de segregação de produtos perigosos
- Nomenclatura química em português brasileiro

Sempre responda em português e use nomes de compostos químicos em português."""

def obter_api_key():
    """Obtém a API key da variável de ambiente ou do Streamlit secrets."""
    # Tenta ler de ambos os lugares: .env (via os.getenv) ou Streamlit secrets
    api_key = None
    
    # Primeiro tenta do arquivo .env (via os.getenv após load_dotenv)
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Se não encontrar, tenta recarregar o .env explicitamente
    if not api_key:
        import pathlib
        env_path = pathlib.Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path, override=True)
        api_key = os.getenv("GOOGLE_API_KEY")
    
    # Se ainda não encontrar, tenta do Streamlit secrets (para produção)
    # Usa a sintaxe sugerida: os.getenv() or st.secrets.get()
    if not api_key:
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY", None)
        except:
            pass
    
    # Fallback final: tenta ler diretamente com a sintaxe combinada sugerida
    if not api_key:
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
        except:
            pass
    
    return api_key

def inicializar_cliente():
    """Inicializa o cliente Gemini."""
    api_key = obter_api_key()
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada. Configure a variável de ambiente.")
    
    # Criar cliente com API key
    client = genai.Client(api_key=api_key)
    
    return client

# Tipagem para estruturas de dados esperadas da IA
class ItemInventario(TypedDict):
    nome_quimico: str
    cas: Optional[str]
    quantidade: Optional[str]
    unidade: Optional[str]
    pureza: Optional[str]
    observacoes: Optional[str]

class Incompatibilidade(TypedDict):
    composto_a: str
    composto_b: str
    tipo_risco: str  # "reacao_violenta", "gas_toxico", "explosao", "incendio"
    severidade: str  # "alta", "media", "baixa"
    descricao: str

class RegraArmazenamento(TypedDict):
    composto: str
    classe_perigo: str
    segregação_obrigatoria: List[str]
    segregação_recomendada: List[str]
    condicoes_especiais: Optional[str]

class RespostaIA(TypedDict):
    inventario_normalizado: List[ItemInventario]
    matriz_risco: List[Incompatibilidade]
    regras_armazenamento: List[RegraArmazenamento]
    avisos_criticos: List[str]
    classificacao_ghs: Dict[str, List[str]]  # nome_quimico -> lista de códigos GHS

# =============================================================================
# 2. PIPELINE DE INGESTÃO FLEXÍVEL (CAMINHO A: EXCEL/XLSX)
# =============================================================================

def preparar_excel_para_ia(arquivo_excel) -> str:
    """
    Lê um arquivo Excel e converte TODO o conteúdo em uma única representação textual.
    
    OTIMIZAÇÃO: Envia TODO o Excel de uma vez (ou chunks grandes) em uma única chamada à API,
    aproveitando a janela de contexto grande do Gemini Flash (até 1M tokens). Isso evita
    múltiplas chamadas que explodem o rate limit (RPM).
    
    FILOSOFIA: Não tentamos adivinhar colunas. Convertemos tudo em texto bruto
    e delegamos a interpretação para a IA em uma única requisição.
    
    Args:
        arquivo_excel: Arquivo Excel carregado via Streamlit
        
    Returns:
        String em formato Markdown/CSV representando TODO o conteúdo do Excel
    """
    try:
        # Tentar ler o Excel (pode ter múltiplas abas)
        xls = pd.ExcelFile(arquivo_excel)
        
        # OTIMIZAÇÃO: Aumentar limite para aproveitar contexto grande do Gemini Flash
        # Gemini 1.5 Flash suporta até 1M tokens, então podemos enviar mais dados
        linhas_limite = 500  # Aumentado de 100 para 500 linhas por aba
        
        texto_completo = []
        texto_completo.append(f"# Arquivo Excel: {arquivo_excel.name}\n")
        texto_completo.append(f"Total de abas: {len(xls.sheet_names)}\n\n")
        
        # Processar TODAS as abas em uma única string
        for aba_nome in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=aba_nome, nrows=linhas_limite)
            texto_completo.append(f"## Aba: {aba_nome}\n")
            texto_completo.append(f"Linhas: {len(df)}, Colunas: {len(df.columns)}\n\n")
            
            # Converter DataFrame para texto (tenta markdown, se falhar usa CSV)
            # OTIMIZAÇÃO: Enviar tudo de uma vez, não linha por linha
            try:
                texto_completo.append(df.to_markdown(index=False))
            except:
                # Fallback: usar CSV se to_markdown falhar
                texto_completo.append(df.to_csv(index=False, sep='|'))
            texto_completo.append("\n\n")
        
        # Retorna TODO o conteúdo em uma única string para UMA única chamada à API
        return "\n".join(texto_completo)
    
    except Exception as e:
        raise ValueError(f"Erro ao processar Excel: {str(e)}")

# =============================================================================
# 3. PIPELINE DE INGESTÃO FLEXÍVEL (CAMINHO B: VISÃO COMPUTACIONAL)
# =============================================================================

def preparar_imagem_para_ia(imagem_upload) -> Image.Image:
    """
    Converte uma imagem para formato PIL.Image compatível com Gemini.
    
    Args:
        imagem_upload: Arquivo de imagem carregado via Streamlit
        
    Returns:
        Objeto PIL.Image
    """
    try:
        # Ler a imagem diretamente com PIL
        imagem = Image.open(imagem_upload)
        
        # Converter para RGB se necessário (Gemini requer RGB)
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')
        
        return imagem
    
    except Exception as e:
        raise ValueError(f"Erro ao processar imagem: {str(e)}")

# =============================================================================
# 4. TEMPLATE DE PROMPT PARA PROCESSAMENTO DE EXCEL
# =============================================================================

PROMPT_EXCEL = """Você é um especialista em segurança química e análise de inventários perigosos.

Analise o seguinte conteúdo de planilha Excel e extraia APENAS informações químicas relevantes.

INSTRUÇÕES CRÍTICAS:
1. IGNORE colunas financeiras, administrativas, códigos de barras, datas de compra, etc.
2. FOQUE em: nomes de compostos químicos, números CAS, quantidades, unidades, pureza.
3. Se encontrar múltiplas planilhas, processe todas.
4. Se houver ambiguidade (ex: "Água" pode ser H2O ou solvente), mantenha o nome original.
5. **IMPORTANTE: Use SEMPRE nomes em PORTUGUÊS para os compostos químicos no campo "nome_quimico".**
   Exemplos: "Ácido Clorídrico" (não "Hydrochloric Acid"), "Hidróxido de Sódio" (não "Sodium Hydroxide"),
   "Acetona" (não "Acetone"), "Peróxido de Hidrogênio" (não "Hydrogen Peroxide").

DADOS BRUTOS:
{conteudo_excel}

Retorne APENAS um JSON válido no seguinte formato (sem markdown, sem explicações):
{{
    "inventario_normalizado": [
        {{
            "nome_quimico": "Nome do composto EM PORTUGUÊS",
            "cas": "123-45-6" ou null,
            "quantidade": "100" ou null,
            "unidade": "kg" ou null,
            "pureza": "98%" ou null,
            "observacoes": "Qualquer informação relevante" ou null
        }}
    ]
}}
"""

# =============================================================================
# 5. TEMPLATE DE PROMPT PARA PROCESSAMENTO DE IMAGEM (OCR)
# =============================================================================

PROMPT_IMAGEM = """Você é um sistema de OCR especializado em rótulos químicos, fichas de segurança e etiquetas de produtos perigosos.

Analise a imagem fornecida e extraia:
1. Nome do composto químico
2. Número CAS (se visível)
3. Quantidade/concentração (se visível)
4. Símbolos de perigo GHS
5. Frases de risco (R-phrases ou H-statements)
6. Informações de armazenamento

**IMPORTANTE: Use SEMPRE nomes em PORTUGUÊS para os compostos químicos no campo "nome_quimico".**
Exemplos: "Ácido Clorídrico" (não "Hydrochloric Acid"), "Hidróxido de Sódio" (não "Sodium Hydroxide"),
"Acetona" (não "Acetone"), "Peróxido de Hidrogênio" (não "Hydrogen Peroxide").

Retorne APENAS um JSON válido no seguinte formato (sem markdown, sem explicações):
{{
    "inventario_normalizado": [
        {{
            "nome_quimico": "Nome identificado EM PORTUGUÊS",
            "cas": "123-45-6" ou null,
            "quantidade": "Valor extraído" ou null,
            "unidade": "kg/L/etc" ou null,
            "pureza": "Concentração" ou null,
            "observacoes": "Informações adicionais do rótulo" ou null
        }}
    ]
}}
"""

# =============================================================================
# 6. TEMPLATE DE PROMPT PARA ANÁLISE DE COMPATIBILIDADE
# =============================================================================

PROMPT_ANALISE = """Você é um especialista em segurança química com conhecimento profundo de:
- Sistema GHS (Globally Harmonized System)
- Incompatibilidades químicas (EPA, NFPA, UN Purple Book)
- Regras de segregação de produtos perigosos

Com base no inventário normalizado fornecido, realize uma análise completa de riscos.

INVENTÁRIO NORMALIZADO:
{inventario_json}

TAREFAS:
1. Identifique TODAS as incompatibilidades químicas entre os compostos listados.
2. Classifique cada composto segundo o GHS (códigos H, categorias de perigo).
3. Gere regras de armazenamento baseadas em segregação obrigatória e recomendada.
4. Identifique avisos críticos (ex: "Ácido nítrico + Acetona = risco de explosão").
5. **IMPORTANTE: Use SEMPRE nomes em PORTUGUÊS para todos os compostos químicos em TODOS os campos.**

Para cada par de compostos, classifique a compatibilidade:
- "compativel": Compostos podem ser armazenados juntos sem risco significativo (VERDE)
- "precaucao": Compostos podem ser armazenados juntos com precauções (AMARELO)
- "incompativel": Compostos NÃO podem ser armazenados juntos - risco alto (VERMELHO)

Retorne APENAS um JSON válido no seguinte formato (sem markdown, sem explicações):
{{
    "matriz_risco": [
        {{
            "composto_a": "Nome do composto 1 EM PORTUGUÊS",
            "composto_b": "Nome do composto 2 EM PORTUGUÊS",
            "tipo_risco": "reacao_violenta" | "gas_toxico" | "explosao" | "incendio",
            "severidade": "alta" | "media" | "baixa",
            "compatibilidade": "compativel" | "precaucao" | "incompativel",
            "descricao": "Descrição detalhada do risco"
        }}
    ],
    "regras_armazenamento": [
        {{
            "composto": "Nome do composto EM PORTUGUÊS",
            "classe_perigo": "Classe GHS (ex: 'Classe 3 - Líquidos Inflamáveis')",
            "segregação_obrigatoria": ["Lista de compostos que NÃO podem estar juntos"],
            "segregação_recomendada": ["Lista de compostos que devem ser separados"],
            "condicoes_especiais": "Temperatura, umidade, etc." ou null
        }}
    ],
    "avisos_criticos": [
        "Lista de avisos críticos de segurança"
    ],
    "classificacao_ghs": {{
        "Nome do Composto EM PORTUGUÊS": ["H225", "H301", "H314"]
    }}
}}
"""

# =============================================================================
# 7. NÚCLEO DE PROCESSAMENTO (CHAMADAS À API GOOGLE GEMINI)
# =============================================================================

# Função auxiliar para verificar se é erro de rate limit
def is_rate_limit_error(exception):
    """Verifica se o erro é relacionado a rate limit (429) ou resource exhausted."""
    error_str = str(exception).lower()
    return (
        "429" in error_str or
        "resource_exhausted" in error_str or
        "rate limit" in error_str or
        "quota" in error_str
    )

# Decorador de retry robusto para chamadas à API
# Retry apenas em erros de rate limit (429, resource_exhausted)
@retry(
    retry=lambda retry_state: is_rate_limit_error(retry_state.outcome.exception()) if retry_state.outcome.failed else False,
    wait=wait_random_exponential(min=5, max=60),  # Backoff exponencial: 5s, 10s, 20s, 40s, até 60s
    stop=stop_after_attempt(5),  # Máximo de 5 tentativas
    reraise=True
)
def chamar_api_gemini_com_retry(client, model_name, contents, config):
    """
    Wrapper para chamadas à API Gemini com retry automático.
    
    Implementa retry com backoff exponencial para erros de rate limit (429).
    O sistema "dorme" e tenta novamente automaticamente se o Google pedir para esperar.
    
    Args:
        client: Cliente Gemini inicializado
        model_name: Nome do modelo
        contents: Conteúdo a ser enviado (texto ou multimodal)
        config: Configuração da geração
        
    Returns:
        Resposta da API
        
    Raises:
        Exception: Se todas as tentativas falharem ou se não for erro de rate limit
    """
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config
        )
        return response
    except Exception as e:
        # Se for erro de rate limit, relança para o retry processar
        if is_rate_limit_error(e):
            raise  # Relança para o tenacity processar o retry com backoff
        else:
            # Para outros erros, relança imediatamente sem retry
            raise

def chamar_ia_excel(conteudo_texto: str) -> Dict:
    """
    Envia conteúdo de Excel para a IA processar.
    
    Args:
        conteudo_texto: Texto Markdown/CSV do Excel
        
    Returns:
        Dicionário com inventário normalizado
    """
    try:
        client = inicializar_cliente()
        
        prompt = PROMPT_EXCEL.format(conteudo_excel=conteudo_texto)
        
        # Configuração da geração
        config = {
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "system_instruction": SYSTEM_INSTRUCTION
        }
        
        # Gerar resposta usando o cliente com retry automático
        response = chamar_api_gemini_com_retry(
            client=client,
            model_name=MODEL_NAME,
            contents=prompt,
            config=config
        )
        
        # Extrair texto da resposta (já vem como JSON)
        resposta_texto = response.text
        
        # Validar e parsear JSON
        return validar_e_parsear_json(resposta_texto, "inventario_normalizado")
    
    except RetryError as e:
        raise ValueError(f"Erro após múltiplas tentativas na API Google Gemini (Excel). Último erro: {str(e.last_attempt.exception())}")
    except Exception as e:
        if is_rate_limit_error(e):
            raise ValueError(f"Rate limit da API Google Gemini excedido. Por favor, aguarde alguns minutos e tente novamente. Erro: {str(e)}")
        raise ValueError(f"Erro na chamada à API Google Gemini (Excel): {str(e)}")

def chamar_ia_imagem(imagem_pil: Image.Image) -> Dict:
    """
    Envia imagem para a IA processar via Vision API do Gemini.
    
    Args:
        imagem_pil: Objeto PIL.Image da imagem
        
    Returns:
        Dicionário com inventário normalizado
    """
    try:
        client = inicializar_cliente()
        
        # Converter PIL.Image para bytes
        buffer = io.BytesIO()
        imagem_pil.save(buffer, format='PNG')
        imagem_bytes = buffer.getvalue()
        
        # Configuração da geração
        config = {
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "system_instruction": SYSTEM_INSTRUCTION
        }
        
        # Conteúdo multimodal
        contents = [
            {"text": PROMPT_IMAGEM},
            {"inline_data": {"mime_type": "image/png", "data": imagem_bytes}}
        ]
        
        # Gerar resposta usando o cliente com retry automático
        response = chamar_api_gemini_com_retry(
            client=client,
            model_name=MODEL_NAME,
            contents=contents,
            config=config
        )
        
        # Extrair texto da resposta (já vem como JSON)
        resposta_texto = response.text
        
        # Validar e parsear JSON
        return validar_e_parsear_json(resposta_texto, "inventario_normalizado")
    
    except RetryError as e:
        raise ValueError(f"Erro após múltiplas tentativas na API Google Gemini (Imagem). Último erro: {str(e.last_attempt.exception())}")
    except Exception as e:
        if is_rate_limit_error(e):
            raise ValueError(f"Rate limit da API Google Gemini excedido. Por favor, aguarde alguns minutos e tente novamente. Erro: {str(e)}")
        raise ValueError(f"Erro na chamada à API Google Gemini (Imagem): {str(e)}")

def chamar_ia_analise(inventario_json: str) -> Dict:
    """
    Envia inventário normalizado para análise de compatibilidade.
    
    Args:
        inventario_json: JSON string com inventário normalizado
        
    Returns:
        Dicionário completo com matriz_risco, regras_armazenamento, etc.
    """
    try:
        client = inicializar_cliente()
        
        prompt = PROMPT_ANALISE.format(inventario_json=inventario_json)
        
        # Configuração da geração
        config = {
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "system_instruction": SYSTEM_INSTRUCTION
        }
        
        # Gerar resposta usando o cliente com retry automático
        response = chamar_api_gemini_com_retry(
            client=client,
            model_name=MODEL_NAME,
            contents=prompt,
            config=config
        )
        
        # Extrair texto da resposta (já vem como JSON)
        resposta_texto = response.text
        
        # Validar e parsear JSON completo
        return validar_e_parsear_json(resposta_texto, "matriz_risco")
    
    except RetryError as e:
        raise ValueError(f"Erro após múltiplas tentativas na API Google Gemini (Análise). Último erro: {str(e.last_attempt.exception())}")
    except Exception as e:
        if is_rate_limit_error(e):
            raise ValueError(f"Rate limit da API Google Gemini excedido. Por favor, aguarde alguns minutos e tente novamente. Erro: {str(e)}")
        raise ValueError(f"Erro na chamada à API Google Gemini (Análise): {str(e)}")

# =============================================================================
# 8. VALIDAÇÃO DE JSON (PROTEÇÃO CONTRA "ALUCINAÇÕES" DA IA)
# =============================================================================

def validar_e_parsear_json(resposta_texto: str, campo_obrigatorio: str) -> Dict:
    """
    Valida e parseia JSON retornado pela IA.
    
    FILOSOFIA: A IA pode "alucinar" e retornar texto fora do formato JSON.
    Esta função tenta extrair o JSON mesmo se houver texto adicional.
    
    Args:
        resposta_texto: Texto retornado pela IA
        campo_obrigatorio: Nome do campo que deve existir no JSON
        
    Returns:
        Dicionário Python parseado
        
    Raises:
        ValueError: Se não conseguir extrair JSON válido
    """
    # Tentar encontrar JSON no texto (pode estar entre ```json ... ``` ou direto)
    texto_limpo = resposta_texto.strip()
    
    # Remover markdown code blocks se existirem
    if "```json" in texto_limpo:
        inicio = texto_limpo.find("```json") + 7
        fim = texto_limpo.find("```", inicio)
        texto_limpo = texto_limpo[inicio:fim].strip()
    elif "```" in texto_limpo:
        inicio = texto_limpo.find("```") + 3
        fim = texto_limpo.find("```", inicio)
        texto_limpo = texto_limpo[inicio:fim].strip()
    
    # Tentar encontrar primeiro { e último }
    primeiro_abre = texto_limpo.find("{")
    ultimo_fecha = texto_limpo.rfind("}")
    
    if primeiro_abre == -1 or ultimo_fecha == -1:
        raise ValueError("Não foi possível encontrar JSON na resposta da IA.")
    
    json_extraido = texto_limpo[primeiro_abre:ultimo_fecha + 1]
    
    try:
        dados = json.loads(json_extraido)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao parsear JSON: {str(e)}\n\nTexto recebido: {json_extraido[:500]}")
    
    # Validar campo obrigatório
    if campo_obrigatorio not in dados:
        raise ValueError(f"Campo obrigatório '{campo_obrigatorio}' não encontrado no JSON retornado.")
    
    return dados

# =============================================================================
# 9. FUNÇÃO PARA GERAR EXCEL DE EXEMPLO
# =============================================================================

def gerar_excel_exemplo() -> bytes:
    """
    Gera um arquivo Excel de exemplo para download.
    
    NOTA: Este é apenas um exemplo. O sistema aceita QUALQUER formato de Excel
    graças à capacidade da IA de interpretar dados não estruturados.
    """
    dados_exemplo = {
        "Produto": [
            "Ácido Clorídrico (HCl)",
            "Hidróxido de Sódio",
            "Acetona",
            "Peróxido de Hidrogênio 30%",
            "Sulfeto de Hidrogênio"
        ],
        "CAS": [
            "7647-01-0",
            "1310-73-2",
            "67-64-1",
            "7722-84-1",
            "7783-06-4"
        ],
        "Qtd": [
            "50",
            "25",
            "100",
            "10",
            "5"
        ],
        "Unidade": [
            "L",
            "kg",
            "L",
            "L",
            "kg"
        ],
        "Pureza": [
            "37%",
            "98%",
            "99%",
            "30%",
            "99%"
        ],
        "Localização": [
            "Armazém A - Prateleira 3",
            "Armazém B - Prateleira 1",
            "Armazém A - Prateleira 5",
            "Geladeira Química",
            "Armazém B - Prateleira 2"
        ]
    }
    
    df = pd.DataFrame(dados_exemplo)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventário')
    
    buffer.seek(0)
    return buffer.getvalue()

# =============================================================================
# 9. FUNÇÕES AUXILIARES PARA TABELA DE COMPATIBILIDADE
# =============================================================================

def criar_matriz_compatibilidade(nomes_compostos: List[str], matriz_risco: List[Dict]) -> Dict[str, Dict[str, str]]:
    """
    Cria uma matriz de compatibilidade entre todos os pares de compostos.
    
    Args:
        nomes_compostos: Lista de nomes únicos de compostos
        matriz_risco: Lista de dicionários com informações de risco entre pares
        
    Returns:
        Dicionário aninhado: {composto_a: {composto_b: "compativel"|"precaucao"|"incompativel"}}
    """
    matriz = {}
    
    # Inicializar matriz com "compativel" (verde) para todos os pares
    for comp_a in nomes_compostos:
        matriz[comp_a] = {}
        for comp_b in nomes_compostos:
            if comp_a == comp_b:
                matriz[comp_a][comp_b] = "-"  # Mesmo composto
            else:
                matriz[comp_a][comp_b] = "compativel"  # Padrão: compatível
    
    # Preencher com dados da matriz_risco
    for risco in matriz_risco:
        comp_a = risco.get("composto_a", "")
        comp_b = risco.get("composto_b", "")
        compatibilidade = risco.get("compatibilidade", "incompativel")
        
        # Se não tiver campo compatibilidade, inferir da severidade
        if not compatibilidade or compatibilidade not in ["compativel", "precaucao", "incompativel"]:
            severidade = risco.get("severidade", "baixa")
            if severidade == "alta":
                compatibilidade = "incompativel"
            elif severidade == "media":
                compatibilidade = "precaucao"
            else:
                compatibilidade = "compativel"
        
        # Atualizar matriz (bidirecional)
        if comp_a in matriz and comp_b in matriz[comp_a]:
            matriz[comp_a][comp_b] = compatibilidade
        if comp_b in matriz and comp_a in matriz[comp_b]:
            matriz[comp_b][comp_a] = compatibilidade
    
    return matriz

def exibir_tabela_compatibilidade(matriz: Dict[str, Dict[str, str]], nomes_compostos: List[str], matriz_risco: List[Dict] = None):
    """
    Exibe uma tabela HTML colorida de compatibilidade entre compostos.
    Inspirada no formato CAMEO - matriz triangular com nomes completos visíveis.
    
    Args:
        matriz: Matriz de compatibilidade criada por criar_matriz_compatibilidade
        nomes_compostos: Lista de nomes de compostos
        matriz_risco: Lista de riscos detalhados para tooltips
    """
    # Criar dicionário de riscos para tooltips
    riscos_dict = {}
    if matriz_risco:
        for risco in matriz_risco:
            comp_a = risco.get("composto_a", "")
            comp_b = risco.get("composto_b", "")
            desc = risco.get("descricao", "")
            tipo_risco = risco.get("tipo_risco", "")
            severidade = risco.get("severidade", "")
            
            chave = f"{comp_a}||{comp_b}"
            riscos_dict[chave] = {
                "descricao": desc,
                "tipo": tipo_risco,
                "severidade": severidade
            }
    
    # Criar HTML da tabela melhorada
    html = """
    <style>
    .compat-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85em;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .compat-table th, .compat-table td {
        border: 1px solid #ccc;
        padding: 10px 8px;
        text-align: center;
        min-width: 80px;
    }
    .compat-table th {
        background-color: #2c3e50;
        color: white;
        font-weight: bold;
        position: sticky;
        top: 0;
        z-index: 10;
        white-space: nowrap;
        font-size: 0.9em;
    }
    .compat-table th.row-header {
        background-color: #34495e;
        text-align: left;
        padding-left: 12px;
        max-width: 200px;
        word-wrap: break-word;
    }
    .compat-verde {
        background-color: #90EE90;
        color: #000;
        font-weight: bold;
        cursor: pointer;
    }
    .compat-verde:hover {
        background-color: #7ACC7A;
    }
    .compat-amarelo {
        background-color: #FFD700;
        color: #000;
        font-weight: bold;
        cursor: pointer;
    }
    .compat-amarelo:hover {
        background-color: #FFC700;
    }
    .compat-vermelho {
        background-color: #FF6B6B;
        color: #fff;
        font-weight: bold;
        cursor: pointer;
    }
    .compat-vermelho:hover {
        background-color: #FF5555;
    }
    .compat-diagonal {
        background-color: #e8e8e8;
        font-weight: bold;
    }
    .compat-vazio {
        background-color: #f9f9f9;
    }
    </style>
    <table class="compat-table">
    <thead>
        <tr>
            <th style="min-width: 200px;">Produto</th>
    """
    
    # Cabeçalhos das colunas com nomes completos
    for comp in nomes_compostos:
        html += f'<th title="{comp}">{comp}</th>'
    html += "</tr></thead><tbody>"
    
    # Linhas da tabela (matriz completa para melhor visualização)
    for idx_a, comp_a in enumerate(nomes_compostos):
        html += f'<tr><th class="row-header" title="{comp_a}">{comp_a}</th>'
        for idx_b, comp_b in enumerate(nomes_compostos):
            compat = matriz.get(comp_a, {}).get(comp_b, "compativel")
            
            # Obter informações detalhadas para tooltip
            chave_direta = f"{comp_a}||{comp_b}"
            chave_reversa = f"{comp_b}||{comp_a}"
            risco_info = riscos_dict.get(chave_direta) or riscos_dict.get(chave_reversa)
            
            if comp_a == comp_b:
                html += '<td class="compat-diagonal">-</td>'
            elif idx_a > idx_b:
                # Parte inferior - espelhar o valor da parte superior (matriz simétrica)
                compat_espelhado = matriz.get(comp_b, {}).get(comp_a, "compativel")
                chave_espelhada = f"{comp_b}||{comp_a}"
                risco_info_esp = riscos_dict.get(chave_espelhada)
                
                tooltip = f"{comp_a} + {comp_b}: "
                if risco_info_esp:
                    tooltip += risco_info_esp.get("descricao", "")
                    if risco_info_esp.get("tipo"):
                        tooltip += f" | Tipo: {risco_info_esp['tipo']}"
                    if risco_info_esp.get("severidade"):
                        tooltip += f" | Severidade: {risco_info_esp['severidade']}"
                else:
                    if compat_espelhado == "compativel":
                        tooltip += "Compatível - Pode armazenar junto"
                    elif compat_espelhado == "precaucao":
                        tooltip += "Precaução - Armazenar com cuidado"
                    elif compat_espelhado == "incompativel":
                        tooltip += "Incompatível - NÃO armazenar junto"
                
                if compat_espelhado == "compativel":
                    html += f'<td class="compat-verde" title="{tooltip}">✓ BOM</td>'
                elif compat_espelhado == "precaucao":
                    html += f'<td class="compat-amarelo" title="{tooltip}">⚠ OK</td>'
                elif compat_espelhado == "incompativel":
                    html += f'<td class="compat-vermelho" title="{tooltip}">✗ NÃO</td>'
                else:
                    html += f'<td class="compat-verde" title="{tooltip}">✓ BOM</td>'
            else:
                # Construir tooltip detalhado
                tooltip = f"{comp_a} + {comp_b}: "
                if risco_info:
                    tooltip += risco_info.get("descricao", "")
                    if risco_info.get("tipo"):
                        tooltip += f" | Tipo: {risco_info['tipo']}"
                    if risco_info.get("severidade"):
                        tooltip += f" | Severidade: {risco_info['severidade']}"
                else:
                    if compat == "compativel":
                        tooltip += "Compatível - Pode armazenar junto"
                    elif compat == "precaucao":
                        tooltip += "Precaução - Armazenar com cuidado"
                    elif compat == "incompativel":
                        tooltip += "Incompatível - NÃO armazenar junto"
                
                if compat == "compativel":
                    html += f'<td class="compat-verde" title="{tooltip}">✓ BOM</td>'
                elif compat == "precaucao":
                    html += f'<td class="compat-amarelo" title="{tooltip}">⚠ OK</td>'
                elif compat == "incompativel":
                    html += f'<td class="compat-vermelho" title="{tooltip}">✗ NÃO</td>'
                else:
                    # Se não tiver informação, assume compatível (verde)
                    html += f'<td class="compat-verde" title="{tooltip}">✓ BOM</td>'
        html += "</tr>"
    
    html += "</tbody></table>"
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Legenda
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background-color: #90EE90; padding: 10px; border-radius: 5px; text-align: center;">
            <strong>✓ VERDE (BOM)</strong><br>
            Compatível - Pode armazenar junto
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background-color: #FFD700; padding: 10px; border-radius: 5px; text-align: center;">
            <strong>⚠ AMARELO (OK)</strong><br>
            Precaução - Armazenar com cuidado
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background-color: #FF6B6B; padding: 10px; border-radius: 5px; text-align: center; color: white;">
            <strong>✗ VERMELHO (NÃO)</strong><br>
            Incompatível - NÃO armazenar junto
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# 10. INTERFACE DO USUÁRIO (STREAMLIT)
# =============================================================================

def renderizar():
    st.title("Compatibilidade Química (Foto e/ou Excel)")
    st.caption("Análise de Inventários Químicos com IA - Processamento Semântico de Dados")
    
    # Verificar API Key
    api_key = obter_api_key()
    if not api_key:
        st.error("""
        **GOOGLE_API_KEY não configurada.**
        
        Configure a variável de ambiente antes de usar este módulo:
        ```bash
        export GOOGLE_API_KEY="AIzaSyDPJgpaoPISixnHOd3pPIbSt502tvChYLs"
        ```
        
        Ou configure no Streamlit Cloud/Secrets:
        ```toml
        # .streamlit/secrets.toml
        GOOGLE_API_KEY = "AIzaSyDPJgpaoPISixnHOd3pPIbSt502tvChYLs"
        ```
        """)
        return
    
    st.markdown("---")
    
    # Seção de Documentação
    with st.expander("📚 Como Funciona - Arquitetura de Processamento Semântico", expanded=False):
        st.markdown("""
        **FILOSOFIA ARQUITETURAL:**
        
        Este módulo não usa lógica tradicional de if/else para ler dados. Em vez disso, utiliza 
        um **LLM (Large Language Model) como motor de processamento ETL semântico**.
        
        **Pipeline de Processamento:**
        
        1. **Ingestão Flexível:**
           - **Caminho A (Excel):** Qualquer planilha é convertida em texto bruto (Markdown/CSV) 
             e enviada para a IA. A IA identifica automaticamente colunas químicas, ignorando 
             dados administrativos/financeiros.
           - **Caminho B (Imagem):** Fotos de rótulos, fichas de segurança ou etiquetas são 
             processadas via OCR especializado em química.
        
        2. **Normalização Inteligente:**
           - A IA extrai nomes químicos, números CAS, quantidades e unidades.
           - Trata ambiguidades e variações de nomenclatura.
        
        3. **Análise de Compatibilidade:**
           - Cruzamento automático com base de conhecimento GHS/Incompatibilidades.
           - Geração de matriz de risco e regras de segregação.
        
        **Vantagens:**
        - Aceita qualquer formato de Excel (não precisa de template rígido)
        - Interpreta dados não estruturados
        - Identifica compostos mesmo com nomenclatura variada
        - Detecta incompatibilidades automaticamente
        """)
    
    st.markdown("---")
    
    # Seleção de Modo de Entrada
    modo_entrada = st.radio(
        "Selecione o modo de entrada:",
        ["📊 Upload de Planilha Excel", "📷 Upload de Imagem (OCR)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Download de Excel de Exemplo
    with st.expander("📥 Baixar Planilha de Exemplo", expanded=False):
        st.markdown("""
        **Nota Importante:** Este é apenas um exemplo de formato. O sistema aceita **QUALQUER** 
        formato de Excel graças à capacidade da IA de interpretar dados não estruturados.
        
        Você pode ter colunas adicionais, diferentes nomes de colunas, múltiplas abas, etc. 
        A IA identificará automaticamente as informações químicas relevantes.
        """)
        
        excel_exemplo = gerar_excel_exemplo()
        st.download_button(
            label="📥 Baixar Excel de Exemplo",
            data=excel_exemplo,
            file_name="inventario_quimico_exemplo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    # Processamento baseado no modo selecionado
    inventario_normalizado = None
    
    if modo_entrada == "📊 Upload de Planilha Excel":
        st.subheader("Upload de Planilha Excel")
        
        arquivo = st.file_uploader(
            "Selecione o arquivo Excel (.xlsx, .xls)",
            type=["xlsx", "xls"],
            help="Aceita qualquer formato de Excel. A IA identificará automaticamente as colunas químicas."
        )
        
        if arquivo is not None:
            if st.button("🔍 Processar Planilha com IA", type="primary", use_container_width=True):
                with st.spinner("Processando planilha com IA..."):
                    try:
                        # Preparar dados
                        conteudo_texto = preparar_excel_para_ia(arquivo)
                        
                        # Chamar IA
                        resultado = chamar_ia_excel(conteudo_texto)
                        inventario_novo = resultado.get("inventario_normalizado", [])
                        
                        # Acumular no inventário existente (não substituir)
                        # PERMITE múltiplos frascos do mesmo produto químico
                        if 'agente_quimico_inventario' not in st.session_state:
                            st.session_state['agente_quimico_inventario'] = []
                        
                        # Adicionar ID único para cada item (permite múltiplos frascos do mesmo produto)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                        for idx, item in enumerate(inventario_novo):
                            item['id_unico'] = f"{timestamp}_{idx}"
                            item['fonte'] = f"Excel: {arquivo.name}"
                        
                        # Adicionar novos itens ao inventário existente (SEMPRE adiciona, mesmo se for o mesmo produto)
                        st.session_state['agente_quimico_inventario'].extend(inventario_novo)
                        
                        total_itens = len(st.session_state['agente_quimico_inventario'])
                        st.success(f"✅ Inventário processado: {len(inventario_novo)} novos itens adicionados. Total no inventário: {total_itens} itens (incluindo múltiplos frascos).")
                        
                    except Exception as e:
                        st.error(f"❌ Erro no processamento: {str(e)}")
                        st.info("💡 Dica: Verifique se o arquivo Excel está em formato válido e contém dados químicos.")
    
    else:  # Modo Imagem
        st.subheader("Upload de Imagem (OCR Químico)")
        
        imagem = st.file_uploader(
            "Selecione uma imagem (JPG, PNG, etc.)",
            type=["jpg", "jpeg", "png", "bmp", "webp"],
            help="Fotos de rótulos, fichas de segurança, etiquetas de produtos perigosos."
        )
        
        if imagem is not None:
            # Mostrar preview da imagem
            img_preview = Image.open(imagem)
            st.image(img_preview, caption="Imagem carregada", use_container_width=True)
            
            if st.button("🔍 Processar Imagem com OCR IA", type="primary", use_container_width=True):
                with st.spinner("Processando imagem com OCR especializado..."):
                    try:
                        # Preparar dados (retorna PIL.Image diretamente)
                        imagem_pil = preparar_imagem_para_ia(imagem)
                        
                        # Chamar IA
                        resultado = chamar_ia_imagem(imagem_pil)
                        inventario_novo = resultado.get("inventario_normalizado", [])
                        
                        # Acumular no inventário existente (não substituir)
                        # PERMITE múltiplos frascos do mesmo produto químico
                        if 'agente_quimico_inventario' not in st.session_state:
                            st.session_state['agente_quimico_inventario'] = []
                        
                        # Adicionar ID único para cada item (permite múltiplos frascos do mesmo produto)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                        for idx, item in enumerate(inventario_novo):
                            item['id_unico'] = f"{timestamp}_{idx}"
                            item['fonte'] = f"Imagem: {imagem.name}"
                        
                        # Adicionar novos itens ao inventário existente (SEMPRE adiciona, mesmo se for o mesmo produto)
                        st.session_state['agente_quimico_inventario'].extend(inventario_novo)
                        
                        total_itens = len(st.session_state['agente_quimico_inventario'])
                        st.success(f"✅ Imagem processada: {len(inventario_novo)} novos itens adicionados. Total no inventário: {total_itens} itens (incluindo múltiplos frascos).")
                        
                    except Exception as e:
                        st.error(f"❌ Erro no processamento: {str(e)}")
                        st.info("💡 Dica: Certifique-se de que a imagem está nítida e contém informações químicas legíveis.")
    
    st.markdown("---")
    
    # Exibir Inventário Normalizado (se disponível)
    if 'agente_quimico_inventario' in st.session_state:
        inventario = st.session_state['agente_quimico_inventario']
        
        if len(inventario) > 0:
            # Cabeçalho com contador e botão de limpar
            col_titulo, col_limpar = st.columns([3, 1])
            with col_titulo:
                st.subheader(f"📋 Inventário Normalizado ({len(inventario)} compostos)")
            with col_limpar:
                if st.button("🗑️ Limpar Inventário", type="secondary", use_container_width=True):
                    st.session_state['agente_quimico_inventario'] = []
                    st.session_state.pop('agente_quimico_analise', None)  # Limpar análise também
                    st.rerun()
            
            # Converter para DataFrame para exibição
            df_inventario = pd.DataFrame(inventario)
            st.dataframe(df_inventario, use_container_width=True)
            
            st.markdown("---")
            
            # Botão para Análise de Compatibilidade
            if st.button("🔬 Realizar Análise de Compatibilidade e Segregação", type="primary", use_container_width=True):
                with st.spinner("Analisando compatibilidade química e gerando regras de segregação..."):
                    try:
                        # Converter inventário para JSON string
                        inventario_json = json.dumps(inventario, ensure_ascii=False, indent=2)
                        
                        # Chamar IA para análise
                        resultado_analise = chamar_ia_analise(inventario_json)
                        
                        st.session_state['agente_quimico_analise'] = resultado_analise
                        st.success("✅ Análise de compatibilidade concluída!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro na análise: {str(e)}")
            
            # Exibir Resultados da Análise
            if 'agente_quimico_analise' in st.session_state:
                analise = st.session_state['agente_quimico_analise']
                
                st.markdown("---")
                st.subheader("⚠️ Avisos Críticos")
                
                avisos = analise.get("avisos_criticos", [])
                if avisos:
                    for aviso in avisos:
                        st.warning(f"🚨 {aviso}")
                else:
                    st.info("✅ Nenhum aviso crítico identificado.")
                
                st.markdown("---")
                st.subheader("🔗 Matriz de Risco (Incompatibilidades)")
                
                matriz_risco = analise.get("matriz_risco", [])
                if matriz_risco:
                    df_risco = pd.DataFrame(matriz_risco)
                    st.dataframe(df_risco, use_container_width=True)
                else:
                    st.info("✅ Nenhuma incompatibilidade identificada.")
                
                # Tabela de Incompatibilidade Visual
                st.markdown("---")
                st.subheader("📊 Tabela de Compatibilidade entre Produtos")
                
                # Obter lista única de compostos do inventário
                inventario = st.session_state.get('agente_quimico_inventario', [])
                if inventario and matriz_risco:
                    # Extrair todos os nomes únicos de compostos
                    nomes_compostos = sorted(list(set([item.get('nome_quimico', '') for item in inventario if item.get('nome_quimico')])))
                    
                    if len(nomes_compostos) > 1:
                        # Criar matriz de compatibilidade
                        matriz_compatibilidade = criar_matriz_compatibilidade(nomes_compostos, matriz_risco)
                        exibir_tabela_compatibilidade(matriz_compatibilidade, nomes_compostos, matriz_risco)
                    else:
                        st.info("É necessário ter pelo menos 2 compostos para gerar a tabela de compatibilidade.")
                else:
                    st.info("Processe o inventário e realize a análise para visualizar a tabela de compatibilidade.")
                
                st.markdown("---")
                st.subheader("📦 Regras de Armazenamento e Segregação")
                
                regras = analise.get("regras_armazenamento", [])
                if regras:
                    for regra in regras:
                        with st.expander(f"🧪 {regra.get('composto', 'Desconhecido')} - {regra.get('classe_perigo', 'N/A')}"):
                            st.markdown(f"**Segregação Obrigatória (NÃO armazenar junto):**")
                            seg_obrig = regra.get("segregação_obrigatoria", [])
                            if seg_obrig:
                                for item in seg_obrig:
                                    st.markdown(f"- ❌ {item}")
                            else:
                                st.info("Nenhuma segregação obrigatória identificada.")
                            
                            st.markdown(f"**Segregação Recomendada:**")
                            seg_rec = regra.get("segregação_recomendada", [])
                            if seg_rec:
                                for item in seg_rec:
                                    st.markdown(f"- ⚠️ {item}")
                            else:
                                st.info("Nenhuma segregação recomendada adicional.")
                            
                            if regra.get("condicoes_especiais"):
                                st.markdown(f"**Condições Especiais:** {regra['condicoes_especiais']}")
                else:
                    st.info("✅ Nenhuma regra de armazenamento específica identificada.")
                
                st.markdown("---")
                st.subheader("🏷️ Classificação GHS")
                
                classificacao = analise.get("classificacao_ghs", {})
                if classificacao:
                    for composto, codigos in classificacao.items():
                        st.markdown(f"**{composto}:**")
                        st.code(" ".join(codigos) if codigos else "Não classificado")
                else:
                    st.info("✅ Classificação GHS não disponível.")
    
    else:
        st.info("👆 Faça upload de uma planilha Excel ou imagem para começar a análise.")

