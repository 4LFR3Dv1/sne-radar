import os
import json
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Para renderizar sem interface gráfica
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import io
import base64
from flask import Flask, jsonify, render_template_string

# Configurações
symbol = "BTCUSDT"
interval = "1m"
limit = 100
br_tz = pytz.timezone("America/Sao_Paulo")

# Estado global do sistema
sistema_estado = {
    "ativo": False,
    "ultima_atualizacao": None,
    "dados_atuais": None,
    "rupturas_detectadas": [],
    "alertas_enviados": 0,
    "inicio_execucao": None,
    "grafico_base64": None
}

# Flask app
app = Flask(__name__)

def buscar_dados_binance(symbol, interval, limit):
    """Busca dados da Binance API com pandas"""
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
        
        # Calculando indicadores técnicos
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

def plotar_candlestick(ax, df):
    """Plota candlesticks manualmente"""
    try:
        # Preparar dados
        df["timestamp"] = mdates.date2num(df.index.to_pydatetime())
        
        # Plotar candlesticks
        for i, (idx, row) in enumerate(df.iterrows()):
            timestamp = row["timestamp"]
            open_price = row["open"]
            close_price = row["close"]
            high_price = row["high"]
            low_price = row["low"]
            
            # Cor do candle
            color = 'lime' if close_price >= open_price else 'red'
            
            # Corpo do candle
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            # Plotar corpo
            ax.bar(timestamp, body_height, bottom=body_bottom, 
                   width=0.0008, color=color, alpha=0.8)
            
            # Plotar sombra
            ax.plot([timestamp, timestamp], [low_price, high_price], 
                   color=color, linewidth=1)
            
    except Exception as e:
        print(f"[ERRO] Falha ao plotar candlesticks: {e}")

def gerar_grafico(df):
    """Gera gráfico candlestick com indicadores"""
    try:
        if df.empty:
            return None
            
        # Configurar matplotlib para modo não-interativo
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        
        # Plotar candlesticks
        plotar_candlestick(ax, df)
        
        # Plotar médias móveis
        df["timestamp"] = mdates.date2num(df.index.to_pydatetime())
        ax.plot(df["timestamp"], df["EMA8"], color="white", linestyle="--", linewidth=1, label="EMA 8")
        ax.plot(df["timestamp"], df["EMA21"], color="orange", linestyle="--", linewidth=1, label="EMA 21")
        ax.plot(df["timestamp"], df["SMA200"], color="magenta", linewidth=1, label="SMA 200")
        
        # Marcar rupturas
        rupturas = df[df["ruptura"]]
        for _, linha in rupturas.iterrows():
            ax.axhline(linha["close"], color='yellow', linestyle='--', linewidth=1)
            ax.plot(linha["timestamp"], linha["close"], 'yo', markersize=8)
        
        # Configurações do gráfico
        ax.set_title(f"SNE Radar: {symbol} - {interval}\nRadar Neural Estratégico", color="yellow", fontsize=14)
        ax.set_ylabel("Preço (USDT)", color="yellow")
        ax.set_xlabel("Horário (GMT-3)", color="yellow")
        ax.tick_params(axis='x', colors='yellow')
        ax.tick_params(axis='y', colors='yellow')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.grid(True, color='gray', linestyle='--', linewidth=0.3)
        ax.legend()
        
        # Rotacionar labels do eixo X
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Converter para base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='black')
        buf.seek(0)
        grafico_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return grafico_base64
        
    except Exception as e:
        print(f"[ERRO] Falha ao gerar gráfico: {e}")
        return None

def detectar_ruptura_gravitacional(df):
    """Detecta rupturas usando a lógica original"""
    rupturas = df[df["ruptura"]]
    
    for _, linha in rupturas.iterrows():
        preco = linha["close"]
        timestamp = linha.name.strftime('%Y-%m-%d %H:%M:%S')
        
        # Adiciona à lista de rupturas detectadas
        ruptura_info = {
            "preco": float(preco),
            "timestamp": timestamp,
            "volume": float(linha["volume"]),
            "densidade": float(linha["densidade"]),
            "ema8": float(linha["EMA8"]),
            "ema21": float(linha["EMA21"])
        }
        
        if ruptura_info not in sistema_estado["rupturas_detectadas"]:
            sistema_estado["rupturas_detectadas"].append(ruptura_info)
            sistema_estado["alertas_enviados"] += 1
            print(f"[ALERTA] Ruptura Magnética Detectada: {preco:.2f} USDT - {timestamp}")

