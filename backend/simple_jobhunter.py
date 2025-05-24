#!/usr/bin/env python3
"""
JobHunter Bot - Versão Simplificada
Busca vagas no LinkedIn e X, extrai emails e envia CVs automaticamente.
"""

import os
import time
import logging
import sqlite3
import smtplib
import re
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jobhunter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleJobHunter:
    """JobHunter Bot simplificado para busca de vagas e envio automático de CVs"""

    def __init__(self):
        # Carrega configurações do .env
        load_dotenv()

        # Configurações de email
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))

        # Dados pessoais
        self.user_name = os.getenv('USER_NAME')
        self.user_email = os.getenv('USER_EMAIL')
        self.user_phone = os.getenv('USER_PHONE', '')
        self.user_linkedin = os.getenv('USER_LINKEDIN', '')

        # Arquivo de CV
        self.cv_file_path = os.getenv('CV_FILE_PATH', 'documents/cv.pdf')

        # Configurações de busca
        self.job_keywords = os.getenv('JOB_KEYWORDS', 'python developer').split(',')
        self.job_location = os.getenv('JOB_LOCATION', 'São Paulo, Brazil')
        self.max_applications_per_day = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '5'))

        # Configurações de busca automatizada
        self.auto_apply = os.getenv('AUTO_APPLY', 'true').lower() == 'true'

        # Database simples com SQLite
        self.db_path = 'jobhunter.db'
        self.init_database()

        logger.info("🚀 JobHunter Bot inicializado")

    def init_database(self):
        """Inicializa database SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Tabela de vagas encontradas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    contact_email TEXT,
                    source_url TEXT,
                    platform TEXT,
                    found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    applied BOOLEAN DEFAULT FALSE,
                    applied_at DATETIME
                )
            ''')

            # Tabela de aplicações enviadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    contact_email TEXT NOT NULL,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            ''')

            conn.commit()
            conn.close()

            logger.info("✅ Database SQLite inicializada")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar database: {e}")

    def extract_emails_from_text(self, text: str) -> List[str]:
        """Extrai emails de um texto usando regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        # Filtra emails comuns que não são úteis
        filtered_emails = []
        for email in emails:
            if not any(domain in email.lower() for domain in [
                'noreply', 'no-reply', 'donotreply', 'linkedin.com',
                'twitter.com', 'x.com', 'facebook.com', 'instagram.com'
            ]):
                filtered_emails.append(email)

        return list(set(filtered_emails))  # Remove duplicatas

    def search_linkedin_jobs(self) -> List[Dict]:
        """Busca vagas no LinkedIn (versão simplificada usando requests)"""
        jobs = []

        try:
            # Simula busca de vagas do LinkedIn
            # Na versão real, usaria LinkedIn API ou scraping
            logger.info("🔍 Buscando vagas no LinkedIn...")

            # Exemplo de dados simulados (substitua por scraping real)
            sample_jobs = [
                {
                    'title': 'Desenvolvedor Python',
                    'company': 'TechCorp',
                    'location': 'São Paulo, SP',
                    'description': 'Vaga para desenvolvedor Python sênior. Contato: rh@techcorp.com',
                    'source_url': 'https://linkedin.com/job/123',
                    'platform': 'LinkedIn'
                },
                {
                    'title': 'Backend Developer',
                    'company': 'StartupXYZ',
                    'location': 'Remote',
                    'description': 'Desenvolvedor backend com Python/Django. Email para candidatura: jobs@startupxyz.com',
                    'source_url': 'https://linkedin.com/job/456',
                    'platform': 'LinkedIn'
                }
            ]

            for job_data in sample_jobs:
                # Extrai emails da descrição
                emails = self.extract_emails_from_text(job_data['description'])
                if emails:
                    job_data['contact_email'] = emails[0]
                    jobs.append(job_data)

            logger.info(f"✅ Encontradas {len(jobs)} vagas no LinkedIn")

        except Exception as e:
            logger.error(f"❌ Erro ao buscar vagas no LinkedIn: {e}")

        return jobs

    def search_x_jobs(self) -> List[Dict]:
        """Busca vagas no X/Twitter (versão simplificada)"""
        jobs = []

        try:
            logger.info("🔍 Buscando vagas no X/Twitter...")

            # Exemplo de dados simulados (substitua por Twitter API)
            sample_jobs = [
                {
                    'title': 'Python Developer - Remote',
                    'company': 'RemoteTech',
                    'location': 'Remote',
                    'description': 'Estamos contratando Python developer! Envie CV para: hiring@remotetech.com #job #python',
                    'source_url': 'https://x.com/post/789',
                    'platform': 'X'
                }
            ]

            for job_data in sample_jobs:
                emails = self.extract_emails_from_text(job_data['description'])
                if emails:
                    job_data['contact_email'] = emails[0]
                    jobs.append(job_data)

            logger.info(f"✅ Encontradas {len(jobs)} vagas no X")

        except Exception as e:
            logger.error(f"❌ Erro ao buscar vagas no X: {e}")

        return jobs

    def save_job_to_db(self, job_data: Dict) -> int:
        """Salva vaga no database e retorna o ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO jobs (title, company, location, description, contact_email, source_url, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data['title'],
                job_data['company'],
                job_data['location'],
                job_data['description'],
                job_data.get('contact_email'),
                job_data['source_url'],
                job_data['platform']
            ))

            job_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return job_id

        except Exception as e:
            logger.error(f"❌ Erro ao salvar vaga no DB: {e}")
            return None

    def create_application_email(self, job_data: Dict) -> tuple:
        """Cria email de candidatura personalizado"""
        subject = f"Candidatura para {job_data['title']} - {self.user_name}"

        body = f"""
