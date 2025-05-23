"""
Modelo de vaga de emprego
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class JobSource(Enum):
    """Fonte da vaga"""
    LINKEDIN = "linkedin"
    X_TWITTER = "x_twitter"
    MANUAL = "manual"


class JobStatus(Enum):
    """Status da vaga"""
    NEW = "new"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"
    ARCHIVED = "archived"


@dataclass
class Job:
    """Modelo de uma vaga de emprego"""

    # Identificação
    id: Optional[str] = None
    title: str = ""
    company: str = ""
    location: str = ""

    # Detalhes
    description: str = ""
    requirements: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "BRL"

    # Links e contato
    url: str = ""
    contact_email: Optional[str] = None

    # Metadados
    source: JobSource = JobSource.MANUAL
    status: JobStatus = JobStatus.NEW
    remote_ok: bool = False
    contract_type: str = ""  # CLT, PJ, Estágio, etc.

    # Skills e matching
    required_skills: List[str] = field(default_factory=list)
    nice_to_have_skills: List[str] = field(default_factory=list)
    match_score: Optional[float] = None

    # Timestamps
    posted_date: Optional[datetime] = None
    found_date: datetime = field(default_factory=datetime.now)
    applied_date: Optional[datetime] = None

    # Tags e classificação
    tags: List[str] = field(default_factory=list)
    experience_level: str = ""  # Junior, Pleno, Senior

    def __post_init__(self):
        """Processamento pós-inicialização"""
        if not self.id:
            # Gerar ID único baseado em título + empresa + URL
            import hashlib
            unique_string = f"{self.title}_{self.company}_{self.url}"
            self.id = hashlib.md5(unique_string.encode()).hexdigest()[:12]

    def extract_skills_from_description(self) -> List[str]:
        """Extrai skills da descrição da vaga"""
        # Lista básica de tecnologias para detectar
        common_skills = [
            'python', 'javascript', 'java', 'react', 'django', 'flask',
            'fastapi', 'postgresql', 'mysql', 'mongodb', 'redis', 'docker',
            'kubernetes', 'aws', 'gcp', 'azure', 'git', 'linux', 'node.js',
            'typescript', 'html', 'css', 'sql', 'api', 'rest', 'graphql'
        ]

        description_lower = self.description.lower()
        requirements_lower = self.requirements.lower()
        full_text = f"{description_lower} {requirements_lower}"

        found_skills = []
        for skill in common_skills:
            if skill in full_text:
                found_skills.append(skill.title())

        return found_skills

    def calculate_match_score(self, user_skills: List[str]) -> float:
        """Calcula score de match com as skills do usuário"""
        if not self.required_skills and not self.nice_to_have_skills:
            # Se não temos skills definidas, extrai da descrição
            extracted_skills = self.extract_skills_from_description()
            self.required_skills = extracted_skills[:5]  # Primeiras 5 como required
            self.nice_to_have_skills = extracted_skills[5:]  # Resto como nice-to-have

        user_skills_lower = [skill.lower() for skill in user_skills]
        required_lower = [skill.lower() for skill in self.required_skills]
        nice_to_have_lower = [skill.lower() for skill in self.nice_to_have_skills]

        # Score baseado em skills obrigatórias (peso 70%)
        required_matches = len(set(user_skills_lower) & set(required_lower))
        required_total = len(required_lower) if required_lower else 1
        required_score = (required_matches / required_total) * 0.7

        # Score baseado em skills desejáveis (peso 30%)
        nice_matches = len(set(user_skills_lower) & set(nice_to_have_lower))
        nice_total = len(nice_to_have_lower) if nice_to_have_lower else 1
        nice_score = (nice_matches / nice_total) * 0.3

        self.match_score = min(required_score + nice_score, 1.0)
        return self.match_score

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'requirements': self.requirements,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'url': self.url,
            'contact_email': self.contact_email,
            'source': self.source.value,
            'status': self.status.value,
            'remote_ok': self.remote_ok,
            'contract_type': self.contract_type,
            'required_skills': self.required_skills,
            'nice_to_have_skills': self.nice_to_have_skills,
            'match_score': self.match_score,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'found_date': self.found_date.isoformat(),
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'tags': self.tags,
            'experience_level': self.experience_level
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Job':
        """Cria instância a partir de dicionário"""
        # Converter datas de string para datetime
        if data.get('posted_date'):
            data['posted_date'] = datetime.fromisoformat(data['posted_date'])
        if data.get('found_date'):
            data['found_date'] = datetime.fromisoformat(data['found_date'])
        if data.get('applied_date'):
            data['applied_date'] = datetime.fromisoformat(data['applied_date'])

        # Converter enums
        if data.get('source'):
            data['source'] = JobSource(data['source'])
        if data.get('status'):
            data['status'] = JobStatus(data['status'])

        return cls(**data)

    def __str__(self) -> str:
        return f"{self.title} at {self.company} ({self.location})"

    def __repr__(self) -> str:
        return f"Job(id='{self.id}', title='{self.title}', company='{self.company}')"
