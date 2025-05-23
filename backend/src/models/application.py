"""
Modelo de candidatura a vaga
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ApplicationStatus(Enum):
    """Status da candidatura"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    REJECTED = "rejected"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_RECEIVED = "offer_received"
    ACCEPTED = "accepted"
    FAILED = "failed"


class ApplicationMethod(Enum):
    """Método de candidatura"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    X_TWITTER = "x_twitter"
    MANUAL = "manual"


@dataclass
class Application:
    """Modelo de uma candidatura"""

    # Identificação
    id: Optional[str] = None
    job_id: str = ""

    # Detalhes da candidatura
    method: ApplicationMethod = ApplicationMethod.EMAIL
    status: ApplicationStatus = ApplicationStatus.PENDING

    # Email/Contato
    recipient_email: Optional[str] = None
    subject: str = ""
    message_body: str = ""
    cover_letter: str = ""

    # Anexos enviados
    resume_sent: bool = False
    portfolio_sent: bool = False
    cover_letter_sent: bool = False
    attachments: List[str] = field(default_factory=list)

    # Timestamps
    created_date: datetime = field(default_factory=datetime.now)
    sent_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    read_date: Optional[datetime] = None
    response_date: Optional[datetime] = None

    # Resposta
    response_received: bool = False
    response_content: Optional[str] = None
    response_type: Optional[str] = None  # positive, negative, neutral

    # Follow-up
    follow_up_count: int = 0
    last_follow_up_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None

    # Metadados
    automated: bool = True
    match_score_at_application: Optional[float] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Processamento pós-inicialização"""
        if not self.id:
            # Gerar ID único
            import hashlib
            import uuid
            unique_string = f"{self.job_id}_{self.created_date.isoformat()}_{uuid.uuid4().hex[:8]}"
            self.id = hashlib.md5(unique_string.encode()).hexdigest()[:12]

    def mark_as_sent(self, email: Optional[str] = None):
        """Marca candidatura como enviada"""
        self.status = ApplicationStatus.SENT
        self.sent_date = datetime.now()
        if email:
            self.recipient_email = email

    def mark_as_delivered(self):
        """Marca candidatura como entregue"""
        self.status = ApplicationStatus.DELIVERED
        self.delivered_date = datetime.now()

    def mark_as_read(self):
        """Marca candidatura como lida"""
        self.status = ApplicationStatus.READ
        self.read_date = datetime.now()

    def add_response(self, content: str, response_type: str = "neutral"):
        """Adiciona resposta recebida"""
        self.response_received = True
        self.response_content = content
        self.response_type = response_type
        self.response_date = datetime.now()
        self.status = ApplicationStatus.RESPONDED

    def schedule_follow_up(self, days_from_now: int = 7):
        """Agenda follow-up"""
        from datetime import timedelta
        self.next_follow_up_date = datetime.now() + timedelta(days=days_from_now)

    def send_follow_up(self):
        """Registra envio de follow-up"""
        self.follow_up_count += 1
        self.last_follow_up_date = datetime.now()
        self.next_follow_up_date = None

    def calculate_response_time(self) -> Optional[int]:
        """Calcula tempo de resposta em horas"""
        if self.sent_date and self.response_date:
            delta = self.response_date - self.sent_date
            return int(delta.total_seconds() / 3600)  # Retorna em horas
        return None

    def is_follow_up_due(self) -> bool:
        """Verifica se é hora de fazer follow-up"""
        if not self.next_follow_up_date:
            return False
        return datetime.now() >= self.next_follow_up_date

    def days_since_application(self) -> int:
        """Retorna quantos dias se passaram desde a candidatura"""
        if self.sent_date:
            delta = datetime.now() - self.sent_date
            return delta.days
        return 0

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'method': self.method.value,
            'status': self.status.value,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'message_body': self.message_body,
            'cover_letter': self.cover_letter,
            'resume_sent': self.resume_sent,
            'portfolio_sent': self.portfolio_sent,
            'cover_letter_sent': self.cover_letter_sent,
            'attachments': self.attachments,
            'created_date': self.created_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'delivered_date': self.delivered_date.isoformat() if self.delivered_date else None,
            'read_date': self.read_date.isoformat() if self.read_date else None,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'response_received': self.response_received,
            'response_content': self.response_content,
            'response_type': self.response_type,
            'follow_up_count': self.follow_up_count,
            'last_follow_up_date': self.last_follow_up_date.isoformat() if self.last_follow_up_date else None,
            'next_follow_up_date': self.next_follow_up_date.isoformat() if self.next_follow_up_date else None,
            'automated': self.automated,
            'match_score_at_application': self.match_score_at_application,
            'notes': self.notes,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Application':
        """Cria instância a partir de dicionário"""
        # Converter datas de string para datetime
        date_fields = ['created_date', 'sent_date', 'delivered_date', 'read_date',
                      'response_date', 'last_follow_up_date', 'next_follow_up_date']

        for field in date_fields:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])

        # Converter enums
        if data.get('method'):
            data['method'] = ApplicationMethod(data['method'])
        if data.get('status'):
            data['status'] = ApplicationStatus(data['status'])

        return cls(**data)

    def __str__(self) -> str:
        return f"Application {self.id} for Job {self.job_id} - {self.status.value}"

    def __repr__(self) -> str:
        return f"Application(id='{self.id}', job_id='{self.job_id}', status='{self.status.value}')"
