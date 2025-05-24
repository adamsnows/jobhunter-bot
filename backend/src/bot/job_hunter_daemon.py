"""
JobHunter Bot Daemon
Sistema daemon para busca e candidatura automática em vagas de emprego
"""

import os
import sys
import time
import signal
import logging
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.database import Database
from src.models.job import Job
from src.models.application import Application
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.scrapers.x_scraper import XScraper
from src.notifications.email_notifier import EmailNotifier
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.whatsapp_notifier import WhatsAppNotifier
from src.utils.job_matcher import JobMatcher
from src.utils.application_sender import ApplicationSender

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/jobhunter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DaemonConfig:
    """Configuração do daemon"""
    # Credenciais LinkedIn
    linkedin_email: str
    linkedin_password: str

    # Credenciais X/Twitter
    x_username: str
    x_password: str

    # Configurações de busca
    keywords: List[str]
    location: str
    experience_level: str
    job_type: str

    # Configurações de candidatura
    auto_apply: bool
    min_match_score: float
    max_applications_per_day: int

    # Configurações de agendamento
    search_interval_hours: int
    search_times: List[str]  # Ex: ["09:00", "14:00", "18:00"]

    # Notificações
    enable_email_notifications: bool
    enable_telegram_notifications: bool
    enable_whatsapp_notifications: bool

    # Modo de operação
    headless_mode: bool
    test_mode: bool

