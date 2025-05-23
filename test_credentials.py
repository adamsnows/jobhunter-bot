#!/usr/bin/env python3
"""
Script para testar todas as credenciais das APIs
Execute: python test_credentials.py
"""

import os
import sys
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def test_email():
    """Testa configuração do email"""
    print("🧪 Testando Email...")

    try:
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        notification_email = os.getenv('NOTIFICATION_EMAIL')

        if not all([email_user, email_password, notification_email]):
            print("❌ Email: Credenciais não configuradas")
            return False

        # Cria mensagem de teste
        msg = MIMEText('🤖 Teste do JobHunter Bot - Email funcionando!')
        msg['Subject'] = 'JobHunter Bot - Teste de Email'
        msg['From'] = email_user
        msg['To'] = notification_email

        # Envia email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)

        print("✅ Email: Funcionando! Verifique sua caixa de entrada.")
        return True

    except Exception as e:
        print(f"❌ Email: Erro - {str(e)}")
        return False

def test_telegram():
    """Testa configuração do Telegram"""
    print("🧪 Testando Telegram...")

    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not all([token, chat_id]):
            print("❌ Telegram: Credenciais não configuradas")
            return False

        # Testa envio de mensagem
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': '🤖 JobHunter Bot - Teste do Telegram funcionando! ✅'
        }

        response = requests.post(url, data=data, timeout=10)

        if response.ok:
            print("✅ Telegram: Funcionando! Verifique seu chat.")
            return True
        else:
            print(f"❌ Telegram: Erro na API - {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Telegram: Erro - {str(e)}")
        return False

def test_whatsapp():
    """Testa configuração do WhatsApp"""
    print("🧪 Testando WhatsApp...")

    try:
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        recipient = os.getenv('WHATSAPP_RECIPIENT_NUMBER')

        if not all([phone_number_id, access_token, recipient]):
            print("❌ WhatsApp: Credenciais não configuradas")
            return False

        # Testa envio de mensagem
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {
                "body": "🤖 JobHunter Bot - Teste do WhatsApp funcionando! ✅"
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ WhatsApp: Funcionando! Verifique seu WhatsApp.")
            return True
        else:
            print(f"❌ WhatsApp: Erro na API - {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"❌ WhatsApp: Erro - {str(e)}")
        return False

def test_twitter():
    """Testa configuração do X (Twitter)"""
    print("🧪 Testando X (Twitter)...")

    try:
        bearer_token = os.getenv('X_BEARER_TOKEN')

        if not bearer_token:
            print("❌ X (Twitter): Bearer token não configurado")
            return False

        # Testa busca básica
        headers = {'Authorization': f'Bearer {bearer_token}'}
        url = 'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': 'python jobs',
            'max_results': 10
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            tweet_count = len(data.get('data', []))
            print(f"✅ X (Twitter): Funcionando! Encontrou {tweet_count} tweets sobre 'python jobs'.")
            return True
        elif response.status_code == 429:
            print("⚠️ X (Twitter): Rate limit atingido, mas credenciais válidas.")
            return True
        else:
            print(f"❌ X (Twitter): Erro na API - {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"❌ X (Twitter): Erro - {str(e)}")
        return False

def test_linkedin():
    """Testa configuração do LinkedIn (apenas validação de credenciais)"""
    print("🧪 Testando LinkedIn...")

    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')

    if not all([email, password]):
        print("❌ LinkedIn: Credenciais não configuradas")
        return False

    # Não fazemos teste real do LinkedIn para evitar bloqueios
    print("⚠️ LinkedIn: Credenciais configuradas. (Teste real não executado para evitar bloqueios)")
    print("   Use com cuidado e adicione delays entre requests!")
    return True

def main():
    """Executa todos os testes"""
    print("🚀 JobHunter Bot - Teste de Credenciais")
    print("=" * 50)

    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        print("   Copie .env.example para .env e configure suas credenciais.")
        sys.exit(1)

    results = {}

    # Executa todos os testes
    results['email'] = test_email()
    results['telegram'] = test_telegram()
    results['whatsapp'] = test_whatsapp()
    results['twitter'] = test_twitter()
    results['linkedin'] = test_linkedin()

    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 50)

    for service, success in results.items():
        status = "✅ Funcionando" if success else "❌ Com problema"
        print(f"{service.capitalize():12} | {status}")

    # Estatísticas
    working = sum(results.values())
    total = len(results)

    print(f"\n📈 {working}/{total} serviços funcionando ({working/total*100:.0f}%)")

    if working >= 2:
        print("\n🎉 Você tem serviços suficientes para começar a usar o bot!")
        print("   Recomendação mínima: Email + Telegram/WhatsApp + Twitter")
    else:
        print("\n⚠️ Configure mais serviços para usar o bot efetivamente.")
        print("   Consulte: docs/setup-credenciais.md")

if __name__ == "__main__":
    main()
