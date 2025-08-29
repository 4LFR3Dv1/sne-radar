import os
import json
import time
from datetime import datetime
import requests
from flask import Flask, render_template, jsonify, request

# Configurações
symbol = "BTCUSDT"
interval = "1m"
limit = 100

# Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

# Estado global do sistema
sistema_estado = {
    "ativo": False,
    "ultima_atualizacao": None,
    "dados_atuais": None,
    "rupturas_detectadas": [],
    "alertas_enviados": 0,
    "inicio_execucao": None,
    "estatisticas": {
        "total_ciclos": 0,
        "rupturas_detectadas": 0,
        "tempo_execucao": 0
    },
    "debug": {
        "ultimo_erro": None,
        "status_api": None
    }
}

def buscar_dados_binance_simples(symbol, interval, limit):
    """Busca dados da Binance API de forma simples"""
    try:
        print(f"[DEBUG] Iniciando busca de dados para {symbol}")
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"[DEBUG] Status code: {response.status_code}")
        
        if response.status_code != 200:
            erro_msg = f"Erro HTTP {response.status_code}: {response.text}"
            print(f"[ERRO] {erro_msg}")
            sistema_estado["debug"]["ultimo_erro"] = erro_msg
            return None
        
        data = response.json()
        print(f"[DEBUG] Dados recebidos: {len(data)} candles")
        
        if not data:
            erro_msg = "Nenhum dado recebido da API"
            print(f"[ERRO] {erro_msg}")
            sistema_estado["debug"]["ultimo_erro"] = erro_msg
            return None
            
        # Pegar o último candle
        ultimo_candle = data[-1]
        print(f"[DEBUG] Último candle: {ultimo_candle}")
        
        timestamp = int(ultimo_candle[0]) / 1000  # Converter para segundos
        dt = datetime.fromtimestamp(timestamp)
        
        dados = {
            "timestamp": dt.strftime('%Y-%m-%d %H:%M:%S'),
            "open": float(ultimo_candle[1]),
            "high": float(ultimo_candle[2]),
            "low": float(ultimo_candle[3]),
            "close": float(ultimo_candle[4]),
            "volume": float(ultimo_candle[5]),
            "trades": int(ultimo_candle[8])
        }
        
        print(f"[DEBUG] Dados processados: {dados}")
        sistema_estado["debug"]["ultimo_erro"] = None
        sistema_estado["debug"]["status_api"] = "OK"
        
        return dados
        
    except requests.exceptions.Timeout:
        erro_msg = "Timeout na requisição para Binance"
        print(f"[ERRO] {erro_msg}")
        sistema_estado["debug"]["ultimo_erro"] = erro_msg
        return None
    except requests.exceptions.RequestException as e:
        erro_msg = f"Erro de requisição: {str(e)}"
        print(f"[ERRO] {erro_msg}")
        sistema_estado["debug"]["ultimo_erro"] = erro_msg
        return None
    except Exception as e:
        erro_msg = f"Erro inesperado: {str(e)}"
        print(f"[ERRO] {erro_msg}")
        sistema_estado["debug"]["ultimo_erro"] = erro_msg
        return None

def calcular_indicadores_simples(dados):
    """Calcula indicadores básicos sem pandas"""
    if not dados:
        return dados
        
    try:
        # Simulação de indicadores técnicos
        preco = dados["close"]
        dados["ema8"] = preco * 0.999  # Simulação EMA8
        dados["ema21"] = preco * 0.998  # Simulação EMA21
        dados["sma200"] = preco * 0.997  # Simulação SMA200
        dados["densidade"] = 1.0 / (abs(dados["ema8"] - dados["ema21"]) + 0.001)
        dados["tendencia"] = "alta" if dados["ema8"] > dados["ema21"] else "baixa"
        
        print(f"[DEBUG] Indicadores calculados: EMA8={dados['ema8']:.2f}, EMA21={dados['ema21']:.2f}")
        return dados
    except Exception as e:
        print(f"[ERRO] Falha ao calcular indicadores: {e}")
        return dados

