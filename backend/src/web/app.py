"""
JobHunter Bot Flask API
API REST para comunicação com o frontend Next.js
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import psutil
import signal
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.models.database import get_database_url
from src.models.job import Job
from src.models.application import Application

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'jobhunter-bot-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Habilitar CORS para comunicação com Next.js
CORS(app, origins=['http://localhost:3000'])

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

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Dashboard stats API
@app.route('/api/stats')
def api_stats():
    """API para obter estatísticas do dashboard"""
    try:
        stats = dashboard.get_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Daemon control endpoints
@app.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """API para iniciar o daemon"""
    try:
        success, message = dashboard.start_daemon()
        return jsonify({
            'success': success, 
            'message': message
        })
    except Exception as e:
        logger.error(f"Error starting daemon: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/daemon/stop', methods=['POST'])
def stop_daemon():
    """API para parar o daemon"""
    try:
        success, message = dashboard.stop_daemon()
        return jsonify({
            'success': success, 
            'message': message
        })
    except Exception as e:
        logger.error(f"Error stopping daemon: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/daemon/status')
def daemon_status():
    """API para verificar status do daemon"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'running': dashboard.is_daemon_running()
            }
        })
    except Exception as e:
        logger.error(f"Error checking daemon status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Jobs endpoints
@app.route('/api/jobs')
def api_jobs():
    """API para obter lista de vagas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        # Validação
        if per_page > 100:
            per_page = 100
        
        conn = sqlite3.connect('data/jobs.db')
        cursor = conn.cursor()
        
        # Query base
        base_query = """
            SELECT id, title, company, location, salary, match_score, url, created_at
            FROM jobs 
        """
        
        # Adicionar filtro de busca se fornecido
        params = []
        if search:
            base_query += " WHERE title LIKE ? OR company LIKE ? OR location LIKE ?"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        # Adicionar ordenação e paginação
        offset = (page - 1) * per_page
        query = base_query + " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        jobs_data = cursor.fetchall()
        
        # Total de vagas para paginação
        count_query = "SELECT COUNT(*) FROM jobs"
        count_params = []
        if search:
            count_query += " WHERE title LIKE ? OR company LIKE ? OR location LIKE ?"
            count_params = [search_term, search_term, search_term]
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Formatar dados
        jobs = []
        for job in jobs_data:
            jobs.append({
                'id': job[0],
                'title': job[1],
                'company': job[2],
                'location': job[3],
                'salary': job[4],
                'match_score': job[5],
                'url': job[6],
                'created_at': job[7]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'jobs': jobs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jobs/<int:job_id>')
def api_job_detail(job_id):
    """API para obter detalhes de uma vaga específica"""
    try:
        conn = sqlite3.connect('data/jobs.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, company, location, salary, description, 
                   requirements, match_score, url, created_at
            FROM jobs 
            WHERE id = ?
        """, (job_id,))
        
        job_data = cursor.fetchone()
        conn.close()
        
        if not job_data:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        job = {
            'id': job_data[0],
            'title': job_data[1],
            'company': job_data[2],
            'location': job_data[3],
            'salary': job_data[4],
            'description': job_data[5],
            'requirements': job_data[6],
            'match_score': job_data[7],
            'url': job_data[8],
            'created_at': job_data[9]
        }
        
        return jsonify({
            'success': True,
            'data': job
        })
    except Exception as e:
        logger.error(f"Error getting job detail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Applications endpoints
@app.route('/api/applications')
def api_applications():
    """API para obter lista de candidaturas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        
        # Validação
        if per_page > 100:
            per_page = 100
        
        conn = sqlite3.connect('data/jobs.db')
        cursor = conn.cursor()
        
        # Query base
        base_query = """
            SELECT a.id, j.title, j.company, a.status, a.sent_at, 
                   a.email_subject, a.response_received, j.location
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
        """
        
        # Adicionar filtro de status se fornecido
        params = []
        if status_filter:
            base_query += " WHERE a.status = ?"
            params.append(status_filter)
        
        # Adicionar ordenação e paginação
        offset = (page - 1) * per_page
        query = base_query + " ORDER BY a.sent_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        apps_data = cursor.fetchall()
        
        # Total de candidaturas para paginação
        count_query = "SELECT COUNT(*) FROM applications a"
        count_params = []
        if status_filter:
            count_query += " WHERE a.status = ?"
            count_params = [status_filter]
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Formatar dados
        applications = []
        for app in apps_data:
            applications.append({
                'id': app[0],
                'job_title': app[1],
                'company': app[2],
                'status': app[3],
                'sent_at': app[4],
                'email_subject': app[5],
                'response_received': app[6],
                'location': app[7]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'applications': applications,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Settings endpoints
@app.route('/api/settings')
def api_settings():
    """API para obter configurações"""
    try:
        # Carrega configurações do .env (sem valores sensíveis)
        env_vars = {}
        sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API_KEY']
        
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        # Mascarar valores sensíveis
                        if any(sensitive in key.upper() for sensitive in sensitive_keys):
                            env_vars[key] = '***' if value else ''
                        else:
                            env_vars[key] = value
        except FileNotFoundError:
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'environment': env_vars
            }
        })
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings', methods=['PUT'])
def api_update_settings():
    """API para atualizar configurações"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Aqui você implementaria a lógica para atualizar configurações
        # Por enquanto, apenas retorna sucesso
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Logs endpoints
@app.route('/api/logs')
def api_logs():
    """API para obter logs"""
    try:
        lines = request.args.get('lines', 100, type=int)
        level = request.args.get('level', 'all')
        
        # Validação
        if lines > 1000:
            lines = 1000
        
        log_file = 'data/logs/jobhunter.log'
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                all_logs = f.readlines()
                # Pegar as últimas N linhas
                recent_logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
                
                # Filtrar por nível se especificado
                for log_line in recent_logs:
                    if level == 'all' or level.upper() in log_line:
                        logs.append({
                            'timestamp': log_line[:19] if len(log_line) > 19 else '',
                            'message': log_line.strip(),
                            'level': 'INFO'  # Simplificado por enquanto
                        })
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'total': len(logs)
            }
        })
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Cria as tabelas se não existirem
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logger.warning(f"Database initialization warning: {str(e)}")
    
    logger.info("🚀 JobHunter Bot API iniciada!")
    logger.info("📡 API endpoints disponíveis em: http://localhost:5000/api")
    logger.info("🔧 Ctrl+C para parar")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
