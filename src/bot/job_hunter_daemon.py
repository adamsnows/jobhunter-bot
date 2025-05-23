"""
JobHunter Bot Daemon
Sistema principal que roda 24/7 procurando vagas e enviando CVs automaticamente
"""

import os
import sys
import time
import signal
import json
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent))

from models.database import Database
from models.job import Job
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.x_scraper import XScraper
from notifications.whatsapp_notifier import WhatsAppNotifier
from email.email_sender import EmailSender
from utils.text_analyzer import TextAnalyzer


class JobHunterDaemon:
    """Daemon principal do JobHunter Bot"""

    def __init__(self):
        """Inicializa o daemon"""
        self.is_running = False
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Sao_Paulo'))
        self.stats = {
            'jobs_found_today': 0,
            'applications_sent_today': 0,
            'last_search': None,
            'total_jobs_found': 0,
            'total_applications_sent': 0,
            'uptime_start': datetime.now()
        }

        # PID file para controle do daemon
        self.pid_file = Path('./data/jobhunter.pid')
        self.status_file = Path('./data/status.json')

        # Inicializa componentes
        self.db = Database()
        self.linkedin_scraper = LinkedInScraper()
        self.x_scraper = XScraper()
        self.whatsapp_notifier = WhatsAppNotifier()
        self.email_sender = EmailSender()
        self.text_analyzer = TextAnalyzer()

        # Configurações do .env
        self.search_interval = int(os.getenv('SEARCH_INTERVAL_MINUTES', 30))
        self.max_applications_per_day = int(os.getenv('MAX_APPLICATIONS_PER_DAY', 10))
        self.min_match_score = float(os.getenv('MIN_JOB_MATCH_SCORE', 0.7))
        self.auto_apply_enabled = os.getenv('AUTO_APPLY_ENABLED', 'false').lower() == 'true'

        # Setup de logs
        self._setup_logging()

        # Signal handlers para shutdown graceful
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_logging(self):
        """Configura o sistema de logs"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', './data/logs/jobhunter.log')

        # Remove handlers existentes
        logger.remove()

        # Console log
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level
        )

        # File log
        logger.add(
            log_file,
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level
        )

    def start(self):
        """Inicia o daemon"""
        if self.is_running:
            logger.warning("Daemon já está rodando!")
            return False

        logger.info("🤖 Iniciando JobHunter Bot Daemon...")

        # Salva PID
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

        self.is_running = True
        self.stats['uptime_start'] = datetime.now()

        # Agenda tarefas
        self._schedule_tasks()

        # Inicia scheduler
        self.scheduler.start()

        # Primeira busca imediata
        threading.Thread(target=self.search_jobs, daemon=True).start()

        # Notifica início
        self.whatsapp_notifier.send_message("🤖 JobHunter Bot iniciado! Procurando vagas...")

        logger.info("✅ Daemon iniciado com sucesso!")

        try:
            # Loop principal
            while self.is_running:
                self._update_status()
                time.sleep(10)  # Check a cada 10 segundos
        except KeyboardInterrupt:
            logger.info("Recebido sinal de interrupção...")
        finally:
            self.stop()

        return True

    def stop(self):
        """Para o daemon"""
        if not self.is_running:
            logger.warning("Daemon não está rodando!")
            return False

        logger.info("🛑 Parando JobHunter Bot Daemon...")

        self.is_running = False

        # Para scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()

        # Notifica parada
        uptime = datetime.now() - self.stats['uptime_start']
        self.whatsapp_notifier.send_message(
            f"🛑 JobHunter Bot parado!\n"
            f"⏱️ Uptime: {str(uptime).split('.')[0]}\n"
            f"📊 Total encontrado: {self.stats['total_jobs_found']} vagas\n"
            f"📧 Total enviado: {self.stats['total_applications_sent']} candidaturas"
        )

        logger.info("✅ Daemon parado com sucesso!")
        return True

    def _schedule_tasks(self):
        """Agenda as tarefas periódicas"""
        # Busca de vagas a cada X minutos
        self.scheduler.add_job(
            func=self.search_jobs,
            trigger=IntervalTrigger(minutes=self.search_interval),
            id='search_jobs',
            name='Busca de Vagas',
            replace_existing=True
        )

        # Reset de contadores diários à meia-noite
        self.scheduler.add_job(
            func=self._reset_daily_stats,
            trigger='cron',
            hour=0,
            minute=0,
            id='reset_daily_stats',
            name='Reset Estatísticas Diárias',
            replace_existing=True
        )

        # Resumo diário às 18h
        self.scheduler.add_job(
            func=self._send_daily_summary,
            trigger='cron',
            hour=18,
            minute=0,
            id='daily_summary',
            name='Resumo Diário',
            replace_existing=True
        )

        # Backup do banco a cada 6 horas
        self.scheduler.add_job(
            func=self._backup_database,
            trigger=IntervalTrigger(hours=6),
            id='backup_db',
            name='Backup Banco de Dados',
            replace_existing=True
        )

    def search_jobs(self):
        """Busca vagas em todas as plataformas"""
        if not self.is_running:
            return

        logger.info("🔍 Iniciando busca de vagas...")
        self.stats['last_search'] = datetime.now()

        new_jobs = []

        try:
            # LinkedIn
            logger.info("📍 Buscando no LinkedIn...")
            linkedin_jobs = self.linkedin_scraper.search_jobs()
            new_jobs.extend(linkedin_jobs)
            logger.info(f"LinkedIn: {len(linkedin_jobs)} vagas encontradas")

            # X (Twitter)
            logger.info("📍 Buscando no X (Twitter)...")
            x_jobs = self.x_scraper.search_jobs()
            new_jobs.extend(x_jobs)
            logger.info(f"X: {len(x_jobs)} vagas encontradas")

            # Processa vagas encontradas
            if new_jobs:
                processed_jobs = self._process_jobs(new_jobs)

                # Aplica filtros e candidatura automática
                if self.auto_apply_enabled:
                    self._auto_apply(processed_jobs)

                logger.info(f"✅ Total processado: {len(processed_jobs)} vagas")

                # Atualiza estatísticas
                self.stats['jobs_found_today'] += len(processed_jobs)
                self.stats['total_jobs_found'] += len(processed_jobs)

                # Notifica sobre vagas high-match
                high_match_jobs = [job for job in processed_jobs if job.get('match_score', 0) >= 0.8]
                if high_match_jobs:
                    self._notify_high_match_jobs(high_match_jobs)

            else:
                logger.info("Nenhuma vaga nova encontrada")

        except Exception as e:
            logger.error(f"❌ Erro na busca de vagas: {str(e)}")
            self.whatsapp_notifier.send_error_notification(f"Erro na busca: {str(e)}")

    def _process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processa e filtra vagas encontradas"""
        processed = []

        for job_data in jobs:
            try:
                # Verifica se já existe no banco
                existing_job = self.db.get_job_by_url(job_data.get('url', ''))
                if existing_job:
                    continue

                # Calcula match score
                match_score = self.text_analyzer.calculate_match_score(
                    job_data.get('description', ''),
                    job_data.get('title', '')
                )
                job_data['match_score'] = match_score

                # Salva no banco
                job = Job(**job_data)
                self.db.save_job(job)

                processed.append(job_data)

            except Exception as e:
                logger.error(f"Erro processando vaga: {str(e)}")
                continue

        return processed

    def _auto_apply(self, jobs: List[Dict[str, Any]]):
        """Candidatura automática para vagas que atendem critérios"""
        if self.stats['applications_sent_today'] >= self.max_applications_per_day:
            logger.info(f"Limite diário de candidaturas atingido ({self.max_applications_per_day})")
            return

        # Filtra vagas elegíveis
        eligible_jobs = [
            job for job in jobs
            if job.get('match_score', 0) >= self.min_match_score
        ]

        # Ordena por match score
        eligible_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        for job in eligible_jobs:
            if self.stats['applications_sent_today'] >= self.max_applications_per_day:
                break

            try:
                success = self.email_sender.send_application(job)

                if success:
                    self.stats['applications_sent_today'] += 1
                    self.stats['total_applications_sent'] += 1

                    logger.info(f"✅ Candidatura enviada: {job.get('title')} - {job.get('company')}")

                    # Notifica
                    self.whatsapp_notifier.send_application_notification(job, 'sent')
                else:
                    logger.warning(f"❌ Falha ao enviar candidatura: {job.get('title')}")

            except Exception as e:
                logger.error(f"Erro enviando candidatura: {str(e)}")
                continue

    def _notify_high_match_jobs(self, jobs: List[Dict[str, Any]]):
        """Notifica sobre vagas com alto match"""
        for job in jobs[:3]:  # Máximo 3 notificações por vez
            self.whatsapp_notifier.send_job_notification(job)

    def _reset_daily_stats(self):
        """Reset estatísticas diárias"""
        self.stats['jobs_found_today'] = 0
        self.stats['applications_sent_today'] = 0
        logger.info("📊 Estatísticas diárias resetadas")

    def _send_daily_summary(self):
        """Envia resumo diário"""
        avg_score = self.db.get_average_match_score_today()
        self.whatsapp_notifier.send_daily_summary(
            self.stats['jobs_found_today'],
            self.stats['applications_sent_today'],
            avg_score or 0
        )

    def _backup_database(self):
        """Backup do banco de dados"""
        try:
            backup_path = f"./data/backups/jobhunter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            import shutil
            shutil.copy2('./data/jobs.db', backup_path)

            logger.info(f"💾 Backup criado: {backup_path}")
        except Exception as e:
            logger.error(f"Erro no backup: {str(e)}")

    def _update_status(self):
        """Atualiza arquivo de status"""
        status = {
            'is_running': self.is_running,
            'pid': os.getpid(),
            'uptime_start': self.stats['uptime_start'].isoformat(),
            'last_search': self.stats['last_search'].isoformat() if self.stats['last_search'] else None,
            'stats': self.stats.copy()
        }
        status['stats']['uptime_start'] = status['stats']['uptime_start'].isoformat()

        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)

    def _signal_handler(self, signum, frame):
        """Handler para sinais do sistema"""
        logger.info(f"Recebido sinal {signum}, parando daemon...")
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do daemon"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                return json.load(f)
        return {'is_running': False}


def main():
    """Função principal para teste do daemon"""
    daemon = JobHunterDaemon()
    daemon.start()


if __name__ == "__main__":
    main()
