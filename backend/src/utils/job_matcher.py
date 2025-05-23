"""
Job Matcher
Sistema para calcular score de compatibilidade entre perfil do usuário e vagas
"""

import re
import logging
from typing import List, Dict, Set
from dataclasses import dataclass

from ..models.job import Job

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """Perfil do usuário para matching"""
    skills: List[str]
    experience_years: int
    preferred_technologies: List[str]
    preferred_roles: List[str]
    location_preferences: List[str]
    salary_min: float
    salary_max: float

class JobMatcher:
    """Calculadora de score de compatibilidade"""

    def __init__(self, profile_file: str = "config/user_profile.json"):
        self.profile = self._load_user_profile(profile_file)

        # Pesos para diferentes critérios
        self.weights = {
            'skills_match': 0.4,
            'title_match': 0.25,
            'location_match': 0.15,
            'salary_match': 0.1,
            'company_preference': 0.1
        }

        # Skills e tecnologias normalizadas
        self.skill_synonyms = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs', 'react', 'vue', 'angular'],
            'java': ['java', 'spring', 'springboot'],
            'docker': ['docker', 'containers', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s', 'orchestration'],
            'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
            'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'database'],
            'machine learning': ['ml', 'machine learning', 'ai', 'artificial intelligence'],
            'devops': ['devops', 'ci/cd', 'jenkins', 'gitlab'],
            'git': ['git', 'github', 'gitlab', 'version control']
        }

    def _load_user_profile(self, profile_file: str) -> UserProfile:
        """Carrega perfil do usuário do arquivo ou cria padrão"""
        try:
            import json
            import os

            if os.path.exists(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return UserProfile(**data)
            else:
                # Perfil padrão se arquivo não existir
                default_profile = UserProfile(
                    skills=['python', 'django', 'flask', 'postgresql', 'docker', 'git'],
                    experience_years=3,
                    preferred_technologies=['python', 'django', 'postgresql', 'docker', 'aws'],
                    preferred_roles=['backend developer', 'python developer', 'software engineer', 'full stack developer'],
                    location_preferences=['são paulo', 'sp', 'remote', 'remoto'],
                    salary_min=5000,
                    salary_max=15000
                )

                # Cria arquivo padrão
                self._save_user_profile(profile_file, default_profile)
                return default_profile

        except Exception as e:
            logger.error(f"Erro ao carregar perfil: {str(e)}")
            # Retorna perfil mínimo
            return UserProfile(
                skills=['python'], experience_years=1,
                preferred_technologies=['python'], preferred_roles=['developer'],
                location_preferences=['remote'], salary_min=0, salary_max=999999
            )

    def _save_user_profile(self, profile_file: str, profile: UserProfile) -> None:
        """Salva perfil do usuário no arquivo"""
        try:
            import json
            import os

            # Cria diretório se não existir
            os.makedirs(os.path.dirname(profile_file), exist_ok=True)

            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'skills': profile.skills,
                    'experience_years': profile.experience_years,
                    'preferred_technologies': profile.preferred_technologies,
                    'preferred_roles': profile.preferred_roles,
                    'location_preferences': profile.location_preferences,
                    'salary_min': profile.salary_min,
                    'salary_max': profile.salary_max
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Erro ao salvar perfil: {str(e)}")

    def calculate_match_score(self, job: Job) -> float:
        """Calcula score de compatibilidade (0-100)"""
        try:
            scores = {}

            # 1. Match de skills/tecnologias
            scores['skills_match'] = self._calculate_skills_match(job)

            # 2. Match de título/função
            scores['title_match'] = self._calculate_title_match(job)

            # 3. Match de localização
            scores['location_match'] = self._calculate_location_match(job)

            # 4. Match de salário
            scores['salary_match'] = self._calculate_salary_match(job)

            # 5. Preferência por empresa (básico)
            scores['company_preference'] = self._calculate_company_preference(job)

            # Calcula score final ponderado
            final_score = sum(
                scores[criteria] * self.weights[criteria]
                for criteria in scores.keys()
            )

            # Normaliza para 0-100
            final_score = max(0, min(100, final_score))

            logger.debug(f"Score para '{job.title}' @ {job.company}: {final_score:.1f}% {scores}")

            return round(final_score, 1)

        except Exception as e:
            logger.error(f"Erro ao calcular score: {str(e)}")
            return 0.0

    def _calculate_skills_match(self, job: Job) -> float:
        """Calcula match de skills/tecnologias"""
        job_text = f"{job.title} {job.description or ''} {job.requirements or ''}".lower()

        matched_skills = 0
        total_skills = len(self.profile.skills)

        for skill in self.profile.skills:
            skill_variants = self.skill_synonyms.get(skill.lower(), [skill.lower()])

            for variant in skill_variants:
                if variant in job_text:
                    matched_skills += 1
                    break

        return (matched_skills / total_skills * 100) if total_skills > 0 else 0

    def _calculate_title_match(self, job: Job) -> float:
        """Calcula match com títulos preferidos"""
        job_title = job.title.lower()

        for preferred_role in self.profile.preferred_roles:
            role_words = preferred_role.lower().split()

            # Verifica se todas as palavras do role estão no título
            if all(word in job_title for word in role_words):
                return 100

            # Verifica match parcial
            matching_words = sum(1 for word in role_words if word in job_title)
            if matching_words > 0:
                return (matching_words / len(role_words)) * 80

        # Match genérico para palavras-chave comuns
        generic_matches = ['developer', 'engineer', 'programmer', 'analyst']
        for match in generic_matches:
            if match in job_title:
                return 50

        return 20  # Score mínimo

    def _calculate_location_match(self, job: Job) -> float:
        """Calcula match de localização"""
        if not job.location:
            return 50  # Neutro se não especificado

        job_location = job.location.lower()

        # Remote/remoto sempre é preferível
        if any(remote in job_location for remote in ['remote', 'remoto', 'home office']):
            return 100

        # Verifica preferências específicas
        for pref in self.profile.location_preferences:
            if pref.lower() in job_location:
                return 90

        # Localizações aceitáveis (mesmo estado/região)
        acceptable_locations = ['sp', 'são paulo', 'brasil', 'brazil']
        for loc in acceptable_locations:
            if loc in job_location:
                return 70

        return 30  # Localização não preferida

    def _calculate_salary_match(self, job: Job) -> float:
        """Calcula match de salário"""
        if not job.salary:
            return 50  # Neutro se não especificado

        try:
            # Extrai números do texto de salário
            salary_numbers = re.findall(r'[\d.]+', job.salary.replace(',', '.'))

            if not salary_numbers:
                return 50

            # Pega o maior valor encontrado
            max_salary = max(float(num) for num in salary_numbers)

            # Normaliza valores (assume que valores < 100 são em milhares)
            if max_salary < 100:
                max_salary *= 1000

            # Verifica se está na faixa desejada
            if self.profile.salary_min <= max_salary <= self.profile.salary_max:
                return 100
            elif max_salary >= self.profile.salary_min:
                return 80  # Acima do mínimo
            else:
                return 30  # Abaixo do mínimo

        except Exception:
            return 50

    def _calculate_company_preference(self, job: Job) -> float:
        """Calcula preferência por empresa (básico)"""
        if not job.company:
            return 50

        company_name = job.company.lower()

        # Empresas tech conhecidas (score maior)
        tech_companies = [
            'google', 'microsoft', 'amazon', 'meta', 'apple', 'netflix',
            'uber', 'airbnb', 'spotify', 'slack', 'github', 'gitlab',
            'nubank', 'stone', 'mercadolivre', 'ifood', 'magazine luiza'
        ]

        for company in tech_companies:
            if company in company_name:
                return 90

        # Startups e empresas menores
        startup_indicators = ['startup', 'fintech', 'tech', 'software', 'digital']
        for indicator in startup_indicators:
            if indicator in company_name:
                return 75

        return 60  # Score padrão para outras empresas

    def get_job_insights(self, job: Job) -> Dict:
        """Retorna insights detalhados sobre uma vaga"""
        skills_found = []
        job_text = f"{job.title} {job.description or ''} {job.requirements or ''}".lower()

        for skill in self.profile.skills:
            skill_variants = self.skill_synonyms.get(skill.lower(), [skill.lower()])

            for variant in skill_variants:
                if variant in job_text:
                    skills_found.append(skill)
                    break

        missing_skills = [skill for skill in self.profile.skills if skill not in skills_found]

        return {
            'match_score': self.calculate_match_score(job),
            'skills_found': skills_found,
            'missing_skills': missing_skills,
            'title_match': job.title.lower() in ' '.join(self.profile.preferred_roles).lower(),
            'location_preference': any(
                pref.lower() in (job.location or '').lower()
                for pref in self.profile.location_preferences
            ),
            'recommendations': self._generate_recommendations(job, skills_found, missing_skills)
        }

    def _generate_recommendations(self, job: Job, skills_found: List[str],
                                missing_skills: List[str]) -> List[str]:
        """Gera recomendações para melhorar o match"""
        recommendations = []

        if len(skills_found) < len(self.profile.skills) * 0.5:
            recommendations.append(
                f"Considere destacar as skills encontradas: {', '.join(skills_found)}"
            )

        if missing_skills:
            recommendations.append(
                f"Skills que podem ser úteis: {', '.join(missing_skills[:3])}"
            )

        if job.salary and 'salário não informado' not in job.salary.lower():
            recommendations.append("Salário informado - bom sinal!")

        return recommendations

    def update_profile(self, **kwargs) -> None:
        """Atualiza perfil do usuário"""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)

        # Salva perfil atualizado
        self._save_user_profile("config/user_profile.json", self.profile)
        logger.info("✅ Perfil do usuário atualizado")
