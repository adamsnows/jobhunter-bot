# 🤖 JobHunter Bot

Um bot inteligente em Python para buscar automaticamente vagas de emprego baseadas em suas qualificações e preferências.

## 📋 Características

- 🔍 **Busca automatizada** em múltiplas plataformas de emprego
- 🎯 **Filtragem inteligente** baseada em suas habilidades e preferências
- 📧 **Notificações automáticas** via email, Telegram ou Slack
- 🚀 **Candidatura automática** com envio de currículo e carta de apresentação
- 📝 **Templates personalizáveis** para emails de candidatura
- 🎨 **Geração automática** de cartas de apresentação baseadas na vaga
- 🕐 **Execução agendada** para busca e candidatura contínua
- 📊 **Análise de mercado** com estatísticas das vagas encontradas
- 💾 **Armazenamento** de vagas para evitar duplicatas
- 📈 **Tracking de candidaturas** enviadas e respostas
- 🌍 **Suporte multilíngua** (PT-BR e EN)

## 🛠️ Tecnologias Utilizadas

- **Python 3.9+**
- **Web Scraping**: BeautifulSoup4, Selenium
- **APIs**: requests para integração com plataformas
- **Email automation**: smtplib, email-templates
- **Document processing**: python-docx, PyPDF2 para manipulação de currículos
- **Template engine**: Jinja2 para geração de cartas personalizadas
- **Agendamento**: schedule
- **Banco de dados**: SQLite (local) ou PostgreSQL (produção)
- **Notificações**: SMTP, Telegram Bot API
- **Análise de texto**: NLTK/spaCy para matching de skills

## 🚀 Plataformas Suportadas

### Implementadas
- [ ] **LinkedIn Jobs**
- [ ] **Indeed**
- [ ] **Glassdoor**
- [ ] **InfoJobs** (Brasil)
- [ ] **Catho** (Brasil)

### Planejadas
- [ ] **AngelList** (Startups)
- [ ] **Stack Overflow Jobs**
- [ ] **GitHub Jobs**
- [ ] **Remote.co**

## 📦 Instalação

### Pré-requisitos
```bash
# Python 3.9 ou superior
python --version

# Git
git --version
```

### Setup do Projeto
```bash
# Clone o repositório
git clone https://github.com/your-username/jobhunter-bot.git
cd jobhunter-bot

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

```bash
# Clone o repositório
git clone https://github.com/your-username/jobhunter-bot.git
cd jobhunter-bot

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Crie as pastas necessárias
mkdir -p documents templates data/logs

# Adicione seus documentos
# - Coloque seu currículo em documents/curriculo.pdf
# - Personalize os templates em templates/
```

### Dependencies (`requirements.txt`)
```txt
# Web scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.0
lxml==4.9.3

# Email and templates
Jinja2==3.1.2
python-dotenv==1.0.0

# Document processing
python-docx==0.8.11
PyPDF2==3.0.1
reportlab==4.0.4

# Database
SQLAlchemy==2.0.21
sqlite3  # Built-in

# NLP and text processing
nltk==3.8.1
spacy==3.7.2
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1

# Scheduling and automation
schedule==1.2.0
APScheduler==3.10.4

# Notifications
telebot==0.0.5

# Web framework (future)
flask==2.3.3
flask-sqlalchemy==3.0.5

# Testing
pytest==7.4.2
pytest-mock==3.11.1

# Logging and monitoring
loguru==0.7.2

# Utilities
python-dateutil==2.8.2
pytz==2023.3
```

## ⚙️ Configuração

### Arquivo `.env`
```bash
# Configurações gerais
SEARCH_LOCATION=São Paulo, SP
SEARCH_RADIUS=50

# Suas habilidades (separadas por vírgula)
MY_SKILLS=Python,Django,FastAPI,PostgreSQL,Docker,AWS

# Cargo desejado
DESIRED_POSITION=Desenvolvedor Python,Python Developer,Backend Developer

# Faixa salarial (opcional)
MIN_SALARY=5000
MAX_SALARY=15000

# Configurações de email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-app
NOTIFICATION_EMAIL=seu-email@gmail.com

# Telegram Bot (opcional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Configurações de candidatura automática
AUTO_APPLY_ENABLED=true
MAX_APPLICATIONS_PER_DAY=10
MIN_JOB_MATCH_SCORE=0.7

