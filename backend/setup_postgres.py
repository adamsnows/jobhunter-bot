#!/usr/bin/env python3
"""
Setup script para configurar PostgreSQL local para o JobHunter Bot
"""
import os
import subprocess
import sys

def check_postgresql():
    """Verifica se PostgreSQL está instalado"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL está instalado")
            return True
    except FileNotFoundError:
        pass

    print("❌ PostgreSQL não encontrado")
    return False

def install_postgresql_macos():
    """Instala PostgreSQL no macOS usando Homebrew"""
    print("📦 Instalando PostgreSQL via Homebrew...")
    try:
        # Instalar PostgreSQL
        subprocess.run(['brew', 'install', 'postgresql@15'], check=True)
        print("✅ PostgreSQL instalado")

        # Iniciar serviço
        subprocess.run(['brew', 'services', 'start', 'postgresql@15'], check=True)
        print("✅ Serviço PostgreSQL iniciado")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar PostgreSQL: {e}")
        return False

def create_database():
    """Cria o banco de dados JobHunter"""
    try:
        # Criar banco de dados
        subprocess.run(['createdb', 'jobhunter_db'], check=True)
        print("✅ Banco de dados 'jobhunter_db' criado")

        # Criar usuário (opcional)
        create_user_sql = """
        CREATE USER jobhunter WITH PASSWORD 'jobhunter123';
        GRANT ALL PRIVILEGES ON DATABASE jobhunter_db TO jobhunter;
        """

        proc = subprocess.run(['psql', 'jobhunter_db'],
                             input=create_user_sql,
                             text=True,
                             capture_output=True)

        if proc.returncode == 0:
            print("✅ Usuário 'jobhunter' criado")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def create_env_file():
    """Cria arquivo .env com configurações padrão"""
    env_content = """# ==============================================
# JOBHUNTER BOT - CONFIGURAÇÕES ESSENCIAIS
# ==============================================

# EMAIL CONFIGURATION (Gmail)
EMAIL_USER=seu.email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app_do_gmail
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# DADOS PESSOAIS PARA CANDIDATURA
USER_NAME=Seu Nome Completo
USER_EMAIL=seu.email@gmail.com
USER_PHONE=+55 11 99999-9999
USER_LINKEDIN=https://linkedin.com/in/seu-perfil

# ARQUIVO DE CURRÍCULO (coloque na pasta documents/)
CV_FILE_PATH=documents/seu_cv.pdf

# CONFIGURAÇÕES DE BUSCA DE VAGAS
JOB_KEYWORDS=python developer,software engineer,backend developer,fullstack developer
JOB_LOCATION=São Paulo, Brazil
EXPERIENCE_LEVEL=mid
JOB_TYPE=full-time

# CONFIGURAÇÕES DE CANDIDATURA
AUTO_APPLY=true
MIN_MATCH_SCORE=0.6
MAX_APPLICATIONS_PER_DAY=5

# HORÁRIOS DE BUSCA (formato HH:MM)
SEARCH_TIMES=09:00,14:00,18:00
SEARCH_INTERVAL_HOURS=4

# DATABASE (PostgreSQL local)
DATABASE_URL=postgresql://jobhunter:jobhunter123@localhost:5432/jobhunter_db

# CONFIGURAÇÕES GERAIS
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_TELEGRAM_NOTIFICATIONS=false
ENABLE_WHATSAPP_NOTIFICATIONS=false
HEADLESS_MODE=true
TEST_MODE=false
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ Arquivo .env criado")

def main():
    print("🤖 JobHunter Bot - Setup PostgreSQL")
    print("=" * 40)

    # Verificar se PostgreSQL está instalado
    if not check_postgresql():
        if sys.platform == "darwin":  # macOS
            install_postgresql_macos()
        else:
            print("❌ Por favor, instale PostgreSQL manualmente")
            print("Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib")
            print("CentOS/RHEL: sudo yum install postgresql postgresql-server")
            return

    # Criar banco de dados
    create_database()

    # Criar arquivo .env
    if not os.path.exists('.env'):
        create_env_file()
    else:
        print("⚠️  Arquivo .env já existe, não sobrescrevendo")

    print("\n🎉 Setup concluído!")
    print("\n📝 Próximos passos:")
    print("1. Edite o arquivo .env com suas configurações")
    print("2. Coloque seu CV na pasta documents/")
    print("3. Configure sua senha de app do Gmail")
    print("4. Execute: python -m src.bot.job_hunter_daemon")

if __name__ == "__main__":
    main()
