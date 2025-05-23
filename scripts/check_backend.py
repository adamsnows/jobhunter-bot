#!/usr/bin/env python3
"""
🔍 JobHunter Bot - Backend Dependency Checker
Script para verificar e corrigir problemas nas dependências do backend Python
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

class BackendTester:
    def __init__(self):
        self.project_root = self.find_project_root()
        self.backend_dir = self.project_root / "backend"
        self.venv_dir = self.backend_dir / "venv"
        self.requirements_file = self.backend_dir / "requirements.txt"

    def find_project_root(self):
        """Encontra a raiz do projeto"""
        current = Path.cwd()

        # Se já estamos na raiz
        if (current / "frontend").exists() and (current / "backend").exists():
            return current

        # Se estamos em uma subpasta
        parent = current.parent
        if (parent / "frontend").exists() and (parent / "backend").exists():
            return parent

        raise Exception("Não foi possível encontrar a raiz do projeto")

    def ensure_venv(self):
        """Verifica e cria o ambiente virtual se necessário"""
        if not self.venv_dir.exists():
            print(f"{Colors.YELLOW}🐍 Criando ambiente virtual Python...{Colors.NC}")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
            print(f"{Colors.GREEN}✅ Ambiente virtual criado em {self.venv_dir}{Colors.NC}")
        else:
            print(f"{Colors.GREEN}✅ Ambiente virtual já existe em {self.venv_dir}{Colors.NC}")

    def pip_command(self, cmd):
        """Executa um comando pip dentro do ambiente virtual"""
        activate_cmd = ""
        if os.name == "nt":  # Windows
            activate_cmd = f"{self.venv_dir}\\Scripts\\activate && "
            final_cmd = f"cmd /c \"{activate_cmd}{cmd}\""
        else:  # Unix/Linux/Mac
            activate_cmd = f"source {self.venv_dir}/bin/activate && "
            final_cmd = f"bash -c '{activate_cmd}{cmd}'"

        return subprocess.run(final_cmd, shell=True, capture_output=True, text=True, cwd=self.backend_dir)

    def check_packages(self):
        """Verifica se os pacotes essenciais estão instalados"""
        print(f"{Colors.BLUE}📦 Verificando pacotes essenciais...{Colors.NC}")

        # Atualiza pip, setuptools e wheel
        print(f"{Colors.YELLOW}🔄 Atualizando pip, setuptools e wheel...{Colors.NC}")
        result = self.pip_command("pip install --upgrade pip setuptools wheel")
        if result.returncode != 0:
            print(f"{Colors.RED}❌ Erro ao atualizar pip: {result.stderr}{Colors.NC}")
        else:
            print(f"{Colors.GREEN}✅ pip atualizado com sucesso{Colors.NC}")

        # Lista de pacotes essenciais para verificar
        essential_packages = ['flask', 'flask-sqlalchemy', 'flask-cors']
        missing_packages = []

        for pkg in essential_packages:
            print(f"{Colors.YELLOW}🔍 Verificando {pkg}...{Colors.NC}")
            result = self.pip_command(f"pip show {pkg}")
            if result.returncode != 0 or not result.stdout.strip():
                missing_packages.append(pkg)
                print(f"{Colors.RED}❌ {pkg} não encontrado{Colors.NC}")
            else:
                print(f"{Colors.GREEN}✅ {pkg} instalado: {result.stdout.splitlines()[1]}{Colors.NC}")

        if missing_packages:
            print(f"{Colors.YELLOW}🔄 Instalando pacotes ausentes: {', '.join(missing_packages)}{Colors.NC}")
            result = self.pip_command(f"pip install {' '.join(missing_packages)}")
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Erro ao instalar pacotes: {result.stderr}{Colors.NC}")
            else:
                print(f"{Colors.GREEN}✅ Pacotes instalados com sucesso{Colors.NC}")

        # Verifica se spacy está instalado corretamente
        print(f"{Colors.YELLOW}🔍 Verificando spacy...{Colors.NC}")
        result = self.pip_command("pip show spacy")
        if result.returncode != 0 or not result.stdout.strip():
            print(f"{Colors.RED}❌ spacy não encontrado, tentando instalar...{Colors.NC}")
            result = self.pip_command("pip install spacy")
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Erro ao instalar spacy: {result.stderr}{Colors.NC}")
            else:
                print(f"{Colors.GREEN}✅ spacy instalado com sucesso{Colors.NC}")

        # Verifica se blis está instalado corretamente (comum causar problemas)
        print(f"{Colors.YELLOW}🔍 Verificando blis (dependência de spacy)...{Colors.NC}")
        result = self.pip_command("pip show blis")
        if result.returncode != 0 or not result.stdout.strip():
            print(f"{Colors.RED}❌ blis não encontrado, tentando instalar...{Colors.NC}")
            # Tenta instalar com flags especiais que podem ajudar em sistemas macOS
            result = self.pip_command("ARCHFLAGS=\"-arch x86_64\" pip install --no-binary=blis blis")
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Erro ao instalar blis: {result.stderr}{Colors.NC}")
                print(f"{Colors.YELLOW}💡 Tente executar 'ARCHFLAGS=\"-arch x86_64\" pip install --no-binary=blis blis' manualmente{Colors.NC}")
            else:
                print(f"{Colors.GREEN}✅ blis instalado com sucesso{Colors.NC}")
        else:
            print(f"{Colors.GREEN}✅ blis já está instalado{Colors.NC}")

    def install_all_requirements(self):
        """Instala todas as dependências do requirements.txt"""
        print(f"{Colors.BLUE}📦 Instalando todas as dependências do requirements.txt...{Colors.NC}")
        result = self.pip_command("pip install -r requirements.txt")
        if result.returncode != 0:
            print(f"{Colors.RED}❌ Erro ao instalar todas as dependências: {result.stderr}{Colors.NC}")
            return False
        else:
            print(f"{Colors.GREEN}✅ Todas as dependências instaladas com sucesso{Colors.NC}")
            return True

    def test_flask_server(self):
        """Testa se o servidor Flask inicia corretamente"""
        print(f"{Colors.BLUE}🔧 Testando servidor Flask...{Colors.NC}")

        # Verifica se o módulo Flask pode ser importado
        flask_test = """