Prezados,

Espero que estejam bem!

Meu nome é {self.user_name} e tenho grande interesse na vaga de {job_data['title']} na {job_data['company']}.

Com experiência em desenvolvimento de software e paixão por tecnologia, acredito que posso contribuir significativamente para a equipe. Anexo meu currículo para análise.

Principais qualificações:
• Desenvolvimento em Python, JavaScript e outras tecnologias
• Experiência com frameworks modernos
• Trabalho em equipe e metodologias ágeis
• Sempre buscando aprender e evoluir

Estou disponível para uma conversa e ansioso para conhecer mais sobre a oportunidade.

Atenciosamente,
{self.user_name}
{self.user_email}
{self.user_phone}
{self.user_linkedin}

---
Esta candidatura foi enviada através do JobHunter Bot em resposta à vaga: {job_data['source_url']}
        """.strip()

        return subject, body

    def send_email_with_cv(self, to_email: str, subject: str, body: str, job_id: int) -> bool:
        """Envia email com CV anexado"""
        try:
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject

            # Adiciona corpo do email
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Anexa CV se existir
            if os.path.exists(self.cv_file_path):
                with open(self.cv_file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(self.cv_file_path)}'
                )
                msg.attach(part)

            # Envia email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)

            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()

            # Registra aplicação no DB
            self.record_application(job_id, to_email, True, None)

            logger.info(f"✅ Email enviado para: {to_email}")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Erro ao enviar email para {to_email}: {error_msg}")

            # Registra erro no DB
            self.record_application(job_id, to_email, False, error_msg)
            return False

    def record_application(self, job_id: int, contact_email: str, success: bool, error_message: str):
        """Registra aplicação no database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO applications (job_id, contact_email, success, error_message)
                VALUES (?, ?, ?, ?)
            ''', (job_id, contact_email, success, error_message))

            # Marca vaga como aplicada
            if success:
                cursor.execute('''
                    UPDATE jobs SET applied = TRUE, applied_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (job_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Erro ao registrar aplicação: {e}")

    def get_applications_today(self) -> int:
        """Retorna número de aplicações enviadas hoje"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM applications
                WHERE DATE(sent_at) = DATE('now') AND success = TRUE
            ''')

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            logger.error(f"❌ Erro ao verificar aplicações hoje: {e}")
            return 0

    def process_jobs(self, jobs: List[Dict]):
        """Processa lista de vagas encontradas"""
        applications_today = self.get_applications_today()

        logger.info(f"📊 Aplicações enviadas hoje: {applications_today}/{self.max_applications_per_day}")

        for job_data in jobs:
            # Verifica limite diário
            if applications_today >= self.max_applications_per_day:
                logger.info(f"🛑 Limite diário de aplicações atingido ({self.max_applications_per_day})")
                break

            # Verifica se tem email de contato
            if not job_data.get('contact_email'):
                logger.warning(f"⚠️ Vaga sem email de contato: {job_data['title']}")
                continue

            # Salva vaga no DB
            job_id = self.save_job_to_db(job_data)
            if not job_id:
                continue

            logger.info(f"💼 Processando: {job_data['title']} - {job_data['company']}")

            # Se auto_apply está ativo, envia candidatura
            if self.auto_apply:
                subject, body = self.create_application_email(job_data)

                if self.send_email_with_cv(job_data['contact_email'], subject, body, job_id):
                    applications_today += 1
                    logger.info(f"✅ Candidatura enviada para: {job_data['company']}")

                    # Pequena pausa entre envios
                    time.sleep(10)
                else:
                    logger.error(f"❌ Falha ao enviar candidatura para: {job_data['company']}")

    def run_search_cycle(self):
        """Executa um ciclo completo de busca"""
        logger.info("🔄 Iniciando ciclo de busca de vagas...")

        all_jobs = []

        # Busca no LinkedIn
        linkedin_jobs = self.search_linkedin_jobs()
        all_jobs.extend(linkedin_jobs)

        # Busca no X
        x_jobs = self.search_x_jobs()
        all_jobs.extend(x_jobs)

        logger.info(f"📈 Total de vagas encontradas: {len(all_jobs)}")

        # Processa vagas
        if all_jobs:
            self.process_jobs(all_jobs)

        logger.info("✅ Ciclo de busca concluído")

    def get_stats(self) -> Dict:
        """Retorna estatísticas do bot"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total de vagas encontradas
            cursor.execute('SELECT COUNT(*) FROM jobs')
            total_jobs = cursor.fetchone()[0]

            # Total de aplicações enviadas
            cursor.execute('SELECT COUNT(*) FROM applications WHERE success = TRUE')
            total_applications = cursor.fetchone()[0]

            # Aplicações hoje
            cursor.execute('''
                SELECT COUNT(*) FROM applications
                WHERE DATE(sent_at) = DATE('now') AND success = TRUE
            ''')
            applications_today = cursor.fetchone()[0]

            # Últimas vagas
            cursor.execute('''
                SELECT title, company, found_at FROM jobs
                ORDER BY found_at DESC LIMIT 5
            ''')
            recent_jobs = cursor.fetchall()

            conn.close()

            return {
                'total_jobs': total_jobs,
                'total_applications': total_applications,
                'applications_today': applications_today,
                'max_daily': self.max_applications_per_day,
                'recent_jobs': recent_jobs
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

    def run_daemon(self, search_interval_hours: int = 4):
        """Executa o bot em modo daemon"""
        logger.info(f"🤖 JobHunter Bot iniciado em modo daemon (busca a cada {search_interval_hours}h)")

        while True:
            try:
                self.run_search_cycle()

                # Mostra estatísticas
                stats = self.get_stats()
                logger.info(f"📊 Stats: {stats['total_jobs']} vagas | {stats['total_applications']} aplicações | {stats['applications_today']}/{stats['max_daily']} hoje")

                # Aguarda próximo ciclo
                logger.info(f"⏰ Próxima busca em {search_interval_hours} horas...")
                time.sleep(search_interval_hours * 3600)

            except KeyboardInterrupt:
                logger.info("🛑 Bot interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no daemon: {e}")
                time.sleep(300)  # Aguarda 5min antes de tentar novamente

def main():
    """Função principal"""
    try:
        # Verifica se arquivo .env existe
        if not os.path.exists('.env'):
            logger.error("❌ Arquivo .env não encontrado. Copie .env.example para .env e configure.")
            return

        # Inicializa bot
        bot = SimpleJobHunter()

        # Verifica configurações essenciais
        if not all([bot.email_user, bot.email_password, bot.user_name]):
            logger.error("❌ Configurações de email não encontradas no .env")
            return

        if not os.path.exists(bot.cv_file_path):
            logger.warning(f"⚠️ Arquivo de CV não encontrado em: {bot.cv_file_path}")
            logger.info("📄 Crie uma pasta 'documents' e coloque seu CV.pdf lá")

        # Mostra configurações
        logger.info(f"👤 Usuário: {bot.user_name} <{bot.user_email}>")
        logger.info(f"📄 CV: {bot.cv_file_path}")
        logger.info(f"🔍 Palavras-chave: {', '.join(bot.job_keywords)}")
        logger.info(f"📍 Localização: {bot.job_location}")
        logger.info(f"🎯 Auto-aplicar: {'Sim' if bot.auto_apply else 'Não'}")
        logger.info(f"📊 Máx. aplicações/dia: {bot.max_applications_per_day}")

        # Executa uma busca de teste
        logger.info("\n🧪 Executando busca de teste...")
        bot.run_search_cycle()

        # Mostra estatísticas
        stats = bot.get_stats()
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"• Total de vagas encontradas: {stats.get('total_jobs', 0)}")
        print(f"• Total de aplicações enviadas: {stats.get('total_applications', 0)}")
        print(f"• Aplicações hoje: {stats.get('applications_today', 0)}/{stats.get('max_daily', 0)}")

        if stats.get('recent_jobs'):
            print(f"\n💼 VAGAS RECENTES:")
            for job in stats['recent_jobs']:
                print(f"• {job[0]} - {job[1]} ({job[2]})")

        # Pergunta se quer executar em modo daemon
        print(f"\n🤖 Deseja executar em modo daemon? (y/n): ", end="")
        response = input().strip().lower()

        if response in ['y', 'yes', 's', 'sim']:
            interval = int(os.getenv('SEARCH_INTERVAL_HOURS', '4'))
            bot.run_daemon(interval)
        else:
            logger.info("✅ Busca de teste concluída. Execute novamente para modo daemon.")

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    main()
