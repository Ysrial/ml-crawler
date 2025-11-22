#!/usr/bin/env python
"""
Setup Automático - Inicializa tudo para rodar o app
Execute: python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(num, msg):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[{num}]{Colors.END} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def run_command(cmd, description):
    """Executa comando e retorna sucesso/falha"""
    try:
        print_info(f"Executando: {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(description)
            return True
        else:
            print_error(f"Falha: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 60)
    print("  🚀 ML CRAWLER - SETUP AUTOMÁTICO")
    print("=" * 60)
    print(f"{Colors.END}\n")
    
    # ========== PASSO 1: Verificar Python ==========
    print_step(1, "Verificando Python")
    if sys.version_info >= (3, 8):
        print_success(f"Python {sys.version.split()[0]} encontrado")
    else:
        print_error("Python 3.8+ obrigatório")
        sys.exit(1)
    
    # ========== PASSO 2: Verificar PostgreSQL ==========
    print_step(2, "Verificando PostgreSQL")
    if run_command("psql --version", "PostgreSQL detectado"):
        print_warning("Certifique-se de que o serviço está rodando!")
    else:
        print_warning("PostgreSQL não encontrado no PATH")
        print_info("Instale em: https://www.postgresql.org/download/")
    
    # ========== PASSO 3: Criar .env ==========
    print_step(3, "Configurando variáveis de ambiente")
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            with open(env_example_path) as f:
                env_content = f.read()
            with open(env_path, "w") as f:
                f.write(env_content)
            print_success(".env criado")
        else:
            print_warning(".env.example não encontrado")
    else:
        print_info(".env já existe")
    
    # ========== PASSO 4: Criar diretórios ==========
    print_step(4, "Criando diretórios necessários")
    dirs = ["data", "logs", "reports"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print_success(f"Diretório '{d}/' pronto")
    
    # ========== PASSO 5: Instalar dependências ==========
    print_step(5, "Instalando dependências Python")
    if run_command("pip install -r requirements.txt", "Dependências instaladas"):
        pass
    else:
        print_error("Falha ao instalar dependências")
        sys.exit(1)
    
    # ========== PASSO 6: Testar conexão BD ==========
    print_step(6, "Testando conexão com PostgreSQL")
    try:
        from src.database_postgres import db
        db.initialize_db()
        print_success("Banco de dados pronto!")
    except Exception as e:
        print_error(f"Erro ao conectar: {e}")
        print_warning("Verifique se PostgreSQL está rodando e .env está correto")
        print_info("Para iniciar PostgreSQL: brew services start postgresql@15")
    
    # ========== PASSO 7: Pronto! ==========
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("=" * 60)
    print("  ✅ SETUP COMPLETO!")
    print("=" * 60)
    print(f"{Colors.END}\n")
    
    print_info("Para rodar o app, execute:")
    print(f"\n  {Colors.BOLD}streamlit run app.py{Colors.END}\n")
    
    print_info("O app abrirá em: http://localhost:8501")
    print_info("Pressione CTRL+C para parar o servidor")
    
    # ========== OPÇÃO: Rodar app automaticamente ==========
    print()
    try:
        resposta = input("Deseja rodar o app agora? (s/n): ").lower()
        if resposta == "s":
            print("\n🚀 Iniciando Streamlit...\n")
            os.system("streamlit run app.py")
        else:
            print_info("Para rodar depois, use: streamlit run app.py")
    except KeyboardInterrupt:
        print_info("\nSetup concluído!")

if __name__ == "__main__":
    main()
