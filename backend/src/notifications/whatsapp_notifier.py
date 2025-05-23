"""
WhatsApp Business API notifier for JobHunter Bot
Sends notifications via WhatsApp Business API
"""

import os
import requests
import json
from typing import List, Dict, Any
from loguru import logger

class WhatsAppNotifier:
    """WhatsApp Business API notifier"""

    def __init__(self):
        """Initialize WhatsApp notifier"""
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.recipient_number = os.getenv('WHATSAPP_RECIPIENT_NUMBER')

        # WhatsApp Business API base URL
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"

        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Validate configuration
        if not all([self.phone_number_id, self.access_token, self.recipient_number]):
            logger.warning("WhatsApp configuration incomplete. Some notifications may not be sent.")

    def send_message(self, message: str) -> bool:
        """
        Send a simple text message via WhatsApp

        Args:
            message: The message to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self._is_configured():
            logger.warning("WhatsApp not configured. Message not sent.")
            return False

        payload = {
            "messaging_product": "whatsapp",
            "to": self.recipient_number,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 200:
                logger.info("WhatsApp message sent successfully")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    def send_job_notification(self, job: Dict[str, Any]) -> bool:
        """
        Send a formatted job notification

        Args:
            job: Job dictionary with details

        Returns:
            bool: True if notification was sent successfully
        """
        message = self._format_job_message(job)
        return self.send_message(message)

    def send_application_notification(self, job: Dict[str, Any], status: str) -> bool:
        """
        Send application status notification

        Args:
            job: Job dictionary with details
            status: Application status (sent, failed, etc.)

        Returns:
            bool: True if notification was sent successfully
        """
        message = self._format_application_message(job, status)
        return self.send_message(message)

    def send_daily_summary(self, jobs_found: int, applications_sent: int, match_score: float) -> bool:
        """
        Send daily summary notification

        Args:
            jobs_found: Number of jobs found
            applications_sent: Number of applications sent
            match_score: Average match score

        Returns:
            bool: True if notification was sent successfully
        """
        message = f"""🤖 *JobHunter Bot - Resumo Diário*

📊 *Estatísticas de hoje:*
• {jobs_found} vagas encontradas
• {applications_sent} candidaturas enviadas
• {match_score:.1%} score médio de compatibilidade

✨ Continue acompanhando as oportunidades!"""

        return self.send_message(message)

    def send_error_notification(self, error_message: str) -> bool:
        """
        Send error notification

        Args:
            error_message: Error message to send

        Returns:
            bool: True if notification was sent successfully
        """
        message = f"""⚠️ *JobHunter Bot - Erro*

{error_message}

Por favor, verifique os logs para mais detalhes."""

        return self.send_message(message)

    def _format_job_message(self, job: Dict[str, Any]) -> str:
        """Format job notification message"""
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        location = job.get('location', 'N/A')
        salary = job.get('salary', 'N/A')
        match_score = job.get('match_score', 0)
        url = job.get('url', '')

        message = f"""🎯 *Nova Vaga Encontrada!*

*{title}*
🏢 {company}
📍 {location}
💰 {salary}
📈 Match: {match_score:.1%}

{url}"""

        return message

    def _format_application_message(self, job: Dict[str, Any], status: str) -> str:
        """Format application notification message"""
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')

        status_emoji = {
            'sent': '✅',
            'failed': '❌',
            'pending': '⏳'
        }.get(status.lower(), '📧')

        message = f"""{status_emoji} *Candidatura {status.title()}*

*{title}*
🏢 {company}

Status: {status}"""

        return message

    def _is_configured(self) -> bool:
        """Check if WhatsApp is properly configured"""
        return all([
            self.phone_number_id,
            self.access_token,
            self.recipient_number
        ])

    def test_connection(self) -> bool:
        """
        Test WhatsApp connection

        Returns:
            bool: True if connection is working
        """
        test_message = "🤖 JobHunter Bot - Teste de conexão WhatsApp ✅"
        return self.send_message(test_message)
