# 🤖 JobHunter Bot - Makefile
# Comandos para desenvolvimento e produção

.PHONY: help dev dev-python dev-bash dev-pnpm install clean setup test backend-diagnostic

# Cores para output
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[1;33m
NC := \033[0m

# Help - mostra comandos disponíveis
help:
	@echo ""
	@echo "${GREEN}🤖 JobHunter Bot - Comandos Disponíveis${NC}"
	@echo ""
	@echo "${BLUE}Desenvolvimento:${NC}"
	@echo "  ${YELLOW}make dev${NC}        - Inicia frontend + backend (Python)"
	@echo "  ${YELLOW}make dev-bash${NC}   - Inicia frontend + backend (Bash)"
	@echo "  ${YELLOW}make dev-pnpm${NC}   - Inicia frontend + backend (PNPM Workspace)"
	@echo "  ${YELLOW}make dev-frontend${NC} - Só frontend (Next.js)"
	@echo "  ${YELLOW}make dev-backend${NC}  - Só backend (Flask)"
	@echo ""
	@echo "${BLUE}Configuração:${NC}"
	@echo "  ${YELLOW}make setup${NC}      - Configuração inicial completa"
	@echo "  ${YELLOW}make install${NC}    - Instala dependências"
	@echo "  ${YELLOW}make clean${NC}      - Limpa cache e dependências"
	@echo ""
	@echo "${BLUE}Utilitários:${NC}"
	@echo "  ${YELLOW}make test${NC}       - Executa testes"
	@echo "  ${YELLOW}make lint${NC}       - Verifica código"
	@echo "  ${YELLOW}make logs${NC}       - Mostra logs em tempo real"
	@echo "  ${YELLOW}make backend-diagnostic${NC} - Diagnostica problemas do backend"
	@echo ""

# Desenvolvimento - Inicia ambos os serviços (método Python)
dev:
	@echo "${GREEN}🚀 Iniciando JobHunter Bot (Python)...${NC}"
	@python3 scripts/dev_server.py

# Desenvolvimento - Inicia ambos os serviços (método Bash)
dev-bash:
	@echo "${GREEN}🚀 Iniciando JobHunter Bot (Bash)...${NC}"
	@./scripts/start_dev.sh

# Só frontend
dev-frontend:
	@echo "${BLUE}🎨 Iniciando só o Frontend...${NC}"
	@cd frontend && npm run dev

# Só backend
dev-backend:
	@echo "${BLUE}🔧 Iniciando só o Backend...${NC}"
	@cd backend && source venv/bin/activate && python3 src/web/app.py

# Desenvolvimento - Inicia ambos os serviços (método PNPM)
dev-pnpm:
	@echo "${GREEN}🚀 Iniciando JobHunter Bot (PNPM Workspace)...${NC}"
	@python3 scripts/pnpm_dev_server.py

# Diagnóstico do Backend
backend-diagnostic:
	@echo "${BLUE}🩺 Executando diagnóstico do backend...${NC}"
	@python3 scripts/check_backend.py

# Configuração inicial completa
setup:
	@echo "${GREEN}⚙️ Configuração inicial do JobHunter Bot...${NC}"
	@echo "${BLUE}📦 Configurando Frontend...${NC}"
	@cd frontend && npm install
	@echo "${BLUE}🐍 Configurando Backend...${NC}"
	@cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "${GREEN}✅ Configuração concluída!${NC}"
	@echo ""
	@echo "${YELLOW}💡 Execute 'make dev' para iniciar o projeto${NC}"

# Instala dependências
install:
	@echo "${BLUE}📦 Instalando dependências...${NC}"
	@cd frontend && npm install
	@cd backend && source venv/bin/activate && pip install -r requirements.txt

# Limpa cache e dependências
clean:
	@echo "${YELLOW}🧹 Limpando cache e dependências...${NC}"
	@rm -rf frontend/node_modules
	@rm -rf frontend/.next
	@rm -rf backend/venv
	@rm -rf backend/__pycache__
	@rm -rf backend/src/**/__pycache__
	@echo "${GREEN}✅ Limpeza concluída${NC}"

# Executa testes
test:
	@echo "${BLUE}🧪 Executando testes...${NC}"
	@cd backend && source venv/bin/activate && python -m pytest tests/ -v
	@cd frontend && npm run test

# Verifica código
lint:
	@echo "${BLUE}🔍 Verificando código...${NC}"
	@cd frontend && npm run lint
	@cd backend && source venv/bin/activate && flake8 src/

# Mostra logs em tempo real
logs:
	@echo "${BLUE}📝 Monitorando logs...${NC}"
	@tail -f backend/data/logs/jobhunter.log

# Comando padrão
.DEFAULT_GOAL := help