# Caminhos dos documentos
RESUME_PATH=./documents/curriculo.pdf
COVER_LETTER_TEMPLATE=./templates/carta_apresentacao.txt
PORTFOLIO_URL=https://seu-portfolio.com

# LinkedIn (opcional - para scraping avançado)
LINKEDIN_EMAIL=seu-email@linkedin.com
LINKEDIN_PASSWORD=sua-senha

# Configurações de execução
SEARCH_INTERVAL_MINUTES=30
MAX_JOBS_PER_SEARCH=50
```

### Configuração do Profile
```python
# config/profile.py
PROFILE = {
    "name": "Seu Nome",
    "skills": [
        "Python", "Django", "FastAPI", "Flask",
        "PostgreSQL", "MongoDB", "Redis",
        "Docker", "Kubernetes", "AWS", "GCP",
        "React", "JavaScript", "HTML", "CSS"
    ],
    "experience_years": 3,
    "education": "Ciência da Computação",
    "languages": ["Português", "Inglês"],
    "location": "São Paulo, SP",
    "remote_ok": True,
    "salary_range": {
        "min": 5000,
        "max": 15000,
        "currency": "BRL"
    },
    "contact": {
        "email": "seu-email@exemplo.com",
        "phone": "+55 11 99999-9999",
        "linkedin": "https://linkedin.com/in/seu-perfil",
        "github": "https://github.com/seu-usuario"
    },
    "auto_apply": {
        "enabled": True,
        "max_per_day": 10,
        "min_match_score": 0.7,
        "blacklist_companies": ["Empresa X", "Empresa Y"]
    }
}
```

## 🎯 Como Usar

### Templates de Candidatura

#### Template de Carta de Apresentação (`templates/carta_apresentacao.txt`)
```text
Prezado(a) Recrutador(a),

Meu nome é {{NOME}} e tenho {{EXPERIENCIA_ANOS}} anos de experiência em desenvolvimento de software. 

Estou muito interessado(a) na vaga de {{CARGO}} na {{EMPRESA}}. Acredito que minhas habilidades em {{SKILLS_MATCH}} se alinham perfeitamente com os requisitos da posição.

{{PARAGRAFO_PERSONALIZADO}}

Principais qualificações:
{{QUALIFICACOES}}

Estou disponível para uma conversa e ansioso(a) para contribuir com o sucesso da {{EMPRESA}}.

Atenciosamente,
{{NOME}}
{{CONTATO}}
```

#### Template de Email (`templates/email_candidatura.html`)
```html
<h2>Candidatura para {{CARGO}} - {{EMPRESA}}</h2>

<p>Prezado(a) time de recrutamento,</p>

<p>{{CARTA_APRESENTACAO}}</p>

<p><strong>Documentos em anexo:</strong></p>
<ul>
    <li>Currículo atualizado</li>
    <li>Portfolio (quando aplicável)</li>
</ul>

<p><strong>Contatos:</strong><br>
📧 {{EMAIL}}<br>
📱 {{TELEFONE}}<br>
💼 {{LINKEDIN}}<br>
🔗 {{PORTFOLIO_URL}}</p>

<p>Aguardo seu retorno!</p>
```

### Execução Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar busca única
python main.py --search

# Executar busca e candidatura automática
python main.py --search --auto-apply

# Executar apenas candidaturas (para vagas já encontradas)
python main.py --apply-only

# Executar com modo verbose
python main.py --search --verbose

# Testar envio de email (sem candidatar)
python main.py --test-email --job-id=123

# Executar análise de mercado
python main.py --analyze

# Ver estatísticas de candidaturas
python main.py --stats --applications
```

### Execução Automática
```bash
# Iniciar bot em modo daemon
python main.py --daemon

# Parar o daemon
python main.py --stop
```

### Interface Web (Planejada)
```bash
# Iniciar interface web
python app.py
# Acesse: http://localhost:5000
```

## 📊 Estrutura do Projeto