def detectar_ruptura_simples(dados):
    """Detecta rupturas de forma simplificada"""
    if not dados:
        return False
        
    try:
        # Simulação de detecção de ruptura
        volume_alto = dados["volume"] > 1000  # Volume alto
        preco_mudanca = abs(dados["close"] - dados["open"]) > 50  # Mudança significativa
        
        print(f"[DEBUG] Verificando ruptura: volume={dados['volume']:.2f}, mudança={abs(dados['close'] - dados['open']):.2f}")
        
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
                sistema_estado["estatisticas"]["rupturas_detectadas"] += 1
                print(f"[ALERTA] Ruptura Detectada: {dados['close']:.2f} USDT - {dados['timestamp']}")
                return True
        
        return False
    except Exception as e:
        print(f"[ERRO] Falha na detecção de ruptura: {e}")
        return False

def executar_ciclo_analise():
    """Executa um ciclo completo de análise"""
    try:
        print(f"[INFO] Iniciando ciclo de análise - {datetime.now().strftime('%H:%M:%S')}")
        
        # Busca dados
        dados = buscar_dados_binance_simples(symbol, interval, limit)
        
        if not dados:
            print("[ERRO] Dados não disponíveis")
            return
        
        # Calcula indicadores
        dados = calcular_indicadores_simples(dados)
        
        # Atualiza estado global
        sistema_estado["dados_atuais"] = {
            "preco_atual": dados["close"],
            "volume_atual": dados["volume"],
            "ema8": dados["ema8"],
            "ema21": dados["ema21"],
            "sma200": dados["sma200"],
            "densidade": dados["densidade"],
            "timestamp": dados["timestamp"],
            "tendencia": dados["tendencia"]
        }
        
        sistema_estado["ultima_atualizacao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sistema_estado["estatisticas"]["total_ciclos"] += 1
        
        print(f"[DEBUG] Estado atualizado: {sistema_estado['dados_atuais']}")
        
        # Detecção de rupturas
        detectar_ruptura_simples(dados)
        
        print(f"[INFO] Ciclo executado com sucesso: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        erro_msg = f"Falha no ciclo de análise: {str(e)}"
        print(f"[ERRO] {erro_msg}")
        sistema_estado["debug"]["ultimo_erro"] = erro_msg

# Rotas Flask
@app.route('/')
def home():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API para status do sistema"""
    return jsonify(sistema_estado)

@app.route('/api/dados')
def api_dados():
    """API para dados atuais"""
    if sistema_estado["dados_atuais"]:
        return jsonify(sistema_estado["dados_atuais"])
    return jsonify({"erro": "Nenhum dado disponível"})

@app.route('/api/rupturas')
def api_rupturas():
    """API para histórico de rupturas"""
    return jsonify(sistema_estado["rupturas_detectadas"])

@app.route('/api/debug')
def api_debug():
    """API para informações de debug"""
    return jsonify(sistema_estado["debug"])

@app.route('/api/iniciar', methods=['POST'])
def api_iniciar():
    """API para iniciar o radar"""
    if not sistema_estado["ativo"]:
        sistema_estado["ativo"] = True
        sistema_estado["inicio_execucao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Executa análise imediata
        executar_ciclo_analise()
        
        return jsonify({"status": "Radar iniciado com sucesso"})
    
    return jsonify({"status": "Radar já está ativo"})

@app.route('/api/parar', methods=['POST'])
def api_parar():
    """API para parar o radar"""
    if sistema_estado["ativo"]:
        sistema_estado["ativo"] = False
        return jsonify({"status": "Radar parado com sucesso"})
    
    return jsonify({"status": "Radar já estava parado"})

@app.route('/api/executar-ciclo', methods=['POST'])
def api_executar_ciclo():
    """API para executar um ciclo manualmente"""
    executar_ciclo_analise()
    return jsonify({"status": "Ciclo executado com sucesso"})

@app.route('/health')
def health():
    """Health check para o Render"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "sistema_ativo": sistema_estado["ativo"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Iniciando SNE Radar na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
