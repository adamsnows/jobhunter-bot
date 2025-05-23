"""
JobHunter Bot Web Dashboard
Dashboard web local para monitorar e controlar o bot
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import psutil
import signal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.models.database import get_database_url
from src.models.job import Job
from src.models.application import Application

app = Flask(__name__)
app.secret_key = 'jobhunter-bot-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DashboardController:
    """Controlador do dashboard"""

    def __init__(self):
        self.daemon_pid_file = '/tmp/jobhunter_daemon.pid'

    def is_daemon_running(self):
        """Verifica se o daemon está rodando"""
        if not os.path.exists(self.daemon_pid_file):
            return False

        try:
            with open(self.daemon_pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Verifica se o processo existe
            return psutil.pid_exists(pid)
        except:
            return False

    def start_daemon(self):
        """Inicia o daemon"""
        if self.is_daemon_running():
            return False, "Daemon já está rodando"

        try:
            # Importa e inicia o daemon
            from src.bot.job_hunter_daemon import JobHunterDaemon
            daemon = JobHunterDaemon()
            daemon.start()
            return True, "Daemon iniciado com sucesso"
        except Exception as e:
            return False, f"Erro ao iniciar daemon: {str(e)}"

    def stop_daemon(self):
        """Para o daemon"""
        if not self.is_daemon_running():
            return False, "Daemon não está rodando"

        try:
            with open(self.daemon_pid_file, 'r') as f:
                pid = int(f.read().strip())

            os.kill(pid, signal.SIGTERM)

            # Remove o arquivo PID
            if os.path.exists(self.daemon_pid_file):
                os.remove(self.daemon_pid_file)

            return True, "Daemon parado com sucesso"
        except Exception as e:
            return False, f"Erro ao parar daemon: {str(e)}"

    def get_stats(self):
        """Obtém estatísticas do bot"""
        try:
            # Conecta ao banco
            conn = sqlite3.connect('data/jobs.db')
            cursor = conn.cursor()

            # Estatísticas gerais
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM applications")
            total_applications = cursor.fetchone()[0] or 0

            # Estatísticas de hoje
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE DATE(created_at) = ?", (today,))
            jobs_today = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM applications WHERE DATE(sent_at) = ?", (today,))
            applications_today = cursor.fetchone()[0] or 0

            # Taxa de sucesso
            cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'sent'")
            successful_apps = cursor.fetchone()[0] or 0

            success_rate = (successful_apps / total_applications * 100) if total_applications > 0 else 0

            # Últimas vagas
            cursor.execute("""
                SELECT title, company, location, match_score, created_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent_jobs = cursor.fetchall()

            # Últimas candidaturas
            cursor.execute("""
                SELECT j.title, j.company, a.status, a.sent_at
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                ORDER BY a.sent_at DESC
                LIMIT 10
            """)
            recent_applications = cursor.fetchall()

            conn.close()

            return {
                'total_jobs': total_jobs,
                'total_applications': total_applications,
                'jobs_today': jobs_today,
                'applications_today': applications_today,
                'success_rate': round(success_rate, 1),
                'recent_jobs': recent_jobs,
                'recent_applications': recent_applications,
                'daemon_running': self.is_daemon_running()
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_jobs': 0,
                'total_applications': 0,
                'jobs_today': 0,
                'applications_today': 0,
                'success_rate': 0,
                'recent_jobs': [],
                'recent_applications': [],
                'daemon_running': False
            }

# Inicializa o controlador
dashboard = DashboardController()

@app.route('/')
def index():
    """Página principal do dashboard"""
    stats = dashboard.get_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/stats')
def api_stats():
    """API para obter estatísticas"""
    return jsonify(dashboard.get_stats())

@app.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """API para iniciar o daemon"""
    success, message = dashboard.start_daemon()
    return jsonify({'success': success, 'message': message})

@app.route('/api/daemon/stop', methods=['POST'])
def stop_daemon():
    """API para parar o daemon"""
    success, message = dashboard.stop_daemon()
    return jsonify({'success': success, 'message': message})

@app.route('/api/daemon/status')
def daemon_status():
    """API para verificar status do daemon"""
    return jsonify({'running': dashboard.is_daemon_running()})

@app.route('/jobs')
def jobs():
    """Página de vagas encontradas"""
    try:
        conn = sqlite3.connect('data/jobs.db')
        cursor = conn.cursor()

        # Busca vagas com paginação
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        cursor.execute("""
            SELECT id, title, company, location, salary, match_score, url, created_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        jobs_data = cursor.fetchall()

        # Total de vagas para paginação
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0] or 0

        conn.close()

        return render_template('jobs.html',
                             jobs=jobs_data,
                             page=page,
                             total=total,
                             per_page=per_page)
    except Exception as e:
        flash(f'Erro ao carregar vagas: {str(e)}', 'error')
        return render_template('jobs.html', jobs=[], page=1, total=0, per_page=20)

@app.route('/applications')
def applications():
    """Página de candidaturas enviadas"""
    try:
        conn = sqlite3.connect('data/jobs.db')
        cursor = conn.cursor()

        # Busca candidaturas com paginação
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        cursor.execute("""
            SELECT a.id, j.title, j.company, a.status, a.sent_at, a.email_subject
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.sent_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        apps_data = cursor.fetchall()

        # Total de candidaturas para paginação
        cursor.execute("SELECT COUNT(*) FROM applications")
        total = cursor.fetchone()[0] or 0

        conn.close()

        return render_template('applications.html',
                             applications=apps_data,
                             page=page,
                             total=total,
                             per_page=per_page)
    except Exception as e:
        flash(f'Erro ao carregar candidaturas: {str(e)}', 'error')
        return render_template('applications.html', applications=[], page=1, total=0, per_page=20)

@app.route('/settings')
def settings():
    """Página de configurações"""
    # Carrega configurações do .env
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    except:
        pass

    return render_template('settings.html', env_vars=env_vars)

@app.route('/logs')
def logs():
    """Página de logs"""
    try:
        log_file = 'data/logs/jobhunter.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()[-100:]  # Últimas 100 linhas
        else:
            logs = ['Log file not found']

        return render_template('logs.html', logs=logs)
    except Exception as e:
        return render_template('logs.html', logs=[f'Error reading logs: {str(e)}'])

if __name__ == '__main__':
    # Cria as tabelas se não existirem
    with app.app_context():
        try:
            db.create_all()
        except:
            pass

    print("🚀 JobHunter Bot Dashboard iniciado!")
    print("📊 Acesse: http://localhost:5000")
    print("🔧 Ctrl+C para parar")

    app.run(host='0.0.0.0', port=5000, debug=True)
