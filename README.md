# 🤖 JobHunter Bot

Um bot inteligente em Python para buscar automaticamente vagas de emprego baseadas em suas qualificações e preferências.

## 📋 Características

- 🔍 **Busca automatizada** em múltiplas plataformas de emprego
- 🎯 **Filtragem inteligente** baseada em suas habilidades e preferências
- 📧 **Notificações automáticas** via email, Telegram ou Slack
- 🕐 **Execução agendada** para busca contínua
- 📊 **Análise de mercado** com estatísticas das vagas encontradas
- 💾 **Armazenamento** de vagas para evitar duplicatas
- 🌍 **Suporte multilíngua** (PT-BR e EN)

## 🛠️ Tecnologias Utilizadas

- **Python 3.9+**
- **Web Scraping**: BeautifulSoup4, Selenium
- **APIs**: requests para integração com plataformas
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

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
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
    }
}
```

## 🎯 Como Usar

### Execução Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar busca única
python main.py --search

# Executar com modo verbose
python main.py --search --verbose

# Executar análise de mercado
python main.py --analyze

# Ver estatísticas
python main.py --stats
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
│   │   └── database.py            # Configuração do banco
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_notifier.py      # Notificações por email
│   │   └── telegram_notifier.py   # Notificações por Telegram
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
├── data/
│   ├── jobs.db                    # Banco SQLite local
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

### 2. Análise Inteligente
- Matching de habilidades usando NLP
- Cálculo de score de compatibilidade
- Análise de requisitos da vaga
- Identificação de trends do mercado

### 3. Notificações
- Email com resumo diário/semanal
- Notificações instantâneas para vagas high-match
- Integração com Telegram/Slack
- Dashboard web (planejado)

### 4. Relatórios
- Estatísticas de mercado
- Análise salarial por região/skill
- Trending technologies
- Histórico de buscas

## 📈 Roadmap

### Versão 1.0 (MVP)
- [x] Estrutura básica do projeto
- [ ] Scraper do LinkedIn
- [ ] Scraper do Indeed
- [ ] Sistema de notificação por email
- [ ] Banco de dados SQLite
- [ ] Filtragem básica por skills

### Versão 1.1
- [ ] Scraper InfoJobs/Catho
- [ ] Notificações Telegram
- [ ] Análise NLP avançada
- [ ] Interface de linha de comando melhorada

### Versão 2.0
- [ ] Interface web
- [ ] Banco PostgreSQL
- [ ] API REST
- [ ] Machine Learning para recomendações
- [ ] Integração com calendário

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

- Autor: [Seu Nome]
- Email: seu-email@exemplo.com
- LinkedIn: [Seu LinkedIn]

---

⭐ **Se este projeto te ajudou, deixe uma star!** ⭐
