# 🤖 JobHunter Bot - PNPM Workspace

Este guia descreve como executar o JobHunter Bot usando o pnpm workspace.

## 📋 Pré-requisitos

- Node.js 18.0.0 ou superior
- pnpm 8.0.0 ou superior
- Python 3.9 ou superior

## 🚀 Início Rápido

```bash
# Instalar pnpm (se ainda não tiver)
npm install -g pnpm

# Clonar o repositório
git clone https://github.com/seu-usuario/jobhunter-bot.git
cd jobhunter-bot

# Instalar dependências e configurar ambiente
pnpm run setup

# Iniciar o ambiente de desenvolvimento
pnpm run dev
```

## 📦 Estrutura do Workspace

```
jobhunter-bot/
├── backend/          # Backend Flask 
├── frontend/         # Frontend Next.js (workspace package)
├── scripts/          # Scripts utilitários
├── package.json      # Configuração raiz
└── pnpm-workspace.yaml  # Configuração do workspace
```

## 🛠️ Comandos via pnpm

| Comando | Descrição |
|---------|-----------|
| `pnpm run dev` | Inicia frontend e backend simultaneamente |
| `pnpm run frontend:dev` | Inicia somente o frontend |
| `pnpm run backend:dev` | Inicia somente o backend |
| `pnpm run setup` | Configura o ambiente inteiro |
| `pnpm run build` | Faz build do frontend |
| `pnpm run start` | Inicia em modo produção |
| `pnpm run clean` | Limpa cache e arquivos temporários |

## 🧰 Utilitários Makefile

Além dos comandos pnpm, você pode usar o Makefile para tarefas comuns:

```bash
# Mostrar todos os comandos disponíveis
make help

# Iniciar com pnpm workspace
make dev-pnpm

# Alternativas de inicialização
make dev          # Usando Python
make dev-bash     # Usando Bash
```

## 🔍 Troubleshooting

**Erro ao iniciar o frontend:**
```
make clean       # Limpa caches
pnpm install     # Reinstala dependências
```

**Erro ao iniciar o backend:**
```
make clean       # Limpa o ambiente virtual
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## 📝 Notas adicionais

- O backend não é gerenciado pelo pnpm, mas os scripts no package.json raiz facilitam a interação com ele
- O frontend é executado na porta 3000 e o backend na porta 5000
- Certifique-se de que estas portas estão disponíveis antes de iniciar
