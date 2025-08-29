import os
import json
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import pytz
import asyncio
from flask import Flask, jsonify, render_template_string
import threading
import time

# Importações dos módulos existentes
from backtest import executar_backtest, estado
from mente_fluida import mente_fluidica_verificar_resonancia
from mente_fluida_ciclica import mente_fluidica_detectar_ciclos
from fluxo_mental import analisar_fluxo_mental
from catalogo_magnetico import atualizar_catalogo, exibir_zonas_relevantes
from xenos_bot import (
    iniciar_oraculo, enviar_oraculo,
    gerar_codice_fluxo, enviar_log_rupturas,
    enviar_alerta_tatico, enviar_resumo_estrategico
)

# Configurações
symbol = "BTCUSDT"
interval = "1m"
limit = 100
br_tz = pytz.timezone("America/Sao_Paulo")
CAMINHO_LOG_ALERTAS = "logs/rupturas_criticas.log"
os.makedirs("logs", exist_ok=True)

# Estado global do sistema
sistema_estado = {
    "ativo": False,
    "ultima_atualizacao": None,
    "dados_atuais": None,
    "rupturas_detectadas": [],
    "alertas_enviados": 0,
    "inicio_execucao": None
}

# Flask app
app = Flask(__name__)

def buscar_dados_binance(symbol, interval, limit):
    """Busca dados da Binance API"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = requests.get(url, params=params, timeout=10).json()
        
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbb", "tbq", "ignore"
        ])
        
        df["time"] = pd.to_datetime(df["open_time"], unit="ms").dt.tz_localize("UTC").dt.tz_convert(br_tz)
        df = df[["time", "open", "high", "low", "close", "volume", "trades"]].astype({
            "open": float, "high": float, "low": float, "close": float,
            "volume": float, "trades": int
        })
        df.set_index("time", inplace=True)
        
        # Calculando indicadores
        df["EMA8"] = df["close"].ewm(span=8).mean()
        df["EMA21"] = df["close"].ewm(span=21).mean()
        df["SMA200"] = df["close"].rolling(window=20).mean()
        df["densidade"] = 1 / (abs(df["EMA8"] - df["EMA21"]) + abs(df["EMA21"] - df["SMA200"]) + 1e-6)
        
        # Detecção de rupturas
        df["ruptura"] = (df["densidade"].diff().abs() > df["densidade"].diff().abs().quantile(0.98)) & \
                        (df["volume"] > df["volume"].quantile(0.9))
        
        df["sinal_compra"] = (df["EMA8"] > df["EMA21"]) & (df["EMA8"].shift(1) <= df["EMA21"].shift(1))
        df["sinal_venda"] = (df["EMA8"] < df["EMA21"]) & (df["EMA8"].shift(1) >= df["EMA21"].shift(1))
        
        return df
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados: {e}")
        return pd.DataFrame()

def buscar_book(symbol):
    """Busca book de ordens da Binance"""
    try:
        url = f"https://api.binance.com/api/v3/depth"
        params = {"symbol": symbol, "limit": 100}
        data = requests.get(url, params=params, timeout=10).json()
        bids = np.array(data["bids"], dtype=float)
        asks = np.array(data["asks"], dtype=float)
        return bids, asks
    except Exception as e:
        print(f"[ERRO] Falha ao buscar book: {e}")
        return np.array([]), np.array([])

def detectar_ruptura_gravitacional(df):
    """Detecta rupturas e envia alertas"""
    rupturas = df[df["ruptura"]]
    
    for _, linha in rupturas.iterrows():
        preco = linha["close"]
        timestamp = linha.name.strftime('%Y-%m-%d %H:%M:%S')
        
        # Adiciona à lista de rupturas detectadas
        ruptura_info = {
            "preco": float(preco),
            "timestamp": timestamp,
            "volume": float(linha["volume"]),
            "densidade": float(linha["densidade"])
        }
        
        if ruptura_info not in sistema_estado["rupturas_detectadas"]:
            sistema_estado["rupturas_detectadas"].append(ruptura_info)
            sistema_estado["alertas_enviados"] += 1
            
            # Envia alerta para Telegram
            mensagem = f"⚡ Ruptura Magnética Detectada!\n💰 Preço: {preco:.2f} USDT\n🕰 Hora: {timestamp}"
            try:
                asyncio.run(enviar_oraculo(mensagem))
                print(f"[TELEGRAM] Ruptura enviada: {preco:.2f} USDT")
            except Exception as e:
                print(f"[ERRO] Falha ao enviar alerta: {e}")

def executar_ciclo_analise():
    """Executa um ciclo completo de análise"""
    try:
        # Busca dados
        df = buscar_dados_binance(symbol, interval, limit)
        bids, asks = buscar_book(symbol)
        
        if df.empty:
            print("[ERRO] DataFrame vazio")
            return
        
        # Atualiza estado global
        sistema_estado["dados_atuais"] = {
            "preco_atual": float(df["close"].iloc[-1]),
            "volume_atual": float(df["volume"].iloc[-1]),
            "ema8": float(df["EMA8"].iloc[-1]),
            "ema21": float(df["EMA21"].iloc[-1]),
            "sma200": float(df["SMA200"].iloc[-1]),
            "densidade": float(df["densidade"].iloc[-1]),
            "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
            "sinal_compra": bool(df["sinal_compra"].iloc[-1]),
            "sinal_venda": bool(df["sinal_venda"].iloc[-1])
        }
        
        sistema_estado["ultima_atualizacao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Detecção de rupturas
        detectar_ruptura_gravitacional(df)
        
        # Execução dos módulos estratégicos
        preco_atual = df["close"].iloc[-1]
        timestamp_atual = df.index[-1]
        
        # Mente Estratégica
        mente_fluidica_verificar_resonancia(preco_atual, timestamp_atual)
        mente_fluidica_detectar_ciclos(df)
        analisar_fluxo_mental(df)
        
        # Atualização do Catálogo
        atualizar_catalogo(df)
        
        # Backtest
        executar_backtest(df)
        
        print(f"[INFO] Ciclo executado: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"[ERRO] Falha no ciclo de análise: {e}")

def loop_principal():
    """Loop principal do sistema"""
    while sistema_estado["ativo"]:
        executar_ciclo_analise()
        time.sleep(60)  # Executa a cada minuto

# Rotas da API
@app.route('/')
def home():
    """Página principal com status do sistema"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SNE Radar - Status</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #00ff00; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { background: #2a2a2a; padding: 20px; border-radius: 10px; margin: 10px 0; }
            .ruptura { background: #ff4444; color: white; padding: 10px; margin: 5px 0; border-radius: 5px; }
            .button { background: #00ff00; color: black; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .button:hover { background: #00cc00; }
        </style>
        <script>
            function atualizarStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('status').innerHTML = JSON.stringify(data, null, 2);
                    });
            }
            setInterval(atualizarStatus, 30000); // Atualiza a cada 30 segundos
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SNE Radar - Sistema Neural Estratégico</h1>
            <div class="status">
                <h2>Status do Sistema</h2>
                <pre id="status">Carregando...</pre>
            </div>
            <div class="status">
                <h2>Controles</h2>
                <button class="button" onclick="fetch('/iniciar', {method: 'POST'})">Iniciar Radar</button>
                <button class="button" onclick="fetch('/parar', {method: 'POST'})">Parar Radar</button>
                <button class="button" onclick="atualizarStatus()">Atualizar Status</button>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/status')
