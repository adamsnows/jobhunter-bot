#!/usr/bin/env python3
"""
🤖 JobHunter Bot - Backend Starter
Script simples para iniciar o backend Flask
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Encontra a raiz do projeto
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    backend_dir = project_root / "backend"

    # Verifica se está no diretório correto
    if not backend_dir.exists():
        print("❌ Erro: Diretório backend não encontrado")
        sys.exit(1)

    # Navega para o backend
    os.chdir(backend_dir)

    # Verifica ambiente virtual
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("🐍 Criando ambiente virtual...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])

        # Ativa e instala dependências
        if os.name == 'nt':  # Windows
            pip_cmd = str(venv_dir / "Scripts" / "pip")
        else:  # Unix/Linux/macOS
            pip_cmd = str(venv_dir / "bin" / "pip")

        print("📦 Instalando dependências...")
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])

    # Inicia o Flask
    if os.name == 'nt':  # Windows
        python_cmd = str(venv_dir / "Scripts" / "python")
    else:  # Unix/Linux/macOS
        python_cmd = str(venv_dir / "bin" / "python")

    print("🚀 Iniciando Backend Flask...")
    subprocess.run([python_cmd, "src/web/app.py"])

if __name__ == "__main__":
    main()
