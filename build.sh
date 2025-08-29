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

echo "Instalando setuptools e wheel..."
pip install setuptools>=61.0.0 wheel>=0.37.0

echo "Instalando requests..."
pip install requests==2.31.0

echo "Instalando flask..."
pip install flask==2.3.3

echo "Instalando flask-socketio..."
pip install flask-socketio==5.3.6

echo "Instalando pytz..."
pip install pytz==2023.3

echo "Instalando numpy..."
pip install numpy==1.24.3

echo "Instalando pandas..."
pip install pandas==1.5.3

echo "Instalando plotly..."
pip install plotly==5.17.0

echo "Instalando python-telegram-bot..."
pip install python-telegram-bot==20.7

echo "Instalando gunicorn..."
pip install gunicorn==21.2.0

echo "Instalando eventlet..."
pip install eventlet==0.33.3

echo "✅ Build concluído com sucesso!"
