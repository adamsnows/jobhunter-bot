#!/usr/bin/env python3
"""
Script interativo para configurar credenciais do JobHunter Bot
Execute: python setup_wizard.py
"""

import os
import shutil
from pathlib import Path

def print_header():
    """Imprime cabeçalho"""
    print("🤖 JobHunter Bot - Assistente de Configuração")
    print("=" * 50)
    print("Este assistente te ajudará a configurar as credenciais necessárias.")
    print("Pressione Enter para pular campos opcionais.\n")

def setup_env_file():
    """Configura o arquivo .env"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')

    # Copia .env.example se .env não existir
    if not env_path.exists() and env_example_path.exists():
        shutil.copy(env_example_path, env_path)
        print("✅ Arquivo .env criado a partir do .env.example")

    return env_path

def update_env_variable(env_path, key, value):
    """Atualiza uma variável no arquivo .env"""
    if not value.strip():
        return

    # Lê o arquivo
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()

    # Procura e atualiza a variável
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            updated = True
            break

    # Adiciona se não encontrou
    if not updated:
        lines.append(f"{key}={value}\n")

    # Escreve o arquivo
    with open(env_path, 'w') as f:
        f.writelines(lines)

def configure_email():
    """Configura email"""
    print("\n📧 CONFIGURAÇÃO DE EMAIL (Obrigatório)")
    print("-" * 30)
    print("Para Gmail:")
    print("1. Ative verificação em duas etapas")
    print("2. Gere uma senha de app em myaccount.google.com")
    print("3. Use a senha de app (16 caracteres), não sua senha normal\n")

    email = input("Digite seu email: ").strip()
    if email:
        password = input("Digite a senha de app: ").strip()
        return {'EMAIL_USER': email, 'EMAIL_PASSWORD': password, 'NOTIFICATION_EMAIL': email}

    return {}

def configure_telegram():
    """Configura Telegram"""
    print("\n🤖 CONFIGURAÇÃO DO TELEGRAM (Recomendado)")
    print("-" * 30)
    print("1. Procure @BotFather no Telegram")
    print("2. Digite /newbot e siga as instruções")
    print("3. Copie o token fornecido")
    print("4. Envie uma mensagem para seu bot")
    print("5. Para obter chat_id, acesse:")
    print("   https://api.telegram.org/bot<TOKEN>/getUpdates\n")

    token = input("Digite o token do bot (opcional): ").strip()
    if token:
        chat_id = input("Digite seu chat ID: ").strip()
        return {'TELEGRAM_BOT_TOKEN': token, 'TELEGRAM_CHAT_ID': chat_id}

    return {}

def configure_twitter():
    """Configura Twitter/X"""
    print("\n🐦 CONFIGURAÇÃO DO X (TWITTER) (Recomendado)")
    print("-" * 30)
    print("1. Acesse developer.twitter.com")
    print("2. Crie uma conta de desenvolvedor")
    print("3. Crie um projeto e app")
    print("4. Copie as credenciais\n")

    bearer = input("Digite o Bearer Token (opcional): ").strip()
    if bearer:
        api_key = input("Digite API Key (opcional): ").strip()
        api_secret = input("Digite API Secret (opcional): ").strip()
        access_token = input("Digite Access Token (opcional): ").strip()
        access_secret = input("Digite Access Token Secret (opcional): ").strip()

        config = {'X_BEARER_TOKEN': bearer}
        if api_key:
            config.update({
                'X_API_KEY': api_key,
                'X_API_SECRET': api_secret,
                'X_ACCESS_TOKEN': access_token,
                'X_ACCESS_TOKEN_SECRET': access_secret
            })
        return config

    return {}

def configure_whatsapp():
    """Configura WhatsApp"""
    print("\n📱 CONFIGURAÇÃO DO WHATSAPP (Opcional - Complexo)")
    print("-" * 30)
    print("WhatsApp Business API é complexo de configurar.")
    print("Recomendamos usar Telegram para começar.")
    print("Consulte docs/setup-credenciais.md para instruções detalhadas.\n")

    choice = input("Deseja configurar WhatsApp agora? (y/N): ").strip().lower()
    if choice == 'y':
        phone_id = input("Digite Phone Number ID: ").strip()
        access_token = input("Digite Access Token: ").strip()
        recipient = input("Digite seu número (+5511999999999): ").strip()

        if phone_id and access_token and recipient:
            return {
                'WHATSAPP_PHONE_NUMBER_ID': phone_id,
                'WHATSAPP_ACCESS_TOKEN': access_token,
                'WHATSAPP_RECIPIENT_NUMBER': recipient
            }

    return {}

def configure_linkedin():
    """Configura LinkedIn"""
    print("\n💼 CONFIGURAÇÃO DO LINKEDIN (Opcional - Cuidado)")
    print("-" * 30)
    print("⚠️ AVISO: LinkedIn proíbe automação.")
    print("Use apenas para testes e com muito cuidado.")
    print("Recomendamos começar sem LinkedIn.\n")

    choice = input("Deseja configurar LinkedIn? (y/N): ").strip().lower()
    if choice == 'y':
        email = input("Digite email do LinkedIn: ").strip()
        password = input("Digite senha do LinkedIn: ").strip()

        if email and password:
            return {'LINKEDIN_EMAIL': email, 'LINKEDIN_PASSWORD': password}

    return {}

def configure_basic_settings():
    """Configura configurações básicas"""
    print("\n⚙️ CONFIGURAÇÕES BÁSICAS")
    print("-" * 30)

    location = input("Localização para busca (ex: São Paulo, SP): ").strip()
    skills = input("Suas habilidades (separadas por vírgula): ").strip()
    positions = input("Cargos desejados (separados por vírgula): ").strip()

    config = {}
    if location:
        config['SEARCH_LOCATION'] = location
    if skills:
        config['MY_SKILLS'] = skills
    if positions:
        config['DESIRED_POSITION'] = positions

    return config

def main():
    """Função principal"""
    print_header()

    # Configura arquivo .env
    env_path = setup_env_file()

    # Coleta todas as configurações
    all_configs = {}

    # Configurações obrigatórias
    all_configs.update(configure_email())

    # Configurações recomendadas
    all_configs.update(configure_telegram())
    all_configs.update(configure_twitter())

    # Configurações opcionais
    all_configs.update(configure_whatsapp())
    all_configs.update(configure_linkedin())

    # Configurações básicas
    all_configs.update(configure_basic_settings())

    # Atualiza arquivo .env
    print("\n💾 Salvando configurações...")
    for key, value in all_configs.items():
        update_env_variable(env_path, key, value)

    print("✅ Configurações salvas em .env")

    # Resumo
    print(f"\n📊 RESUMO: {len(all_configs)} configurações definidas")
    for key in all_configs.keys():
        print(f"  ✅ {key}")

    print("\n🧪 PRÓXIMOS PASSOS:")
    print("1. Execute: pip install -r requirements.txt")
    print("2. Teste as credenciais: python test_credentials.py")
    print("3. Execute o bot: python main.py --search")

    print("\n📚 DOCUMENTAÇÃO:")
    print("- Guia completo: docs/setup-credenciais.md")
    print("- README: README.md")

    print("\n🎉 Configuração concluída!")

if __name__ == "__main__":
    main()
