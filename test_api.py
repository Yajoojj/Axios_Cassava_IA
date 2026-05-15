"""
Script de Teste Rápido da API
Verifica se a API está funcionando corretamente
"""

import requests
import sys
import time

API_URL = "http://localhost:8000"

def check_api_health():
    """Verifica se a API está respondendo"""
    try:
        print(f"🔍 Testando saúde da API em {API_URL}...")
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API está respondendo!")
            print(f"   Status: {data.get('status')}")
            print(f"   Modelo carregado: {data.get('model_loaded')}")
            print(f"   Versão: {data.get('version')}")
            return True
        else:
            print(f"❌ API retornou erro: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Não consegui conectar à API")
        print(f"   Verifique se o backend está rodando em {API_URL}")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def check_frontend():
    """Verifica se o frontend está rodando"""
    try:
        print(f"\n🔍 Testando frontend em http://localhost:3000...")
        response = requests.get("http://localhost:3000", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Frontend está respondendo!")
            print(f"   URL: http://localhost:3000")
            return True
        else:
            print(f"❌ Frontend retornou erro: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Não consegui conectar ao frontend")
        print(f"   Verifique se o frontend está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def check_api_docs():
    """Verifica se a documentação da API está disponível"""
    try:
        print(f"\n🔍 Testando documentação da API...")
        response = requests.get(f"{API_URL}/docs", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ API Docs estão disponíveis!")
            print(f"   URL: {API_URL}/docs")
            return True
        else:
            print(f"❌ API Docs retornaram erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def check_metrics():
    """Verifica endpoint de métricas"""
    try:
        print(f"\n🔍 Testando métricas da API...")
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Métricas disponíveis!")
            print(f"   Total de predições: {data.get('total_predictions', 0)}")
            print(f"   Tempo médio: {data.get('average_processing_time_ms', 0):.2f}ms")
            return True
        else:
            print(f"❌ Métricas retornaram erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 Teste de Funcionamento - Cassava Blight Detection")
    print("=" * 60)
    print()
    
    print("⏳ Aguardando 2 segundos para garantir que tudo está carregado...")
    time.sleep(2)
    print()
    
    all_ok = True
    
    # Testa API
    if not check_api_health():
        all_ok = False
    
    # Testa Docs
    if not check_api_docs():
        all_ok = False
    
    # Testa Métricas
    if not check_metrics():
        all_ok = False
    
    # Testa Frontend
    if not check_frontend():
        all_ok = False
    
    print()
    print("=" * 60)
    if all_ok:
        print("✅ TUDO ESTÁ FUNCIONANDO!")
        print()
        print("URLs de acesso:")
        print(f"  Frontend:   http://localhost:3000")
        print(f"  API:        http://localhost:8000")
        print(f"  API Docs:   http://localhost:8000/docs")
        print(f"  Health:     http://localhost:8000/health")
        print(f"  Métricas:   http://localhost:8000/metrics")
    else:
        print("❌ ALGUNS SERVIÇOS NÃO ESTÃO RESPONDENDO")
        print()
        print("Verifique:")
        print("  1. Backend está rodando? (run_local.bat - Terminal 1)")
        print("  2. Frontend está rodando? (run_local.bat - Terminal 2)")
        print("  3. setup_local.bat foi executado?")
        print("  4. Portas 8000 e 3000 não estão em uso")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        sys.exit(1)

