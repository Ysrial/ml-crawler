#!/bin/bash

# Script para coletar dados de todas as 6 categorias

echo "🚀 Iniciando coleta de todas as categorias..."
echo ""

# Array de categorias e URLs
declare -a categorias=(
    "celular|https://lista.mercadolivre.com.br/celular"
    "eletrodomestico|https://lista.mercadolivre.com.br/eletrodomestico"
    "roupa|https://lista.mercadolivre.com.br/roupa"
    "cosmetica|https://lista.mercadolivre.com.br/cosmetica"
    "movel|https://lista.mercadolivre.com.br/movel"
    "higiene|https://lista.mercadolivre.com.br/higiene"
)

# Para cada categoria, rodar o scraper
for categoria in "${categorias[@]}"; do
    IFS='|' read -r nome url <<< "$categoria"
    
    echo "📊 Coletando: $nome"
    echo "   URL: $url"
    
    python -m src.main "$url" 300 6
    
    echo ""
    echo "✅ $nome concluído!"
    echo "---"
    sleep 2
done

echo ""
echo "🎉 Coleta completa de todas as 6 categorias!"
echo ""
echo "📊 Dashboard disponível em: http://localhost:8501"
