"""
Configuração e gerenciamento do banco de dados
"""
import sqlite3
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import json
from datetime import datetime

from .job import Job, JobSource, JobStatus
from .application import Application, ApplicationStatus, ApplicationMethod


class Database:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Inicializa as tabelas do banco"""
        with self.get_connection() as conn:
            # Tabela de vagas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    requirements TEXT,
                    salary_min REAL,
                    salary_max REAL,
                    salary_currency TEXT DEFAULT 'BRL',
                    url TEXT,
                    contact_email TEXT,
                    source TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    remote_ok BOOLEAN DEFAULT FALSE,
                    contract_type TEXT,
                    required_skills TEXT, -- JSON array
                    nice_to_have_skills TEXT, -- JSON array
                    match_score REAL,
                    posted_date TEXT,
                    found_date TEXT NOT NULL,
                    applied_date TEXT,
                    tags TEXT, -- JSON array
                    experience_level TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de candidaturas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    recipient_email TEXT,
                    subject TEXT,
                    message_body TEXT,
                    cover_letter TEXT,
                    resume_sent BOOLEAN DEFAULT FALSE,
                    portfolio_sent BOOLEAN DEFAULT FALSE,
                    cover_letter_sent BOOLEAN DEFAULT FALSE,
                    attachments TEXT, -- JSON array
                    created_date TEXT NOT NULL,
                    sent_date TEXT,
                    delivered_date TEXT,
                    read_date TEXT,
                    response_date TEXT,
                    response_received BOOLEAN DEFAULT FALSE,
                    response_content TEXT,
                    response_type TEXT,
                    follow_up_count INTEGER DEFAULT 0,
                    last_follow_up_date TEXT,
                    next_follow_up_date TEXT,
                    automated BOOLEAN DEFAULT TRUE,
                    match_score_at_application REAL,
                    notes TEXT,
                    tags TEXT, -- JSON array
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs (match_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_found_date ON jobs (found_date)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications (job_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_sent_date ON applications (sent_date)")
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # === MÉTODOS PARA JOBS ===
    
    def save_job(self, job: Job) -> bool:
        """Salva ou atualiza uma vaga"""
        try:
            with self.get_connection() as conn:
                job_dict = job.to_dict()
                
                # Converter listas para JSON
                job_dict['required_skills'] = json.dumps(job_dict['required_skills'])
                job_dict['nice_to_have_skills'] = json.dumps(job_dict['nice_to_have_skills'])
                job_dict['tags'] = json.dumps(job_dict['tags'])
                
                # Verificar se já existe
                existing = conn.execute("SELECT id FROM jobs WHERE id = ?", (job.id,)).fetchone()
                
                if existing:
                    # Update
                    job_dict['updated_at'] = datetime.now().isoformat()
                    placeholders = ', '.join([f"{k} = ?" for k in job_dict.keys() if k != 'id'])
                    values = [v for k, v in job_dict.items() if k != 'id'] + [job.id]
                    
                    conn.execute(f"UPDATE jobs SET {placeholders} WHERE id = ?", values)
                else:
                    # Insert
                    job_dict['created_at'] = datetime.now().isoformat()
                    job_dict['updated_at'] = job_dict['created_at']
                    
                    placeholders = ', '.join(['?' for _ in job_dict])
                    columns = ', '.join(job_dict.keys())
                    
                    conn.execute(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", list(job_dict.values()))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao salvar vaga: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Busca uma vaga por ID"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row:
                return self._row_to_job(row)
        return None
    
    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """Busca vagas com filtros opcionais"""
        query = "SELECT * FROM jobs"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
        
        query += " ORDER BY found_date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def search_jobs(self, **filters) -> List[Job]:
        """Busca vagas com filtros avançados"""
        conditions = []
        params = []
        
        if filters.get('company'):
            conditions.append("company LIKE ?")
            params.append(f"%{filters['company']}%")
        
        if filters.get('title'):
            conditions.append("title LIKE ?")
            params.append(f"%{filters['title']}%")
        
        if filters.get('location'):
            conditions.append("location LIKE ?")
            params.append(f"%{filters['location']}%")
        
        if filters.get('min_match_score'):
            conditions.append("match_score >= ?")
            params.append(filters['min_match_score'])
        
        if filters.get('source'):
            conditions.append("source = ?")
            params.append(filters['source'])
        
        if filters.get('remote_ok'):
            conditions.append("remote_ok = ?")
            params.append(filters['remote_ok'])
        
        query = "SELECT * FROM jobs"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY match_score DESC, found_date DESC"
        
        if filters.get('limit'):
            query += " LIMIT ?"
            params.append(filters['limit'])
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def job_exists(self, url: str) -> bool:
        """Verifica se uma vaga já existe pelo URL"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
            return result is not None
    
    def _row_to_job(self, row) -> Job:
        """Converte linha do banco para objeto Job"""
        data = dict(row)
        
        # Converter JSON arrays de volta para listas
        data['required_skills'] = json.loads(data['required_skills']) if data['required_skills'] else []
        data['nice_to_have_skills'] = json.loads(data['nice_to_have_skills']) if data['nice_to_have_skills'] else []
        data['tags'] = json.loads(data['tags']) if data['tags'] else []
        
        # Remover campos do banco que não estão no modelo
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        return Job.from_dict(data)
    
    # === MÉTODOS PARA APPLICATIONS ===
    
    def save_application(self, application: Application) -> bool:
        """Salva ou atualiza uma candidatura"""
        try:
            with self.get_connection() as conn:
                app_dict = application.to_dict()
                
                # Converter lista para JSON
                app_dict['attachments'] = json.dumps(app_dict['attachments'])
                app_dict['tags'] = json.dumps(app_dict['tags'])
                
                # Verificar se já existe
                existing = conn.execute("SELECT id FROM applications WHERE id = ?", (application.id,)).fetchone()
                
                if existing:
                    # Update
                    app_dict['updated_at'] = datetime.now().isoformat()
                    placeholders = ', '.join([f"{k} = ?" for k in app_dict.keys() if k != 'id'])
                    values = [v for k, v in app_dict.items() if k != 'id'] + [application.id]
                    
                    conn.execute(f"UPDATE applications SET {placeholders} WHERE id = ?", values)
                else:
                    # Insert
                    app_dict['created_at'] = datetime.now().isoformat()
                    app_dict['updated_at'] = app_dict['created_at']
                    
                    placeholders = ', '.join(['?' for _ in app_dict])
                    columns = ', '.join(app_dict.keys())
                    
                    conn.execute(f"INSERT INTO applications ({columns}) VALUES ({placeholders})", list(app_dict.values()))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao salvar candidatura: {e}")
            return False
    
    def get_application(self, app_id: str) -> Optional[Application]:
        """Busca uma candidatura por ID"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
            if row:
                return self._row_to_application(row)
        return None
    
    def get_applications_for_job(self, job_id: str) -> List[Application]:
        """Busca candidaturas de uma vaga específica"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM applications WHERE job_id = ? ORDER BY created_date DESC", 
                (job_id,)
            ).fetchall()
            return [self._row_to_application(row) for row in rows]
    
    def get_applications(self, status: Optional[ApplicationStatus] = None, limit: Optional[int] = None) -> List[Application]:
        """Busca candidaturas com filtros opcionais"""
        query = "SELECT * FROM applications"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_application(row) for row in rows]
    
    def _row_to_application(self, row) -> Application:
        """Converte linha do banco para objeto Application"""
        data = dict(row)
        
        # Converter JSON arrays de volta para listas
        data['attachments'] = json.loads(data['attachments']) if data['attachments'] else []
        data['tags'] = json.loads(data['tags']) if data['tags'] else []
        
        # Remover campos do banco que não estão no modelo
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        return Application.from_dict(data)
    
    # === MÉTODOS DE ESTATÍSTICA ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais"""
        with self.get_connection() as conn:
            stats = {}
            
            # Estatísticas de vagas
            stats['total_jobs'] = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            stats['jobs_by_status'] = dict(conn.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status"
            ).fetchall())
            stats['jobs_by_source'] = dict(conn.execute(
                "SELECT source, COUNT(*) FROM jobs GROUP BY source"
            ).fetchall())
            
            # Estatísticas de candidaturas
            stats['total_applications'] = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            stats['applications_by_status'] = dict(conn.execute(
                "SELECT status, COUNT(*) FROM applications GROUP BY status"
            ).fetchall())
            
            # Estatísticas de match
            avg_match = conn.execute(
                "SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL"
            ).fetchone()[0]
            stats['average_match_score'] = round(avg_match, 2) if avg_match else 0
            
            # Taxa de candidatura
            jobs_with_applications = conn.execute("""
                SELECT COUNT(DISTINCT j.id) 
                FROM jobs j 
                INNER JOIN applications a ON j.id = a.job_id
            """).fetchone()[0]
            
            if stats['total_jobs'] > 0:
                stats['application_rate'] = round(jobs_with_applications / stats['total_jobs'], 2)
            else:
                stats['application_rate'] = 0
            
            return stats
    
    def cleanup_old_jobs(self, days: int = 30):
        """Remove vagas antigas"""
        cutoff_date = datetime.now().replace(day=datetime.now().day - days)
        
        with self.get_connection() as conn:
            # Primeiro remove candidaturas órfãs
            conn.execute("""
                DELETE FROM applications 
                WHERE job_id IN (
                    SELECT id FROM jobs 
                    WHERE found_date < ? AND status = 'archived'
                )
            """, (cutoff_date.isoformat(),))
            
            # Depois remove as vagas
            deleted = conn.execute(
                "DELETE FROM jobs WHERE found_date < ? AND status = 'archived'",
                (cutoff_date.isoformat(),)
            ).rowcount
            
            conn.commit()
            return deleted
