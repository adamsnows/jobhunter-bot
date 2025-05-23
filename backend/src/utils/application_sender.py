"""
Application Sender
Sistema para envio automático de candidaturas
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from jinja2 import Template
from datetime import datetime

from ..models.job import Job

logger = logging.getLogger(__name__)

class ApplicationSender:
    """Enviador de candidaturas automáticas"""

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('EMAIL_ADDRESS', '')
        self.password = os.getenv('EMAIL_PASSWORD', '')

        # Configurações do usuário
        self.user_name = os.getenv('USER_NAME', 'Candidato')
        self.user_email = os.getenv('USER_EMAIL', self.email)
        self.cv_path = os.getenv('CV_PATH', 'documents/cv.pdf')

        # Templates
        self.email_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Carrega templates de email"""
        templates = {}

        # Template padrão de candidatura
        templates['default'] = """
Prezados recrutadores,

Espero que estejam bem!

Venho por meio desta demonstrar meu interesse na vaga de {{ job_title }} anunciada por {{ company }}.

Com {{ experience_years }} anos de experiência em desenvolvimento de software, tenho sólidos conhecimentos em:
{{ skills_list }}

Principais qualificações:
• Experiência comprovada em desenvolvimento backend com Python
• Conhecimento em frameworks como Django/Flask
• Experiência com bancos de dados relacionais (PostgreSQL, MySQL)
• Familiaridade com containerização (Docker) e cloud (AWS)
• Metodologias ágeis e versionamento com Git

Acredito que meu perfil está alinhado com os requisitos da vaga e gostaria muito de contribuir com os objetivos da {{ company }}.

Estou disponível para uma conversa e desde já agradeço a atenção.

Atenciosamente,
{{ user_name }}
{{ user_email }}
{{ user_phone }}
        """.strip()

        # Template para vagas de Python
        templates['python'] = """
Olá equipe de recrutamento da {{ company }}!

Vi a vaga de {{ job_title }} e fiquei muito interessado em fazer parte da equipe!

Sou desenvolvedor Python com foco em backend e APIs, com experiência em:
{{ skills_list }}

Alguns projetos que realizei:
• APIs REST com Django/Flask e PostgreSQL
• Sistemas de automação e web scraping
• Integração com serviços externos e APIs
• Deploy em cloud (AWS/GCP) com Docker

Tenho grande paixão por tecnologia e sempre busco aprender novas ferramentas e metodologias.

Estou ansioso para conhecer mais sobre a vaga e como posso contribuir!

Forte abraço,
{{ user_name }}
        """.strip()

        return templates

    def send_application(self, job: Job) -> bool:
        """Envia candidatura por email"""
        try:
            logger.info(f"📧 Preparando candidatura para {job.title} @ {job.company}")

            # Determina template baseado na vaga
            template_name = self._select_template(job)

            # Gera conteúdo do email
            subject, body = self._generate_email_content(job, template_name)

            # Envia email
            success = self._send_email(
                to_email=self._extract_company_email(job),
                subject=subject,
                body=body,
                attachments=[self.cv_path] if os.path.exists(self.cv_path) else []
            )

            if success:
                logger.info("✅ Candidatura enviada com sucesso!")
            else:
                logger.error("❌ Falha ao enviar candidatura")

            return success

        except Exception as e:
            logger.error(f"❌ Erro ao enviar candidatura: {str(e)}")
            return False

    def _select_template(self, job: Job) -> str:
        """Seleciona template baseado na vaga"""
        job_text = f"{job.title} {job.description or ''}".lower()

        if 'python' in job_text:
            return 'python'

        return 'default'

    def _generate_email_content(self, job: Job, template_name: str) -> tuple:
        """Gera conteúdo do email baseado no template"""
        try:
            # Dados para o template
            template_data = {
                'job_title': job.title,
                'company': job.company,
                'user_name': self.user_name,
                'user_email': self.user_email,
                'user_phone': os.getenv('USER_PHONE', ''),
                'experience_years': os.getenv('EXPERIENCE_YEARS', '3'),
                'skills_list': self._format_skills_list(),
                'current_date': datetime.now().strftime('%d/%m/%Y')
            }

            # Carrega e renderiza template
            template_content = self.email_templates.get(template_name, self.email_templates['default'])
            template = Template(template_content)
            body = template.render(**template_data)

            # Gera assunto
            subject = f"Candidatura para {job.title} - {self.user_name}"

            return subject, body

        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo: {str(e)}")
            return f"Candidatura para {job.title}", "Candidatura anexada."

    def _format_skills_list(self) -> str:
        """Formata lista de skills do usuário"""
        skills = os.getenv('USER_SKILLS', 'Python,Django,PostgreSQL,Docker,Git').split(',')
        return '• ' + '\n• '.join(skill.strip() for skill in skills)

    def _extract_company_email(self, job: Job) -> str:
        """Extrai ou gera email da empresa"""
        # Por enquanto, usa email genérico baseado na empresa
        # Em uma implementação real, você poderia:
        # 1. Extrair email da descrição da vaga
        # 2. Usar APIs para encontrar emails corporativos
        # 3. Enviar através da própria plataforma (LinkedIn, etc.)

        company_name = job.company.lower().replace(' ', '').replace('.', '')

        # Emails genéricos comuns
        generic_emails = [
            f"rh@{company_name}.com.br",
            f"recrutamento@{company_name}.com.br",
            f"jobs@{company_name}.com.br",
            f"contato@{company_name}.com.br"
        ]

        # Por agora, retorna o primeiro
        return generic_emails[0]

    def _send_email(self, to_email: str, subject: str, body: str,
                   attachments: List[str] = None) -> bool:
        """Envia email SMTP"""
        try:
            # Validações básicas
            if not self.email or not self.password:
                logger.error("❌ Credenciais de email não configuradas")
                return False

            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Adiciona corpo do email
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Adiciona anexos
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
                    else:
                        logger.warning(f"⚠️ Arquivo não encontrado: {file_path}")

            # Conecta e envia
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)

            logger.info(f"📧 Email enviado para: {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {str(e)}")
            return False

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """Anexa arquivo ao email"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)

            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            msg.attach(part)
            logger.info(f"📎 Arquivo anexado: {filename}")

        except Exception as e:
            logger.error(f"❌ Erro ao anexar arquivo {file_path}: {str(e)}")

    def create_custom_template(self, template_name: str, content: str) -> bool:
        """Cria template personalizado"""
        try:
            self.email_templates[template_name] = content

            # Salva em arquivo (opcional)
            template_file = f"templates/email_{template_name}.txt"
            os.makedirs(os.path.dirname(template_file), exist_ok=True)

            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"✅ Template '{template_name}' criado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao criar template: {str(e)}")
            return False

    def test_email_setup(self) -> bool:
        """Testa configuração de email"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)

            logger.info("✅ Configuração de email OK")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na configuração de email: {str(e)}")
            return False

    def get_application_stats(self) -> Dict:
        """Retorna estatísticas de candidaturas"""
        # Esta função seria implementada junto com o banco de dados
        # para rastrear estatísticas de envio

        return {
            'total_sent': 0,
            'success_rate': 0,
            'last_sent': None,
            'email_configured': bool(self.email and self.password)
        }
