#!/bin/bash

echo "🚀 Iniciando build do SNE Radar..."

# Atualizar pip e setuptools
echo "🔄 Atualizando pip e setuptools..."
pip install --upgrade pip setuptools wheel

# Instalar dependências básicas
echo "📚 Instalando dependências..."

echo "Instalando setuptools e wheel..."
pip install setuptools>=61.0.0 wheel>=0.37.0

echo "Instalando requests..."
pip install requests==2.31.0

echo "Instalando flask..."
pip install flask==2.3.3

echo "✅ Build concluído com sucesso!"
