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
    """Busca dados da Binance API de forma simples"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if not data:
            return None
            
        # Pegar o último candle
        ultimo_candle = data[-1]
        timestamp = int(ultimo_candle[0]) / 1000  # Converter para segundos
        dt = datetime.fromtimestamp(timestamp, tz=br_tz)
        
        return {
            "timestamp": dt.strftime('%Y-%m-%d %H:%M:%S'),
            "open": float(ultimo_candle[1]),
            "high": float(ultimo_candle[2]),
            "low": float(ultimo_candle[3]),
            "close": float(ultimo_candle[4]),
            "volume": float(ultimo_candle[5]),
            "trades": int(ultimo_candle[8])
        }
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados: {e}")
        return None

def calcular_indicadores_simples(dados):
    """Calcula indicadores básicos sem pandas"""
    if not dados:
        return dados
        
    # Para simplificar, vamos usar valores fixos para os indicadores
    # Em uma versão completa, isso seria calculado com pandas
    dados["ema8"] = dados["close"] * 0.99  # Simulação
    dados["ema21"] = dados["close"] * 0.98  # Simulação
    dados["sma200"] = dados["close"] * 0.97  # Simulação
    dados["densidade"] = 1.0 / (abs(dados["ema8"] - dados["ema21"]) + 0.001)
    dados["tendencia"] = "alta" if dados["ema8"] > dados["ema21"] else "baixa"
    
    return dados

def detectar_ruptura_simples(dados):
    """Detecta rupturas de forma simplificada"""
    if not dados:
        return False
        
    # Simulação de detecção de ruptura
    # Em uma versão completa, isso seria mais sofisticado
    volume_alto = dados["volume"] > 1000  # Volume alto
    preco_mudanca = abs(dados["close"] - dados["open"]) > 100  # Mudança significativa
    
    if volume_alto and preco_mudanca:
        ruptura_info = {
            "preco": dados["close"],
            "timestamp": dados["timestamp"],
            "volume": dados["volume"],
            "densidade": dados["densidade"],
            "tipo": "volume_alto"
        }
        
        if ruptura_info not in sistema_estado["rupturas_detectadas"]:
            sistema_estado["rupturas_detectadas"].append(ruptura_info)
            sistema_estado["alertas_enviados"] += 1
            print(f"[ALERTA] Ruptura Detectada: {dados['close']:.2f} USDT - {dados['timestamp']}")
            return True
    
    return False

def executar_ciclo_analise():
    """Executa um ciclo completo de análise"""
    try:
        # Busca dados
        dados = buscar_dados_binance_simples(symbol, interval, limit)
        
        if not dados:
            print("[ERRO] Dados não disponíveis")
            return
        
        # Calcula indicadores
        dados = calcular_indicadores_simples(dados)
        
        # Atualiza estado global
        sistema_estado["dados_atuais"] = dados
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
            .info { 
                background: #333; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 10px 0;
                border-left: 4px solid #00ff00;
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
                            document.getElementById('preco').textContent = data.dados_atuais.close.toFixed(2);
                            document.getElementById('volume').textContent = data.dados_atuais.volume.toFixed(2);
                            document.getElementById('tendencia').textContent = data.dados_atuais.tendencia.toUpperCase();
                            document.getElementById('densidade').textContent = data.dados_atuais.densidade.toFixed(4);
                        }
                    });
            }
            
            // Atualizar a cada 30 segundos
            setInterval(atualizarStatus, 30000);
            
            // Atualizar imediatamente
            atualizarStatus();
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SNE Radar - Sistema Neural Estratégico</h1>
            
            <div class="info">
                <h3>📊 Versão Simplificada</h3>
                <p>Esta é uma versão básica do SNE Radar funcionando no Render. 
                Os gráficos e análises avançadas serão adicionados em breve.</p>
            </div>
            
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
            
            <div class="status">
                <h2>🎮 Controles</h2>
                <button class="button" onclick="fetch('/iniciar', {method: 'POST'})">🚀 Iniciar Radar</button>
                <button class="button" onclick="fetch('/parar', {method: 'POST'})">⏹️ Parar Radar</button>
                <button class="button" onclick="atualizarStatus()">🔄 Atualizar</button>
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