import flask
import flask_sqlalchemy
import flask_cors
print("✓ Flask e suas dependências podem ser importadas")

# Tenta criar uma aplicação Flask mínima
app = flask.Flask(__name__)
print("✓ Instância do Flask criada com sucesso")

# Tenta configurar CORS
flask_cors.CORS(app)
print("✓ CORS configurado com sucesso")

# Tenta configurar SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
db = flask_sqlalchemy.SQLAlchemy(app)
print("✓ SQLAlchemy configurado com sucesso")

print("FLASK_TEST_SUCCESS")
"""

        # Salva o teste em um arquivo temporário
        test_file = self.backend_dir / "flask_test_temp.py"
        with open(test_file, "w") as f:
            f.write(flask_test)

        try:
            print(f"{Colors.YELLOW}🔍 Executando teste do Flask...{Colors.NC}")
            result = self.pip_command(f"python {test_file}")

            if "FLASK_TEST_SUCCESS" in result.stdout:
                print(f"{Colors.GREEN}✅ Servidor Flask testado com sucesso!{Colors.NC}")
                print(f"{Colors.GREEN}✅ Saída do teste:\n{result.stdout}{Colors.NC}")
                return True
            else:
                print(f"{Colors.RED}❌ Teste do Flask falhou{Colors.NC}")
                print(f"{Colors.RED}❌ Saída do teste:\n{result.stdout}{Colors.NC}")
                print(f"{Colors.RED}❌ Erros:\n{result.stderr}{Colors.NC}")
                return False
        finally:
            # Remove o arquivo temporário
            if test_file.exists():
                test_file.unlink()

    def run(self):
        """Executa todos os testes"""
        print(f"{Colors.GREEN}🤖 JobHunter Bot - Backend Dependency Checker{Colors.NC}")
        print(f"{Colors.BLUE}📂 Diretório do projeto: {self.project_root}{Colors.NC}")
        print(f"{Colors.BLUE}📂 Diretório backend: {self.backend_dir}{Colors.NC}")

        try:
            # Verifica e cria o ambiente virtual, se necessário
            self.ensure_venv()

            # Verifica e instala os pacotes essenciais
            self.check_packages()

            # Pergunta se deve tentar instalar todos os pacotes
            print(f"{Colors.YELLOW}⚠️ Deseja instalar todas as dependências do requirements.txt? (s/n){Colors.NC}")
            answer = input().strip().lower()
            if answer == 's' or answer == 'y':
                self.install_all_requirements()

            # Testa o servidor Flask
            flask_ok = self.test_flask_server()

            # Resumo final
            print("\n" + "="*50)
            print(f"{Colors.BLUE}📋 RESUMO FINAL{Colors.NC}")
            print("="*50)

            if flask_ok:
                print(f"{Colors.GREEN}✅ O ambiente Flask está configurado corretamente!{Colors.NC}")
                print(f"{Colors.GREEN}✅ Você pode iniciar o projeto com 'pnpm run dev' ou 'make dev-pnpm'{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Existem problemas com a configuração do Flask{Colors.NC}")
                print(f"{Colors.YELLOW}💡 Siga as instruções acima para resolver os problemas{Colors.NC}")

        except Exception as e:
            print(f"{Colors.RED}❌ Ocorreu um erro: {str(e)}{Colors.NC}")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run()
