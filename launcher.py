#!/usr/bin/env python3
"""
Script de Automação para Cassava Blight Detection
Gerencia setup, execução e troubleshooting de forma simples
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_python():
    """Verifica versão do Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ necessário. Você tem: {version.major}.{version.minor}")
        print("   Baixe em: https://www.python.org/downloads/")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_nodejs():
    """Verifica se Node.js está instalado"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("❌ Node.js 18+ não encontrado")
    print("   Baixe em: https://nodejs.org/")
    return False

def check_kaggle_credentials():
    """Verifica credenciais do Kaggle"""
    home = Path.home()
    kaggle_json = home / ".kaggle" / "kaggle.json"
    
    if kaggle_json.exists():
        print(f"✓ Kaggle.json encontrado")
        return True
    else:
        print(f"⚠️  Kaggle.json não encontrado")
        print(f"   Caminho esperado: {kaggle_json}")
        return False

def run_setup():
    """Executa o setup"""
    if os.name == 'nt':
        os.system('setup_local.bat')
    else:
        print("❌ Setup para Linux/Mac não implementado ainda")
        print("   Use: bash setup.sh")

def run_app():
    """Executa a aplicação"""
    if os.name == 'nt':
        os.system('run_local.bat')
    else:
        print("❌ Run para Linux/Mac não implementado ainda")
        print("   Execute manualmente em dois terminais:")
        print("   Terminal 1: cd backend && source venv/bin/activate && python -m uvicorn main:app --reload")
        print("   Terminal 2: cd frontend && npm start")

def download_dataset():
    """Baixa o dataset do Kaggle"""
    if os.name == 'nt':
        os.chdir('backend')
        os.system('download_dataset.bat')
        os.chdir('..')
    else:
        os.chdir('backend')
        os.system('bash -c "source venv/bin/activate && python download_kaggle_dataset.py"')
        os.chdir('..')

def show_menu():
    """Mostra menu principal"""
    clear_screen()
    print("=" * 50)
    print("🌿 Cassava Blight Detection - Menu Principal")
    print("=" * 50)
    print()
    print("1️⃣  Setup Inicial (executar UMA VEZ)")
    print("2️⃣  Rodar Aplicação")
    print("3️⃣  Baixar Dataset do Kaggle")
    print("4️⃣  Verificar Dependências")
    print("5️⃣  Ver Documentação")
    print("0️⃣  Sair")
    print()
    return input("Escolha uma opção (0-5): ").strip()

def show_docs():
    """Mostra documentação"""
    clear_screen()
    print("=" * 50)
    print("📚 Documentação")
    print("=" * 50)
    print()
    print("ARQUIVOS IMPORTANTES:")
    print()
    print("📄 COMECE_AQUI.txt")
    print("   → Guia rápido em português")
    print()
    print("📄 EXECUTATION_GUIDE_PT_BR.md")
    print("   → Guia completo com exemplos e troubleshooting")
    print()
    print("📄 README.md")
    print("   → Documentação técnica da IA")
    print()
    print("📄 SETUP.md")
    print("   → Setup avançado e deploy")
    print()
    print("🌐 http://localhost:8000/docs")
    print("   → Documentação da API (ao rodar)")
    print()
    input("Pressione ENTER para voltar...")

def show_deps():
    """Mostra status das dependências"""
    clear_screen()
    print("=" * 50)
    print("🔍 Verificando Dependências")
    print("=" * 50)
    print()
    
    all_ok = True
    
    if not check_python():
        all_ok = False
    
    if not check_nodejs():
        all_ok = False
    
    check_kaggle_credentials()
    
    print()
    if all_ok:
        print("✅ Tudo pode rodar!")
    else:
        print("❌ Faltam dependências. Instale-as antes.")
    print()
    input("Pressione ENTER para voltar...")

def main():
    """Função principal"""
    os.chdir(Path(__file__).parent)
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            print()
            print("⏳ Executando setup...")
            print("   Isso pode levar alguns minutos...")
            print()
            run_setup()
            print()
            input("Pressione ENTER para voltar...")
            
        elif choice == '2':
            print()
            print("⏳ Iniciando aplicação...")
            print()
            run_app()
            
        elif choice == '3':
            print()
            print("⏳ Baixando dataset...")
            print("   Isso pode levar 30+ minutos (dataset é grande)...")
            print()
            download_dataset()
            print()
            input("Pressione ENTER para voltar...")
            
        elif choice == '4':
            show_deps()
            
        elif choice == '5':
            show_docs()
            
        elif choice == '0':
            print()
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")
            input("Pressione ENTER para tentar novamente...")

if __name__ == "__main__":
    if not check_python():
        sys.exit(1)
    main()

