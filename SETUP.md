# 🚀 Setup Rápido com pnpm Workspace

## Pré-requisitos

- **Node.js** 18+
- **pnpm** 8+
- **Python** 3.9+

## Instalação do pnpm

```bash
# Via npm
npm install -g pnpm

# Via Homebrew (macOS)
brew install pnpm

# Via curl
curl -fsSL https://get.pnpm.io/install.sh | sh
```

## Setup Completo

```bash
# 1. Clone o repositório
git clone <repo-url>
cd jobhunter-bot

# 2. Setup completo (frontend + backend)
pnpm setup

# 3. Inicia tudo em modo desenvolvimento
pnpm dev
```

## Comandos Disponíveis

### 🚀 Desenvolvimento
```bash
pnpm dev              # Inicia frontend + backend
pnpm frontend:dev     # Apenas frontend (Next.js)
pnpm backend:dev      # Apenas backend (Flask)
```

### 🏗️ Build & Deploy
```bash
pnpm build            # Build do frontend
pnpm start            # Produção (frontend + backend)
```

### 🧹 Manutenção
```bash
pnpm clean            # Limpa cache e node_modules
pnpm check:ports      # Verifica se portas estão livres
pnpm lint             # Linter do frontend
pnpm test             # Testes
```

### 🔧 Backend específico
```bash
pnpm backend:setup    # Cria venv e instala deps Python
```

## URLs de Desenvolvimento

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

## Estrutura do Workspace

```
jobhunter-bot/
├── package.json          # Root workspace config
├── pnpm-workspace.yaml   # pnpm workspace config
├── frontend/             # Next.js app
│   └── package.json      # Frontend dependencies
├── backend/              # Flask API
│   ├── requirements.txt  # Python dependencies
│   └── venv/            # Python virtual env
└── scripts/
    └── start_backend.py  # Backend starter script
```

## Vantagens do pnpm Workspace

✅ **Comando único**: `pnpm dev` inicia tudo
✅ **Gerenciamento unificado** de dependências
✅ **Scripts organizados** por workspace
✅ **Cache inteligente** do pnpm
✅ **Builds paralelos** e otimizados

## Troubleshooting

### Porta ocupada
```bash
pnpm check:ports  # Verifica portas 3000 e 5000
```

### Reset completo
```bash
pnpm clean
pnpm setup
```

### Problemas com Python venv
```bash
rm -rf backend/venv
pnpm backend:setup
```
