#!/bin/bash
# Script para rodar o agendador do ML Crawler com Prefect

echo "🚀 ML Crawler - Agendador com Prefect"
echo "======================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: Execute este script da raiz do projeto"
    exit 1
fi

# Ativar venv
echo "1️⃣  Ativando virtual environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Venv ativado"
    echo "   Python: $(which python3)"
else
    echo "❌ Erro: Venv não encontrado em .venv/"
    exit 1
fi
echo ""

# Verificar se o banco está rodando
echo "2️⃣  Verificando PostgreSQL..."
if ! docker compose ps | grep -q "ml_crawler_db.*Up"; then
    echo "⚠️  PostgreSQL não está rodando. Iniciando..."
    docker compose up -d
    sleep 3
fi
echo "✅ PostgreSQL OK"
echo ""

# Informar sobre o agendamento
echo "📅 Configuração de agendamento:"
echo "   • Frequência: A cada 10 minutos"
echo "   • Timezone: America/Sao_Paulo"
echo "   • Categorias: celular, notebook, computador-desktop, eletrodoméstico, roupa, cosmética, móvel, higiene"
echo ""

# Rodar o agendador
echo "3️⃣  Iniciando o agendador..."
echo "   Pressione CTRL+C para parar"
echo ""

python3 -m src.tasks