def status():
    """Retorna status atual do sistema"""
    return jsonify(sistema_estado)

@app.route('/dados')
def dados():
    """Retorna dados atuais do mercado"""
    if sistema_estado["dados_atuais"]:
        return jsonify(sistema_estado["dados_atuais"])
    return jsonify({"erro": "Nenhum dado disponível"})

@app.route('/rupturas')
def rupturas():
    """Retorna histórico de rupturas"""
    return jsonify(sistema_estado["rupturas_detectadas"])

@app.route('/iniciar', methods=['POST'])
def iniciar_radar():
    """Inicia o radar"""
    if not sistema_estado["ativo"]:
        sistema_estado["ativo"] = True
        sistema_estado["inicio_execucao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Inicia o loop em thread separada
        thread = threading.Thread(target=loop_principal, daemon=True)
        thread.start()
        
        # Inicia componentes assíncronos
        try:
            asyncio.run(iniciar_oraculo())
            asyncio.run(enviar_oraculo("🚀 SNE Radar iniciado no Render. Sistema ativo e monitorando."))
        except Exception as e:
            print(f"[ERRO] Falha ao iniciar oráculo: {e}")
        
        return jsonify({"status": "Radar iniciado com sucesso"})
    return jsonify({"status": "Radar já está ativo"})

@app.route('/parar', methods=['POST'])
def parar_radar():
    """Para o radar"""
    if sistema_estado["ativo"]:
        sistema_estado["ativo"] = False
        
        # Envia mensagem de encerramento
        try:
            asyncio.run(enviar_oraculo("🛑 SNE Radar encerrado. Sistema em standby."))
        except Exception as e:
            print(f"[ERRO] Falha ao enviar mensagem de encerramento: {e}")
        
        return jsonify({"status": "Radar parado com sucesso"})
    return jsonify({"status": "Radar já estava parado"})

@app.route('/health')
def health():
    """Health check para o Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