def executar_ciclo_analise():
    """Executa um ciclo completo de análise"""
    try:
        # Busca dados
        df = buscar_dados_binance(symbol, interval, limit)
        
        if df.empty:
            print("[ERRO] DataFrame vazio")
            return
        
        # Gera gráfico
        grafico_base64 = gerar_grafico(df)
        if grafico_base64:
            sistema_estado["grafico_base64"] = grafico_base64
        
        # Atualiza estado global
        ultimo_dado = df.iloc[-1]
        sistema_estado["dados_atuais"] = {
            "preco_atual": float(ultimo_dado["close"]),
            "volume_atual": float(ultimo_dado["volume"]),
            "ema8": float(ultimo_dado["EMA8"]),
            "ema21": float(ultimo_dado["EMA21"]),
            "sma200": float(ultimo_dado["SMA200"]),
            "densidade": float(ultimo_dado["densidade"]),
            "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
            "sinal_compra": bool(ultimo_dado["sinal_compra"]),
            "sinal_venda": bool(ultimo_dado["sinal_venda"]),
            "tendencia": "alta" if ultimo_dado["EMA8"] > ultimo_dado["EMA21"] else "baixa"
        }
        
        sistema_estado["ultima_atualizacao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Detecção de rupturas
        detectar_ruptura_gravitacional(df)
        
        print(f"[INFO] Ciclo executado: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"[ERRO] Falha no ciclo de análise: {e}")

# Rotas da API
@app.route('/')
def home():
    """Página principal com status do sistema e gráfico"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SNE Radar - Sistema Neural Estratégico</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: 'Courier New', monospace; 
                background: #0a0a0a; 
                color: #00ff00; 
                margin: 20px; 
                overflow-x: auto;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .status { 
                background: #1a1a1a; 
                padding: 20px; 
                border-radius: 10px; 
                margin: 10px 0; 
                border: 1px solid #333;
            }
            .ruptura { 
                background: #ff4444; 
                color: white; 
                padding: 10px; 
                margin: 5px 0; 
                border-radius: 5px; 
            }
            .button { 
                background: #00ff00; 
                color: black; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 5px;
                font-weight: bold;
            }
            .button:hover { background: #00cc00; }
            .grafico { 
                text-align: center; 
                margin: 20px 0; 
                background: #1a1a1a; 
                padding: 20px; 
                border-radius: 10px;
            }
            .grafico img { 
                max-width: 100%; 
                height: auto; 
                border: 1px solid #333;
            }
            .dados { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 10px; 
                margin: 10px 0; 
            }
            .dado-item { 
                background: #2a2a2a; 
                padding: 10px; 
                border-radius: 5px; 
                text-align: center;
            }
            .dado-valor { 
                font-size: 1.2em; 
                font-weight: bold; 
                color: #00ff00; 
            }
            .dado-label { 
                font-size: 0.9em; 
                color: #888; 
            }
        </style>
        <script>
            function atualizarStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('status').innerHTML = JSON.stringify(data, null, 2);
                        
                        // Atualizar dados se disponível
                        if (data.dados_atuais) {
                            document.getElementById('preco').textContent = data.dados_atuais.preco_atual.toFixed(2);
                            document.getElementById('volume').textContent = data.dados_atuais.volume_atual.toFixed(2);
                            document.getElementById('tendencia').textContent = data.dados_atuais.tendencia.toUpperCase();
                            document.getElementById('densidade').textContent = data.dados_atuais.densidade.toFixed(4);
                        }
                    });
            }
            
            function atualizarGrafico() {
                fetch('/grafico')
                    .then(response => response.json())
                    .then(data => {
                        if (data.grafico) {
                            document.getElementById('grafico-img').src = 'data:image/png;base64,' + data.grafico;
                            document.getElementById('grafico-img').style.display = 'block';
                            document.getElementById('grafico-loading').style.display = 'none';
                        }
                    });
            }
            
            // Atualizar a cada 30 segundos
            setInterval(atualizarStatus, 30000);
            setInterval(atualizarGrafico, 60000);
            
            // Atualizar imediatamente
            atualizarStatus();
            atualizarGrafico();
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SNE Radar - Sistema Neural Estratégico</h1>
            
            <div class="status">
                <h2>📊 Dados em Tempo Real</h2>
                <div class="dados">
                    <div class="dado-item">
                        <div class="dado-label">Preço BTC</div>
                        <div class="dado-valor" id="preco">--</div>
                    </div>
                    <div class="dado-item">
                        <div class="dado-label">Volume</div>
                        <div class="dado-valor" id="volume">--</div>
                    </div>
                    <div class="dado-item">
                        <div class="dado-label">Tendência</div>
                        <div class="dado-valor" id="tendencia">--</div>
                    </div>
                    <div class="dado-item">
                        <div class="dado-label">Densidade</div>
                        <div class="dado-valor" id="densidade">--</div>
                    </div>
                </div>
            </div>
            
            <div class="grafico">
                <h2>📈 Gráfico em Tempo Real</h2>
                <img id="grafico-img" src="" alt="Gráfico SNE Radar" style="display: none;">
                <div id="grafico-loading">Carregando gráfico...</div>
            </div>
            
            <div class="status">
                <h2>🎮 Controles</h2>
                <button class="button" onclick="fetch('/iniciar', {method: 'POST'})">🚀 Iniciar Radar</button>
                <button class="button" onclick="fetch('/parar', {method: 'POST'})">⏹️ Parar Radar</button>
                <button class="button" onclick="atualizarStatus(); atualizarGrafico()">🔄 Atualizar</button>
            </div>
            
            <div class="status">
                <h2>📋 Status do Sistema</h2>
                <pre id="status">Carregando...</pre>
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

@app.route('/grafico')
def grafico():
    """Retorna gráfico atual em base64"""
    if sistema_estado["grafico_base64"]:
        return jsonify({"grafico": sistema_estado["grafico_base64"]})
    return jsonify({"erro": "Gráfico não disponível"})

@app.route('/iniciar', methods=['POST'])
def iniciar_radar():
    """Inicia o radar"""
    if not sistema_estado["ativo"]:
        sistema_estado["ativo"] = True
        sistema_estado["inicio_execucao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Executa análise imediata
        executar_ciclo_analise()
        
        return jsonify({"status": "Radar iniciado com sucesso"})
    return jsonify({"status": "Radar já está ativo"})

@app.route('/parar', methods=['POST'])
def parar_radar():
    """Para o radar"""
    if sistema_estado["ativo"]:
        sistema_estado["ativo"] = False
        return jsonify({"status": "Radar parado com sucesso"})
    return jsonify({"status": "Radar já estava parado"})

@app.route('/health')
def health():
    """Health check para o Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
