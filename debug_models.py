"""
Script de Diagnóstico: Listar Modelos Disponíveis do Google Gemini

Este script lista todos os modelos disponíveis na API do Google Gemini,
especialmente aqueles que contêm "flash" no nome e suportam generateContent.
"""

import os
import sys
from dotenv import load_dotenv
import pathlib
import google.genai as genai

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis de ambiente
# Tenta múltiplos caminhos
env_paths = [
    pathlib.Path(__file__).parent / '.env',
    pathlib.Path(__file__).parent.parent / '.env',
    pathlib.Path('.env')
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        break
else:
    load_dotenv()  # Fallback: tenta carregar do diretório atual

# Obter API key
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ ERRO: GOOGLE_API_KEY não encontrada no arquivo .env")
    print("Configure a variável GOOGLE_API_KEY no arquivo .env")
    exit(1)

print(f"✅ API Key carregada: {api_key[:20]}...")
print("\n" + "="*60)
print("LISTANDO MODELOS DISPONÍVEIS DO GOOGLE GEMINI")
print("="*60 + "\n")

try:
    # Inicializar cliente
    client = genai.Client(api_key=api_key)
    
    # Listar todos os modelos disponíveis
    print("Buscando modelos disponíveis...\n")
    
    # Tentar listar modelos
    try:
        models = client.models.list()
        
        print("📋 TODOS OS MODELOS DISPONÍVEIS:")
        print("-" * 60)
        
        flash_models = []
        all_models = []
        
        for model in models:
            model_name = model.name if hasattr(model, 'name') else str(model)
            all_models.append(model_name)
            
            # Filtrar modelos com "flash" no nome
            if "flash" in model_name.lower():
                flash_models.append(model_name)
                print(f"  🔹 {model_name}")
        
        print("\n" + "="*60)
        print(f"📊 RESUMO:")
        print(f"   Total de modelos encontrados: {len(all_models)}")
        print(f"   Modelos com 'flash' no nome: {len(flash_models)}")
        print("="*60 + "\n")
        
        if flash_models:
            print("✅ MODELOS FLASH DISPONÍVEIS:")
            for model in flash_models:
                print(f"   • {model}")
        else:
            print("⚠️  Nenhum modelo com 'flash' encontrado na lista.")
        
        print("\n" + "="*60)
        print("💡 RECOMENDAÇÃO:")
        if flash_models:
            print(f"   Use: {flash_models[0]}")
        else:
            print("   Verifique a documentação da API para o nome correto do modelo.")
        print("="*60)
        
    except AttributeError:
        # Se list() não funcionar, tentar método alternativo
        print("⚠️  Método list() não disponível. Tentando método alternativo...\n")
        
        # Tentar usar diretamente alguns nomes conhecidos
        modelos_testar = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-001",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash",
            "gemini-pro",
            "gemini-1.5-pro"
        ]
        
        print("Testando modelos conhecidos:")
        print("-" * 60)
        
        modelos_validos = []
        for modelo_nome in modelos_testar:
            try:
                # Tentar criar uma requisição simples para verificar se o modelo existe
                response = client.models.generate_content(
                    model=modelo_nome,
                    contents="test",
                    config={"max_output_tokens": 1}
                )
                modelos_validos.append(modelo_nome)
                print(f"  ✅ {modelo_nome} - VÁLIDO")
            except Exception as e:
                error_str = str(e).lower()
                if "404" in error_str or "not found" in error_str:
                    print(f"  ❌ {modelo_nome} - NÃO ENCONTRADO (404)")
                else:
                    print(f"  ⚠️  {modelo_nome} - Erro: {str(e)[:50]}")
        
        print("\n" + "="*60)
        print("✅ MODELOS VÁLIDOS ENCONTRADOS:")
        for modelo in modelos_validos:
            print(f"   • {modelo}")
        print("="*60)
        
except Exception as e:
    print(f"\n❌ ERRO ao listar modelos: {str(e)}")
    print("\nDetalhes do erro:")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensagem: {str(e)}")
    
    # Sugestões de troubleshooting
    print("\n" + "="*60)
    print("🔧 TROUBLESHOOTING:")
    print("   1. Verifique se a API key está correta")
    print("   2. Verifique se a biblioteca google-genai está atualizada:")
    print("      pip install -U google-genai")
    print("   3. Verifique a documentação oficial do Google Gemini")
    print("="*60)

