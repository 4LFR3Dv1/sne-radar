#!/bin/bash

echo "🚀 Iniciando build do SNE Radar..."

# Forçar Python 3.10
echo "📦 Configurando Python 3.10..."
python3.10 --version || echo "Python 3.10 não encontrado, usando versão padrão"

# Atualizar pip e setuptools
echo "🔄 Atualizando pip e setuptools..."
pip install --upgrade pip setuptools wheel

# Instalar dependências uma por uma
echo "📚 Instalando dependências..."

echo "Instalando requests..."
pip install requests==2.31.0

echo "Instalando flask..."
pip install flask==2.3.3

echo "Instalando pytz..."
pip install pytz==2023.3

echo "Instalando numpy..."
pip install numpy==1.24.3

echo "Instalando pandas..."
pip install pandas==1.5.3

echo "Instalando matplotlib..."
pip install matplotlib==3.7.1

echo "Instalando gunicorn..."
pip install gunicorn==21.2.0

echo "✅ Build concluído com sucesso!"
