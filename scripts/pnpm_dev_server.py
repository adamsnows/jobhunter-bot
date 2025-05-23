#!/usr/bin/env python3
"""
🚀 JobHunter Bot - PNPM Workspace Development Server
Script Python para iniciar o ambiente de desenvolvimento completo via pnpm workspace
"""

import os
import sys
import subprocess
import signal
import time
import socket
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

class PnpmDevServer:
    def __init__(self):
        self.dev_process = None
        self.project_root = self.find_project_root()

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

    def is_port_available(self, port):
        """Verifica se uma porta está disponível"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False

    def check_dependencies(self):
        """Verifica e instala dependências se necessário"""
        print(f"{Colors.BLUE}📦 Verificando dependências...{Colors.NC}")

        # Verifica se o pnpm está instalado
        try:
            subprocess.run(["pnpm", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}❌ pnpm não encontrado. Instalando...{Colors.NC}")
            try:
                subprocess.run(["npm", "install", "-g", "pnpm"], check=True)
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}❌ Falha ao instalar pnpm. Por favor, instale manualmente:{Colors.NC}")
                print("npm install -g pnpm")
                return False

        # Verifica se as dependências estão instaladas
        if not (self.project_root / "node_modules").exists():
            print(f"{Colors.YELLOW}🔍 Instalando dependências via pnpm...{Colors.NC}")
            try:
                subprocess.run(["pnpm", "install"], cwd=self.project_root, check=True)
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}❌ Falha ao instalar dependências.{Colors.NC}")
                return False

        # Verifica se o ambiente virtual do Python existe
        backend_venv = self.project_root / "backend" / "venv"
        if not backend_venv.exists():
            print(f"{Colors.YELLOW}🐍 Configurando ambiente virtual Python...{Colors.NC}")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(backend_venv)], check=True)
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}❌ Falha ao criar ambiente virtual Python.{Colors.NC}")
                return False

        # Verifica se as dependências do Python estão instaladas
        activate_script = str(backend_venv / "bin" / "activate")
        pip_path = str(backend_venv / "bin" / "pip")

        if not os.path.exists(pip_path):
            print(f"{Colors.RED}❌ Ambiente virtual Python parece corrompido. Tente remover a pasta 'backend/venv' e rodar novamente.{Colors.NC}")
            return False

        print(f"{Colors.YELLOW}🐍 Verificando/instalando dependências Python...{Colors.NC}")
        try:
            # Garante que pip, wheel e setuptools estão atualizados
            subprocess.run(f"source {activate_script} && pip install --upgrade pip wheel setuptools",
                          shell=True, check=True, cwd=self.project_root / "backend")

            # Instala as dependências com handling especial para pacotes problemáticos
            print(f"{Colors.BLUE}📦 Instalando dependências Python do requirements.txt...{Colors.NC}")
            subprocess.run(f"source {activate_script} && pip install -r requirements.txt",
                          shell=True, check=True, cwd=self.project_root / "backend")

            # Teste se flask está instalado corretamente
            test_flask = subprocess.run(
                f"source {activate_script} && python -c 'import flask; print(\"Flask installed!\")'",
                shell=True, capture_output=True, text=True, cwd=self.project_root / "backend"
            )

            if "Flask installed!" not in test_flask.stdout:
                print(f"{Colors.RED}❌ Flask não está instalado corretamente. Tentando instalar diretamente...{Colors.NC}")
                subprocess.run(f"source {activate_script} && pip install flask==2.3.3 flask-sqlalchemy==3.0.5 flask-cors==4.0.0",
                              shell=True, check=True, cwd=self.project_root / "backend")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Falha ao instalar dependências Python: {e}{Colors.NC}")
            print(f"{Colors.YELLOW}💡 Tentando instalar manualmente...{Colors.NC}")

            # Tenta instalar dependências críticas diretamente
            try:
                subprocess.run(f"source {activate_script} && pip install flask==2.3.3 flask-sqlalchemy==3.0.5 flask-cors==4.0.0",
                              shell=True, check=True, cwd=self.project_root / "backend")
                print(f"{Colors.GREEN}✅ Dependências críticas instaladas com sucesso{Colors.NC}")
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}❌ Falha na instalação manual das dependências{Colors.NC}")
                return False

        return True

    def start_dev_services(self):
        """Inicia os serviços de desenvolvimento via pnpm"""
        print(f"{Colors.GREEN}🚀 Iniciando JobHunter Bot via pnpm workspace...{Colors.NC}")        # Verifica se as portas 3000 e 5001 estão disponíveis
        if not self.is_port_available(3000):
            print(f"{Colors.RED}❌ Porta 3000 já está em uso (Frontend){Colors.NC}")
            return False

        if not self.is_port_available(5001):
            print(f"{Colors.RED}❌ Porta 5001 já está em uso (Backend){Colors.NC}")
            return False

        # Inicia os serviços via pnpm dev - usando a versão atualizada que inclui a ativação do venv
        self.dev_process = subprocess.Popen(
            ["pnpm", "run", "dev"],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=False
        )

        return True

    def display_output(self):
        """Exibe a saída dos processos"""
        while self.dev_process and self.dev_process.poll() is None:
            output = self.dev_process.stdout.readline().strip()
            if output:
                print(output)
                # Detecta que o frontend está pronto
                if "Local:" in output and "http://localhost:3000" in output:
                    print(f"\n{Colors.GREEN}✅ Frontend pronto!{Colors.NC}")
                    print(f"{Colors.BLUE}📱 Frontend (Next.js): http://localhost:3000{Colors.NC}")
                # Detecta que o backend está pronto
                elif "JobHunter Bot API iniciada" in output:
                    print(f"\n{Colors.GREEN}✅ Backend pronto!{Colors.NC}")
                    print(f"{Colors.BLUE}🔧 Backend (Flask): http://localhost:5001{Colors.NC}")
                    print(f"{Colors.BLUE}📊 API Health: http://localhost:5001/api/health{Colors.NC}")

    def cleanup(self, signum=None, frame=None):
        """Limpa processos ao sair"""
        print(f"\n{Colors.YELLOW}🛑 Parando serviços...{Colors.NC}")

        if self.dev_process:
            self.dev_process.terminate()
            try:
                self.dev_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.dev_process.kill()

        print(f"{Colors.GREEN}✅ Serviços parados{Colors.NC}")
        sys.exit(0)

    def run(self):
        """Executa o servidor de desenvolvimento"""
        print(f"{Colors.GREEN}🤖 JobHunter Bot - PNPM Workspace Development Server{Colors.NC}")
        print(f"{Colors.BLUE}📂 Diretório do projeto: {self.project_root}{Colors.NC}")

        # Configurar signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

        # Verifica portas
        if not self.is_port_available(3000):
            print(f"{Colors.RED}❌ Porta 3000 já está em uso (Frontend){Colors.NC}")
            return

        if not self.is_port_available(5001):
            print(f"{Colors.RED}❌ Porta 5001 já está em uso (Backend){Colors.NC}")
            return

        # Verifica e instala dependências
        if not self.check_dependencies():
            return

        # Inicia os serviços
        if self.start_dev_services():
            print(f"{Colors.GREEN}🚀 Serviços iniciados via pnpm{Colors.NC}")
            print(f"{Colors.YELLOW}💡 Pressione Ctrl+C para parar todos os serviços{Colors.NC}")

            try:
                # Exibe outputs dos processos
                self.display_output()
            except KeyboardInterrupt:
                pass
            finally:
                self.cleanup()

if __name__ == "__main__":
    server = PnpmDevServer()
    server.run()
