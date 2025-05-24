"""
Template de email para candidatura automática
"""

EMAIL_TEMPLATE = """
Prezados,

Espero que estejam bem.

Meu nome é {user_name} e gostaria de manifestar meu interesse na vaga de {job_title} na {company}.

Tenho experiência sólida em desenvolvimento de software e acredito que meu perfil se alinha perfeitamente com os requisitos da posição. Segue em anexo meu currículo para análise.

Principais qualificações:
• Experiência em desenvolvimento Python/JavaScript
• Conhecimento em frameworks modernos
• Experiência com bancos de dados
• Capacidade de trabalhar em equipe

Estou disponível para uma conversa e seria um prazer contribuir com o crescimento da empresa.

Atenciosamente,
{user_name}

Contato: {user_email}
Telefone: {user_phone}
LinkedIn: {user_linkedin}

---
Este email foi enviado automaticamente pelo JobHunter Bot.
"""

EMAIL_SUBJECT_TEMPLATE = "Candidatura para {job_title} - {user_name}"
