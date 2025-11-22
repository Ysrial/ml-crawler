#!/bin/bash

# Script para rodar o dashboard Streamlit

echo "🚀 Iniciando Monitorador de Preços..."
echo ""
echo "✅ PostgreSQL deve estar rodando em localhost:5432"
echo "✅ Variáveis de ambiente carregadas do .env"
echo ""
echo "📊 Dashboard disponível em: http://localhost:8501"
echo ""

# Carrega variáveis de ambiente
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "✅ Arquivo .env carregado"
else
    echo "⚠️  Arquivo .env não encontrado. Usando valores padrão."
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=ml_crawler
    export DB_USER=postgres
    export DB_PASSWORD=postgres
fi

echo ""
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Inicia o Streamlit
streamlit run --logger.level=debug src/app.py