```
jobhunter-bot/
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── job_hunter.py          # Classe principal do bot
│   │   ├── applicant.py           # Sistema de candidatura automática
│   │   └── scheduler.py           # Agendamento de tarefas
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py        # Classe base para scrapers
│   │   ├── linkedin_scraper.py    # Scraper do LinkedIn
│   │   ├── indeed_scraper.py      # Scraper do Indeed
│   │   └── infojobs_scraper.py    # Scraper do InfoJobs
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py                 # Modelo de vaga
│   │   ├── application.py         # Modelo de candidatura
│   │   └── database.py            # Configuração do banco
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_notifier.py      # Notificações por email
│   │   └── telegram_notifier.py   # Notificações por Telegram
│   ├── email/
│   │   ├── __init__.py
│   │   ├── email_sender.py        # Envio de emails de candidatura
│   │   ├── template_engine.py     # Geração de cartas personalizadas
│   │   └── attachment_handler.py  # Gerenciamento de anexos
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_analyzer.py       # Análise de texto e matching
│   │   ├── logger.py              # Sistema de logs
│   │   └── helpers.py             # Funções auxiliares
│   └── web/                       # Interface web (futuro)
├── config/
│   ├── __init__.py
│   ├── settings.py                # Configurações gerais
│   └── profile.py                 # Perfil do usuário
├── documents/
│   ├── curriculo.pdf              # Seu currículo em PDF
│   ├── curriculo_en.pdf           # Currículo em inglês
│   └── portfolio.pdf              # Portfolio (opcional)
├── templates/
│   ├── carta_apresentacao.txt     # Template da carta em PT-BR
│   ├── cover_letter_en.txt        # Template da carta em inglês
│   ├── email_candidatura.html     # Template do email de candidatura
│   └── email_followup.html        # Template de follow-up
├── data/
│   ├── jobs.db                    # Banco SQLite local
│   ├── applications.db            # Histórico de candidaturas
│   └── logs/                      # Arquivos de log
├── tests/
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_models.py
│   └── test_notifications.py
├── docs/                          # Documentação adicional
├── requirements.txt               # Dependências Python
├── .env.example                   # Exemplo de configuração
├── .gitignore
├── main.py                        # Ponto de entrada
└── README.md
```

## 🔧 Funcionalidades Principais

### 1. Busca de Vagas
- Scraping automatizado de sites de emprego
- Integração com APIs oficiais quando disponível
- Filtragem por localização, salário e habilidades
- Detecção de duplicatas

### 2. Candidatura Automática
- Envio automático de currículo e carta de apresentação
- Geração personalizada de cartas baseada na vaga
- Sistema de templates customizáveis
- Controle de limites diários de candidaturas
- Blacklist de empresas indesejadas

### 3. Análise Inteligente
- Matching de habilidades usando NLP
- Cálculo de score de compatibilidade
- Análise de requisitos da vaga
- Identificação de trends do mercado

### 4. Gestão de Candidaturas
- Tracking completo de emails enviados
- Histórico de candidaturas com status
- Follow-up automático após X dias
- Relatórios de taxa de resposta

### 5. Notificações
- Email com resumo diário/semanal
- Notificações instantâneas para vagas high-match
- Alertas de candidaturas enviadas
- Integração com Telegram/Slack
- Dashboard web (planejado)

### 6. Relatórios
- Estatísticas de mercado
- Análise salarial por região/skill
- Performance de candidaturas
- Trending technologies
- Histórico de buscas

## 📈 Roadmap

### Versão 1.0 (MVP)
- [x] Estrutura básica do projeto
- [ ] Scraper do LinkedIn
- [ ] Scraper do Indeed
- [ ] Sistema de notificação por email
- [ ] Sistema de candidatura automática
- [ ] Templates de carta de apresentação
- [ ] Banco de dados SQLite
- [ ] Filtragem básica por skills

### Versão 1.1
- [ ] Scraper InfoJobs/Catho
- [ ] Notificações Telegram
- [ ] Follow-up automático
- [ ] Análise NLP avançada
- [ ] Blacklist de empresas
- [ ] Interface de linha de comando melhorada

### Versão 2.0
- [ ] Interface web para gestão de candidaturas
- [ ] Banco PostgreSQL
- [ ] API REST
- [ ] Machine Learning para recomendações
- [ ] Integração com calendário
- [ ] Analytics avançados de candidaturas

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Aviso Legal

Este bot é para uso educacional e pessoal. Respeite os termos de uso dos sites que você está fazendo scraping. Considere usar APIs oficiais quando disponíveis.

## 📞 Contato

- Autor: Adam
- Email: adaamangelow@gmail.com
- LinkedIn: https://www.linkedin.com/in/adam-neves/

---

⭐ **Se este projeto te ajudou, deixe uma star!** ⭐
