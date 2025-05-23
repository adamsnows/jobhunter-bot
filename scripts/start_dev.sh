#!/bin/bash

# 🚀 JobHunter Bot - Script de desenvolvimento
# Inicia frontend (Next.js) e backend (Flask) simultaneamente

echo "🤖 Iniciando JobHunter Bot em modo desenvolvimento..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para cleanup ao sair
cleanup() {
    echo -e "\n${YELLOW}🛑 Parando serviços...${NC}"
    # Mata todos os processos filhos
    pkill -P $$
    exit 0
}

# Trap para cleanup
trap cleanup SIGINT SIGTERM

# Verifica se estamos no diretório correto
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Erro: Execute este script a partir da raiz do projeto${NC}"
    exit 1
fi

# Navega para a raiz do projeto se necessário
if [ -d "frontend" ] && [ -d "backend" ]; then
    PROJECT_ROOT=$(pwd)
elif [ -f "../frontend/package.json" ]; then
    PROJECT_ROOT=$(dirname $(pwd))
    cd "$PROJECT_ROOT"
else
    echo -e "${RED}❌ Erro: Não foi possível encontrar os diretórios frontend e backend${NC}"
    exit 1
fi

echo -e "${BLUE}📂 Diretório do projeto: $PROJECT_ROOT${NC}"

# Verifica dependências do frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependências do frontend...${NC}"
    cd frontend && npm install && cd ..
fi

# Verifica ambiente virtual do backend
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}🐍 Criando ambiente virtual do backend...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Verifica se as portas estão livres
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Porta 3000 já está em uso (Frontend)${NC}"
    exit 1
fi

if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Porta 5001 já está em uso (Backend)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Verificações concluídas${NC}"
echo -e "${BLUE}🚀 Iniciando serviços...${NC}"

# Inicia backend em background
echo -e "${BLUE}🔧 Iniciando Backend (Flask)...${NC}"
cd backend
source venv/bin/activate
python src/web/app.py &
BACKEND_PID=$!
cd ..

# Aguarda um pouco para o backend iniciar
sleep 3

# Inicia frontend em background
echo -e "${BLUE}🎨 Iniciando Frontend (Next.js)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Aguarda os serviços iniciarem
sleep 5

echo ""
echo -e "${GREEN}🎉 JobHunter Bot iniciado com sucesso!${NC}"
echo ""
echo -e "${BLUE}📱 Frontend (Next.js):${NC} http://localhost:3000"
echo -e "${BLUE}🔧 Backend (Flask):${NC} http://localhost:5001"
echo -e "${BLUE}📊 API Health:${NC} http://localhost:5001/api/health"
echo ""
echo -e "${YELLOW}💡 Pressione Ctrl+C para parar todos os serviços${NC}"
echo ""

# Monitora os processos
wait
