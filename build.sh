#!/bin/bash
echo "🚀 Iniciando build do SNE Radar..."

# Atualizar pip
pip install --upgrade pip

# Instalar dependências uma por uma para melhor controle
echo "📦 Instalando dependências..."
pip install requests==2.31.0
pip install numpy==1.24.3
pip install pandas==1.5.3
pip install matplotlib==3.7.1
pip install pytz==2023.3
pip install flask==2.3.3
pip install websocket-client==1.6.4

echo "✅ Build concluído com sucesso!"
