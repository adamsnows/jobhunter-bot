#!/usr/bin/env python3
"""
🚀 JobHunter Bot - Gerenciador de desenvolvimento
Script Python para iniciar frontend e backend simultaneamente
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

class DevServer:
    def __init__(self):
        self.frontend_process = None
        self.backend_process = None
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
        
        # Frontend
        frontend_modules = self.project_root / "frontend" / "node_modules"
        if not frontend_modules.exists():
            print(f"{Colors.YELLOW}📦 Instalando dependências do frontend...{Colors.NC}")
            result = subprocess.run(
                ["npm", "install"], 
                cwd=self.project_root / "frontend",
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Erro ao instalar dependências do frontend{Colors.NC}")
                print(result.stderr)
                return False
        
        # Backend
        backend_venv = self.project_root / "backend" / "venv"
        if not backend_venv.exists():
            print(f"{Colors.YELLOW}🐍 Criando ambiente virtual do backend...{Colors.NC}")
            subprocess.run(
                [sys.executable, "-m", "venv", "venv"], 
                cwd=self.project_root / "backend"
            )
            
            # Instalar dependências
            pip_path = backend_venv / "bin" / "pip"
            if not pip_path.exists():
                pip_path = backend_venv / "Scripts" / "pip.exe"  # Windows
                
            subprocess.run([
                str(pip_path), "install", "-r", "requirements.txt"
            ], cwd=self.project_root / "backend")
        
        return True
    
    def start_backend(self):
        """Inicia o servidor backend Flask"""
        print(f"{Colors.BLUE}🔧 Iniciando Backend (Flask)...{Colors.NC}")
        
        # Ativar ambiente virtual e iniciar
        backend_dir = self.project_root / "backend"
        venv_python = backend_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = backend_dir / "venv" / "Scripts" / "python.exe"  # Windows
        
        self.backend_process = subprocess.Popen(
            [str(venv_python), "src/web/app.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        return self.backend_process
    
    def start_frontend(self):
        """Inicia o servidor frontend Next.js"""
        print(f"{Colors.BLUE}🎨 Iniciando Frontend (Next.js)...{Colors.NC}")
        
        self.frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=self.project_root / "frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        return self.frontend_process
    
    def cleanup(self, signum=None, frame=None):
        """Limpa processos ao sair"""
        print(f"\n{Colors.YELLOW}🛑 Parando serviços...{Colors.NC}")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        print(f"{Colors.GREEN}✅ Serviços parados{Colors.NC}")
        sys.exit(0)
    
    def run(self):
        """Executa o servidor de desenvolvimento"""
        print(f"{Colors.GREEN}🤖 Iniciando JobHunter Bot em modo desenvolvimento...{Colors.NC}")
        print(f"{Colors.BLUE}📂 Diretório do projeto: {self.project_root}{Colors.NC}")
        
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        try:
            # Verificar portas
            if not self.is_port_available(3000):
                print(f"{Colors.RED}❌ Porta 3000 já está em uso (Frontend){Colors.NC}")
                return 1
                
            if not self.is_port_available(5000):
                print(f"{Colors.RED}❌ Porta 5000 já está em uso (Backend){Colors.NC}")
                return 1
            
            # Verificar dependências
            if not self.check_dependencies():
                return 1
            
            print(f"{Colors.GREEN}✅ Verificações concluídas{Colors.NC}")
            print(f"{Colors.BLUE}🚀 Iniciando serviços...{Colors.NC}")
            
            # Iniciar backend
            self.start_backend()
            time.sleep(3)  # Aguarda backend iniciar
            
            # Iniciar frontend
            self.start_frontend()
            time.sleep(5)  # Aguarda frontend iniciar
            
            print()
            print(f"{Colors.GREEN}🎉 JobHunter Bot iniciado com sucesso!{Colors.NC}")
            print()
            print(f"{Colors.BLUE}📱 Frontend (Next.js):{Colors.NC} http://localhost:3000")
            print(f"{Colors.BLUE}🔧 Backend (Flask):{Colors.NC} http://localhost:5000")
            print(f"{Colors.BLUE}📊 API Health:{Colors.NC} http://localhost:5000/api/health")
            print()
            print(f"{Colors.YELLOW}💡 Pressione Ctrl+C para parar todos os serviços{Colors.NC}")
            print()
            
            # Monitorar processos
            while True:
                if self.backend_process.poll() is not None:
                    print(f"{Colors.RED}❌ Backend parou inesperadamente{Colors.NC}")
                    break
                    
                if self.frontend_process.poll() is not None:
                    print(f"{Colors.RED}❌ Frontend parou inesperadamente{Colors.NC}")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"{Colors.RED}❌ Erro: {str(e)}{Colors.NC}")
            self.cleanup()
            return 1
        
        return 0

if __name__ == "__main__":
    server = DevServer()
    sys.exit(server.run())
