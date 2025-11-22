#!/bin/bash
# Script para rodar tudo facilmente

echo "🚀 ML Crawler - Startup"
echo "========================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar Docker
echo "1️⃣  Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado${NC}"
    echo "Instale em: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker OK${NC}"

# 2. Verificar Docker Compose
echo ""
echo "2️⃣  Verificando Docker Compose..."
if ! docker-compose --version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não está instalado${NC}"
    echo "Instale Docker Desktop (inclui Compose)"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose OK${NC}"

# 3. Iniciar PostgreSQL
echo ""
echo "3️⃣  Iniciando PostgreSQL..."
docker-compose up -d
sleep 3

# Verificar se está rodando
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ PostgreSQL rodando${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar PostgreSQL${NC}"
    exit 1
fi

# 4. Instalar dependências
echo ""
echo "4️⃣  Instalando dependências Python..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dependências instaladas${NC}"
else
    echo -e "${RED}❌ Erro ao instalar dependências${NC}"
    exit 1
fi

# 5. Pronto!
echo ""
echo -e "${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SETUP COMPLETO!${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"
echo ""
echo "Para iniciar o app, execute:"
echo -e "  ${YELLOW}streamlit run app.py${NC}"
echo ""
echo "O app abrirá em: http://localhost:8501"
echo ""
echo "Para parar: docker-compose down"
echo ""
