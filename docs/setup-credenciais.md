# 🔑 Guia Completo: Como Obter Credenciais das APIs

Este guia te ajudará a obter todas as credenciais necessárias para o JobHunter Bot funcionar com LinkedIn, X (Twitter) e WhatsApp.

## 📧 Email (Gmail) - MAIS FÁCIL

### 1. Configurar senha de app no Gmail
1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas** (ative se não estiver)
3. Procure por **Senhas de app**
4. Selecione **Email** como app e **Outro** como dispositivo
5. Digite "JobHunter Bot"
6. **Copie a senha gerada** (16 caracteres)

```bash
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop  # Senha de app gerada
```

## 💼 LinkedIn - INTERMEDIÁRIO

### ⚠️ Importante sobre LinkedIn
O LinkedIn tem políticas rigorosas contra scraping automatizado. Recomendamos:

#### Opção 1: Scraping Manual (Mais Seguro)
- Use apenas busca manual no LinkedIn
- Configure alertas de vagas no próprio LinkedIn
- Use o bot apenas para outras plataformas

#### Opção 2: LinkedIn API Oficial (Limitada)
1. Acesse [developer.linkedin.com](https://developer.linkedin.com)
2. Crie um app
3. **PROBLEMA**: A API de Jobs não está mais disponível para novos desenvolvedores

#### Opção 3: Scraping Cuidadoso (Risco)
```bash
# Use suas credenciais normais, mas com MUITO cuidado
LINKEDIN_EMAIL=seu-email@linkedin.com
LINKEDIN_PASSWORD=sua-senha

# Configure delays entre requests (já implementado no código)
```

**⚠️ AVISO**: Use por sua conta e risco. LinkedIn pode banir contas por automação.

## 🐦 X (Twitter) API - INTERMEDIÁRIO

### 1. Criar conta de desenvolvedor
1. Acesse [developer.twitter.com](https://developer.twitter.com)
2. Clique em **Sign up** e faça login com sua conta do X
3. Escolha **Hobbyist** → **Making a bot**

### 2. Criar um projeto
1. Nome do projeto: "JobHunter Bot"
2. Descrição: "Bot para buscar vagas de emprego no Twitter"
3. **Use case**: "Exploring the API"

### 3. Criar um app
1. Nome do app: "jobhunter-bot"
2. Salve as **API Keys** geradas:

```bash
X_API_KEY=sua-api-key-aqui
X_API_SECRET=sua-api-secret-aqui
```

### 4. Gerar tokens de acesso
1. No painel do app, vá em **Keys and tokens**
2. Clique em **Generate** em "Access Token and Secret"
3. Salve os tokens:

```bash
X_ACCESS_TOKEN=seu-access-token
X_ACCESS_TOKEN_SECRET=seu-access-token-secret
```

### 5. Bearer Token
1. Ainda em **Keys and tokens**
2. Copie o **Bearer Token**:

```bash
X_BEARER_TOKEN=seu-bearer-token
```

## 📱 WhatsApp Business API - MAIS COMPLEXO

### Opção 1: Meta for Developers (Gratuito, mas complexo)

#### 1. Criar conta Meta for Developers
1. Acesse [developers.facebook.com](https://developers.facebook.com)
2. Crie uma conta ou faça login
3. Clique em **My Apps** → **Create App**
4. Escolha **Business** como tipo de app

#### 2. Adicionar WhatsApp Business
1. No painel do app, clique em **Add Product**
2. Procure **WhatsApp** e clique em **Set up**
3. Siga o setup inicial

#### 3. Configurar número de telefone
1. Em **WhatsApp** → **Getting Started**
2. Adicione um número de telefone business
3. **IMPORTANTE**: Não pode ser um número já usado no WhatsApp pessoal

#### 4. Obter credenciais
```bash
# No painel WhatsApp → Getting Started
WHATSAPP_PHONE_NUMBER_ID=123456789  # Phone Number ID
WHATSAPP_ACCESS_TOKEN=EAAxxxxx     # Temporary Access Token

# Seu número para receber mensagens (com código do país)
WHATSAPP_RECIPIENT_NUMBER=+5511999999999
```

#### 5. Gerar token permanente
1. Vá em **WhatsApp** → **Configuration**
2. Configure um **System User** com permissões
3. Gere um token permanente

### Opção 2: Telegram (MUITO MAIS FÁCIL!)

Como o WhatsApp é complexo, recomendo usar Telegram:

#### 1. Criar bot no Telegram
1. Abra o Telegram e procure por **@BotFather**
2. Digite `/newbot`
3. Escolha um nome: "JobHunter Bot"
4. Escolha um username: "jobhunter_bot_seu_nome"
5. **Copie o token** fornecido

#### 2. Obter seu Chat ID
1. Envie uma mensagem para seu bot
2. Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Procure por `"chat":{"id":123456789}`

```bash
TELEGRAM_BOT_TOKEN=123456:ABCDEFxxxxxx
TELEGRAM_CHAT_ID=123456789
```

## 🚀 Configuração Rápida para Começar

### Configuração Mínima (Funcional)
```bash
# Email (obrigatório para candidaturas)
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-app-gmail

# Telegram (mais fácil que WhatsApp)
TELEGRAM_BOT_TOKEN=seu-token-telegram
TELEGRAM_CHAT_ID=seu-chat-id

# X/Twitter (para buscar vagas)
X_BEARER_TOKEN=seu-bearer-token

# LinkedIn (opcional, use com cuidado)
# LINKEDIN_EMAIL=seu-email@linkedin.com
# LINKEDIN_PASSWORD=sua-senha
```

### Configuração Completa
```bash
# Todas as credenciais acima +
X_API_KEY=sua-api-key
X_API_SECRET=sua-api-secret
X_ACCESS_TOKEN=seu-access-token
X_ACCESS_TOKEN_SECRET=seu-access-token-secret

# WhatsApp (se conseguir configurar)
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_RECIPIENT_NUMBER=+5511999999999
```

## 🧪 Como Testar

### 1. Testar Email
```bash
python -c "
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

msg = MIMEText('Teste do JobHunter Bot')
msg['Subject'] = 'Teste'
msg['From'] = os.getenv('EMAIL_USER')
msg['To'] = os.getenv('NOTIFICATION_EMAIL')

with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
    server.starttls()
    server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
    server.send_message(msg)
print('✅ Email funcionando!')
"
```

### 2. Testar Telegram
```bash
python -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {'chat_id': chat_id, 'text': '🤖 JobHunter Bot funcionando!'}

response = requests.post(url, data=data)
print('✅ Telegram funcionando!' if response.ok else '❌ Erro no Telegram')
"
```

### 3. Testar X (Twitter)
```bash
python -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {'Authorization': f'Bearer {os.getenv(\"X_BEARER_TOKEN\")}'}
url = 'https://api.twitter.com/2/tweets/search/recent'
params = {'query': 'python developer jobs', 'max_results': 10}

response = requests.get(url, headers=headers, params=params)
print('✅ X/Twitter funcionando!' if response.ok else '❌ Erro no Twitter')
"
```

## 📝 Ordem Recomendada para Setup

1. **Gmail** (5 minutos) ✅ Essencial
2. **Telegram** (10 minutos) ✅ Muito recomendado
3. **X/Twitter** (20 minutos) ✅ Boa fonte de vagas
4. **LinkedIn** (Use com cuidado) ⚠️ Opcional
5. **WhatsApp** (1-2 horas) 😅 Se tiver paciência

## 🆘 Problemas Comuns

### Email não funciona
- Verifique se a verificação em duas etapas está ativa
- Use senha de app, não sua senha normal
- Verifique se o Gmail permite apps menos seguros

### Telegram não funciona
- Verifique se você enviou pelo menos uma mensagem para o bot
- Use `/start` no bot antes de testar
- Confirme se o token está correto

### X/Twitter rate limit
- A API gratuita tem limite de 300 requests por 15 minutos
- Implemente delays entre requests
- Use apenas Bearer Token para começar

### LinkedIn bloqueia
- Use VPN se necessário
- Adicione delays maiores entre requests
- Considere usar apenas manualmente

---

Precisa de ajuda com alguma configuração específica? 🤔