class JobHunterDaemon:
    """Daemon principal do JobHunter Bot"""

    def __init__(self, config_file: str = ".env"):
        self.config = self._load_config(config_file)
        self.running = False
        self.pid_file = "/tmp/jobhunter_daemon.pid"

        # Componentes
        self.db = Database()
        self.job_matcher = JobMatcher()
        self.application_sender = ApplicationSender()

        # Scrapers
        self.linkedin_scraper = None
        self.x_scraper = None

        # Notificadores
        self.email_notifier = None
        self.telegram_notifier = None
        self.whatsapp_notifier = None

        # Estatísticas
        self.stats = {
            'total_jobs_found': 0,
            'total_applications_sent': 0,
            'applications_today': 0,
            'last_search_time': None,
            'uptime_start': None
        }

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("🤖 JobHunter Daemon inicializado")

    def _load_config(self, config_file: str) -> DaemonConfig:
        """Carrega configuração do arquivo .env"""
        from dotenv import load_dotenv
        load_dotenv(config_file)

        # Keywords padrão se não especificadas
        keywords_str = os.getenv('JOB_KEYWORDS', 'python developer,software engineer,backend developer')
        keywords = [k.strip() for k in keywords_str.split(',')]

        # Horários de busca padrão
        search_times_str = os.getenv('SEARCH_TIMES', '09:00,14:00,18:00')
        search_times = [t.strip() for t in search_times_str.split(',')]

        return DaemonConfig(
            # LinkedIn
            linkedin_email=os.getenv('LINKEDIN_EMAIL', ''),
            linkedin_password=os.getenv('LINKEDIN_PASSWORD', ''),

            # X/Twitter
            x_username=os.getenv('X_USERNAME', ''),
            x_password=os.getenv('X_PASSWORD', ''),

            # Busca
            keywords=keywords,
            location=os.getenv('JOB_LOCATION', 'São Paulo, Brazil'),
            experience_level=os.getenv('EXPERIENCE_LEVEL', 'mid'),
            job_type=os.getenv('JOB_TYPE', 'full-time'),

            # Candidatura
            auto_apply=os.getenv('AUTO_APPLY', 'false').lower() == 'true',
            min_match_score=float(os.getenv('MIN_MATCH_SCORE', '70')),
            max_applications_per_day=int(os.getenv('MAX_APPLICATIONS_PER_DAY', '10')),

            # Agendamento
            search_interval_hours=int(os.getenv('SEARCH_INTERVAL_HOURS', '4')),
            search_times=search_times,

            # Notificações
            enable_email_notifications=os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() == 'true',
            enable_telegram_notifications=os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'false').lower() == 'true',
            enable_whatsapp_notifications=os.getenv('ENABLE_WHATSAPP_NOTIFICATIONS', 'false').lower() == 'true',

            # Modo
            headless_mode=os.getenv('HEADLESS_MODE', 'true').lower() == 'true',
            test_mode=os.getenv('TEST_MODE', 'false').lower() == 'true'
        )

    def start(self) -> None:
        """Inicia o daemon"""
        if self._is_already_running():
            logger.error("❌ Daemon já está rodando!")
            return

        self._write_pid_file()
        self.running = True
        self.stats['uptime_start'] = datetime.now()

        logger.info("🚀 Iniciando JobHunter Daemon...")

        # Inicializa componentes
        self._initialize_components()

        # Configura agendamentos
        self._setup_schedule()

        # Executa busca inicial (opcional)
        if not self.config.test_mode:
            logger.info("🔍 Executando busca inicial...")
            self._execute_job_search()

        # Loop principal
        self._main_loop()

    def stop(self) -> None:
        """Para o daemon"""
        logger.info("🛑 Parando JobHunter Daemon...")
        self.running = False

        # Fecha scrapers
        if self.linkedin_scraper:
            self.linkedin_scraper.close()
        if self.x_scraper:
            self.x_scraper.close()

        # Remove arquivo PID
        self._remove_pid_file()

        logger.info("✅ Daemon parado com sucesso")

    def _initialize_components(self) -> None:
        """Inicializa todos os componentes necessários"""
        try:
            # Inicializa banco de dados
            self.db.init_database()

            # Inicializa scrapers
            if self.config.linkedin_email and self.config.linkedin_password:
                self.linkedin_scraper = LinkedInScraper(
                    self.config.linkedin_email,
                    self.config.linkedin_password,
                    headless=self.config.headless_mode
                )
                logger.info("✅ LinkedIn scraper inicializado")

            if self.config.x_username and self.config.x_password:
                self.x_scraper = XScraper(
                    self.config.x_username,
                    self.config.x_password,
                    headless=self.config.headless_mode
                )
                logger.info("✅ X/Twitter scraper inicializado")

            # Inicializa notificadores
            if self.config.enable_email_notifications:
                self.email_notifier = EmailNotifier()
                logger.info("✅ Email notifier inicializado")

            if self.config.enable_telegram_notifications:
                self.telegram_notifier = TelegramNotifier()
                logger.info("✅ Telegram notifier inicializado")

            if self.config.enable_whatsapp_notifications:
                self.whatsapp_notifier = WhatsAppNotifier()
                logger.info("✅ WhatsApp notifier inicializado")

        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {str(e)}")
            raise

    def _setup_schedule(self) -> None:
        """Configura agendamentos de tarefas"""
        # Agendamento por horários específicos
        for search_time in self.config.search_times:
            schedule.every().day.at(search_time).do(self._execute_job_search)
            logger.info(f"📅 Busca agendada para {search_time}")

        # Agendamento por intervalo (backup)
        schedule.every(self.config.search_interval_hours).hours.do(self._execute_job_search)

        # Limpeza diária de logs antigos
        schedule.every().day.at("02:00").do(self._cleanup_old_logs)

        # Reset contador diário de candidaturas
        schedule.every().day.at("00:01").do(self._reset_daily_application_count)

        # Relatório diário
        schedule.every().day.at("23:00").do(self._send_daily_report)

    def _main_loop(self) -> None:
        """Loop principal do daemon"""
        logger.info("🔄 Entrando no loop principal...")

        try:
            while self.running:
                # Executa tarefas agendadas
                schedule.run_pending()

                # Sleep por 1 minuto
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("⚠️ Interrupção pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {str(e)}")
        finally:
            self.stop()

    def _execute_job_search(self) -> None:
        """Executa busca por vagas"""
        logger.info("🔍 Iniciando busca por vagas...")

        try:
            all_jobs = []

            # Busca no LinkedIn
            if self.linkedin_scraper:
                logger.info("🔗 Buscando no LinkedIn...")
                linkedin_jobs = self.linkedin_scraper.search_jobs(
                    keywords=self.config.keywords,
                    location=self.config.location,
                    experience_level=self.config.experience_level,
                    job_type=self.config.job_type
                )
                all_jobs.extend(linkedin_jobs)
                logger.info(f"✅ {len(linkedin_jobs)} vagas encontradas no LinkedIn")

            # Busca no X/Twitter
            if self.x_scraper:
                logger.info("🐦 Buscando no X/Twitter...")
                x_jobs = self.x_scraper.search_jobs(
                    keywords=self.config.keywords,
                    location=self.config.location
                )
                all_jobs.extend(x_jobs)
                logger.info(f"✅ {len(x_jobs)} vagas encontradas no X/Twitter")

            # Processa vagas encontradas
            if all_jobs:
                self._process_jobs(all_jobs)

            # Atualiza estatísticas
            self.stats['total_jobs_found'] += len(all_jobs)
            self.stats['last_search_time'] = datetime.now()

            logger.info(f"✅ Busca concluída. {len(all_jobs)} vagas encontradas")

        except Exception as e:
            logger.error(f"❌ Erro na busca por vagas: {str(e)}")
            self._send_error_notification(f"Erro na busca: {str(e)}")

    def _process_jobs(self, jobs: List[Job]) -> None:
        """Processa vagas encontradas"""
        logger.info(f"⚙️ Processando {len(jobs)} vagas...")

        new_jobs = 0
        applications_sent = 0

        for job in jobs:
            try:
                # Verifica se já existe no banco
                if self.db.job_exists(job.url):
                    continue

                # Salva no banco
                job_id = self.db.save_job(job)
                new_jobs += 1

                # Calcula score de compatibilidade
                match_score = self.job_matcher.calculate_match_score(job)
                job.match_score = match_score

                # Atualiza score no banco
                self.db.update_job_match_score(job_id, match_score)

                logger.info(f"💼 Nova vaga: {job.title} @ {job.company} (Score: {match_score}%)")

                # Decide se deve candidatar
                if self._should_apply(job):
                    if self._apply_to_job(job):
                        applications_sent += 1

            except Exception as e:
                logger.error(f"❌ Erro ao processar vaga {job.title}: {str(e)}")
                continue

        # Envia notificação sobre novas vagas
        if new_jobs > 0:
            self._send_new_jobs_notification(new_jobs, applications_sent)

        logger.info(f"✅ Processamento concluído: {new_jobs} novas vagas, {applications_sent} candidaturas")

    def _should_apply(self, job: Job) -> bool:
        """Decide se deve candidatar-se a uma vaga"""
        if not self.config.auto_apply:
            return False

        # Verifica score mínimo
        if job.match_score < self.config.min_match_score:
            return False

        # Verifica limite diário
        if self.stats['applications_today'] >= self.config.max_applications_per_day:
            logger.info("⚠️ Limite diário de candidaturas atingido")
            return False

        # Verifica se já se candidatou
        if self.db.application_exists(job.url):
            return False

        return True

    def _apply_to_job(self, job: Job) -> bool:
        """Envia candidatura para uma vaga"""
        try:
            logger.info(f"📨 Enviando candidatura para: {job.title} @ {job.company}")

            # Envia candidatura
            success = self.application_sender.send_application(job)

            if success:
                # Salva no banco
                application = Application(
                    job_url=job.url,
                    status='sent',
                    sent_at=datetime.now(),
                    email_subject=f"Candidatura para {job.title}",
                    response_received=False
                )

                self.db.save_application(application)

                self.stats['applications_today'] += 1
                self.stats['total_applications_sent'] += 1

                logger.info("✅ Candidatura enviada com sucesso!")
                return True
            else:
                logger.error("❌ Falha ao enviar candidatura")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao enviar candidatura: {str(e)}")
            return False

    def _send_new_jobs_notification(self, new_jobs: int, applications_sent: int) -> None:
        """Envia notificação sobre novas vagas"""
        message = f"""
🤖 JobHunter Bot - Relatório de Busca

📊 Resultados:
• {new_jobs} novas vagas encontradas
• {applications_sent} candidaturas enviadas
• Score médio: {self._calculate_average_score()}%

⏰ Última busca: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """.strip()

        # Email
        if self.email_notifier:
            self.email_notifier.send_notification(
                subject="JobHunter Bot - Novas Vagas",
                message=message
            )

        # Telegram
        if self.telegram_notifier:
            self.telegram_notifier.send_notification(message)

        # WhatsApp
        if self.whatsapp_notifier:
            self.whatsapp_notifier.send_notification(message)

    def _send_daily_report(self) -> None:
        """Envia relatório diário"""
        uptime = datetime.now() - self.stats['uptime_start'] if self.stats['uptime_start'] else timedelta(0)

        report = f"""
📊 JobHunter Bot - Relatório Diário

🎯 Estatísticas de Hoje:
• Candidaturas enviadas: {self.stats['applications_today']}
• Total de vagas encontradas: {self.stats['total_jobs_found']}
• Última busca: {self.stats['last_search_time'].strftime('%H:%M') if self.stats['last_search_time'] else 'N/A'}

💻 Sistema:
• Uptime: {str(uptime).split('.')[0]}
• Status: Ativo ✅

📅 Próxima busca: {self.config.search_times[0]} (amanhã)
        """.strip()

        if self.email_notifier:
            self.email_notifier.send_notification(
                subject="JobHunter Bot - Relatório Diário",
                message=report
            )

    def _send_error_notification(self, error: str) -> None:
        """Envia notificação de erro"""
        message = f"""
⚠️ JobHunter Bot - Erro

🔴 Erro detectado:
{error}

⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}

ℹ️ O bot continuará tentando nas próximas execuções.
        """.strip()

        if self.email_notifier:
            self.email_notifier.send_notification(
                subject="JobHunter Bot - Erro",
                message=message
            )

    def _calculate_average_score(self) -> float:
        """Calcula score médio das vagas do dia"""
        try:
            today_jobs = self.db.get_jobs_by_date(datetime.now().date())
            if not today_jobs:
                return 0.0

            scores = [job.match_score for job in today_jobs if job.match_score]
            return sum(scores) / len(scores) if scores else 0.0

        except Exception:
            return 0.0

    def _reset_daily_application_count(self) -> None:
        """Reseta contador diário de candidaturas"""
        self.stats['applications_today'] = 0
        logger.info("🔄 Contador diário de candidaturas resetado")

    def _cleanup_old_logs(self) -> None:
        """Remove logs antigos"""
        try:
            log_file = 'data/logs/jobhunter.log'
            if os.path.exists(log_file):
                # Mantém apenas últimas 1000 linhas
                with open(log_file, 'r') as f:
                    lines = f.readlines()

                if len(lines) > 1000:
                    with open(log_file, 'w') as f:
                        f.writelines(lines[-1000:])

                    logger.info("🧹 Logs antigos removidos")
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de logs: {str(e)}")

    def _is_already_running(self) -> bool:
        """Verifica se o daemon já está rodando"""
        if not os.path.exists(self.pid_file):
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Verifica se o processo existe
            os.kill(pid, 0)  # Não mata, apenas verifica
            return True
        except (OSError, ValueError):
            # Processo não existe, remove arquivo PID
            self._remove_pid_file()
            return False

    def _write_pid_file(self) -> None:
        """Escreve arquivo PID"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"❌ Erro ao escrever arquivo PID: {str(e)}")

    def _remove_pid_file(self) -> None:
        """Remove arquivo PID"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except Exception as e:
            logger.error(f"❌ Erro ao remover arquivo PID: {str(e)}")

    def _signal_handler(self, signum, frame) -> None:
        """Handler para sinais do sistema"""
        logger.info(f"📡 Sinal recebido: {signum}")
        self.stop()

    def get_status(self) -> Dict:
        """Retorna status atual do daemon"""
        uptime = datetime.now() - self.stats['uptime_start'] if self.stats['uptime_start'] else timedelta(0)

        return {
            'running': self.running,
            'uptime': str(uptime).split('.')[0],
            'stats': self.stats,
            'config': {
                'keywords': self.config.keywords,
                'location': self.config.location,
                'auto_apply': self.config.auto_apply,
                'search_times': self.config.search_times
            }
        }

def main():
    """Função principal para execução do daemon"""
    import argparse

    parser = argparse.ArgumentParser(description='JobHunter Bot Daemon')
    parser.add_argument('--config', default='.env', help='Arquivo de configuração')
    parser.add_argument('--test', action='store_true', help='Modo de teste')

    args = parser.parse_args()

    try:
        daemon = JobHunterDaemon(args.config)

        if args.test:
            daemon.config.test_mode = True
            logger.info("🧪 Executando em modo de teste")

        daemon.start()

    except KeyboardInterrupt:
        logger.info("⚠️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()