"""
Email notification module for JobHunter Bot
Sends job application emails with CV attachment
"""
import logging
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification and application sender"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize email notifier"""
        self.config = config or {}
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))

        # User data for applications
        self.user_name = os.getenv('USER_NAME', '')
        self.user_email = os.getenv('USER_EMAIL', '')
        self.user_phone = os.getenv('USER_PHONE', '')
        self.user_linkedin = os.getenv('USER_LINKEDIN', '')
        self.cv_file_path = os.getenv('CV_FILE_PATH', 'documents/cv.pdf')

        self.enabled = bool(self.email_user and self.email_password)

        if self.enabled:
            logger.info("📧 Email notifier initialized and ready")
        else:
            logger.warning("📧 Email notifier disabled - missing credentials")

    def send_job_application(self, job_data: Dict[str, Any], contact_email: str) -> bool:
        """Send job application email with CV attachment"""
        try:
            if not self.enabled:
                logger.error("📧 Email not configured")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = contact_email
            msg['Subject'] = f"Candidatura para {job_data.get('title', 'Vaga')} - {self.user_name}"

            # Email body
            body = self._create_application_email_body(job_data)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Attach CV if exists
            if os.path.exists(self.cv_file_path):
                self._attach_cv(msg)
            else:
                logger.warning(f"📎 CV file not found: {self.cv_file_path}")

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"📧 Application sent to {contact_email} for {job_data.get('title', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"📧 Failed to send application: {str(e)}")
            return False

    def _create_application_email_body(self, job_data: Dict[str, Any]) -> str:
        """Create email body for job application"""
        company = job_data.get('company', 'empresa')
        job_title = job_data.get('title', 'vaga')

        return f"""Prezados,

Espero que estejam bem.

Meu nome é {self.user_name} e gostaria de manifestar meu interesse na vaga de {job_title} na {company}.

Tenho experiência sólida em desenvolvimento de software e acredito que meu perfil se alinha perfeitamente com os requisitos da posição. Segue em anexo meu currículo para análise.

Principais qualificações:
• Experiência em desenvolvimento Python/JavaScript
• Conhecimento em frameworks modernos
• Experiência com bancos de dados
• Capacidade de trabalhar em equipe

Estou disponível para uma conversa e seria um prazer contribuir com o crescimento da {company}.

Atenciosamente,
{self.user_name}

Contato: {self.user_email}
Telefone: {self.user_phone}
LinkedIn: {self.user_linkedin}

---
Referência da vaga: {job_data.get('url', 'N/A')}
"""

    def _attach_cv(self, msg: MIMEMultipart) -> None:
        """Attach CV file to email"""
        try:
            with open(self.cv_file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            filename = Path(self.cv_file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            logger.info(f"📎 CV attached: {filename}")

        except Exception as e:
            logger.error(f"📎 Failed to attach CV: {str(e)}")

    def send_notification(self, subject: str, message: str, recipient: Optional[str] = None) -> bool:
        """Send general notification email"""
        try:
            if not self.enabled:
                return False

            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = recipient or self.user_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain', 'utf-8'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"📧 Notification sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"📧 Failed to send notification: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """Test email connection"""
        try:
            if not self.enabled:
                return False

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)

            logger.info("📧 Email connection test: OK")
            return True

        except Exception as e:
            logger.error(f"📧 Email connection test failed: {str(e)}")
            return False
