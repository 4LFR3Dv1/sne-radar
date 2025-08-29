import os
import json
from datetime import datetime
import requests
import pytz
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
    "inicio_execucao": None
}

# Flask app
app = Flask(__name__)

def buscar_dados_binance_simples(symbol, interval, limit):
    """Busca dados da Binance API de forma simplificada"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = requests.get(url, params=params, timeout=10).json()
        
        if not data:
            return None
            
        # Processa apenas o último candle
        ultimo_candle = data[-1]
        
        return {
            "open_time": int(ultimo_candle[0]),
            "open": float(ultimo_candle[1]),
            "high": float(ultimo_candle[2]),
            "low": float(ultimo_candle[3]),
            "close": float(ultimo_candle[4]),
            "volume": float(ultimo_candle[5]),
            "trades": int(ultimo_candle[8]),
            "timestamp": datetime.fromtimestamp(int(ultimo_candle[0])/1000, tz=br_tz).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados: {e}")
        return None

def calcular_indicadores_simples(dados):
    """Calcula indicadores básicos sem pandas"""
    try:
        # Simula cálculo de médias móveis simples
        preco_atual = dados["close"]
        
        # Indicadores simulados para demonstração
        return {
            "preco_atual": preco_atual,
            "volume_atual": dados["volume"],
            "trades": dados["trades"],
            "timestamp": dados["timestamp"],
            "tendencia": "alta" if preco_atual > 50000 else "baixa",
            "volatilidade": "alta" if dados["volume"] > 100 else "baixa"
        }
    except Exception as e:
        print(f"[ERRO] Falha ao calcular indicadores: {e}")
        return None

def detectar_ruptura_simples(dados):
    """Detecta rupturas de forma simplificada"""
    try:
        preco = dados["close"]
        volume = dados["volume"]
        
        # Lógica simples de detecção
        if volume > 50:  # Volume alto
            ruptura_info = {
                "preco": preco,
                "timestamp": dados["timestamp"],
                "volume": volume,
                "tipo": "volume_alto"
            }
            
            if ruptura_info not in sistema_estado["rupturas_detectadas"]:
                sistema_estado["rupturas_detectadas"].append(ruptura_info)
                sistema_estado["alertas_enviados"] += 1
                print(f"[ALERTA] Ruptura detectada: {preco:.2f} USDT")
                
    except Exception as e:
        print(f"[ERRO] Falha na detecção: {e}")

def executar_ciclo_analise():
    """Executa um ciclo completo de análise simplificado"""
    try:
        # Busca dados
        dados = buscar_dados_binance_simples(symbol, interval, limit)
        
        if not dados:
            print("[ERRO] Dados não disponíveis")
            return
        
        # Calcula indicadores
        indicadores = calcular_indicadores_simples(dados)
        
        if indicadores:
            # Atualiza estado global
            sistema_estado["dados_atuais"] = indicadores
            sistema_estado["ultima_atualizacao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Detecção de rupturas
            detectar_ruptura_simples(dados)
            
            print(f"[INFO] Ciclo executado: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"[ERRO] Falha no ciclo de análise: {e}")

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
