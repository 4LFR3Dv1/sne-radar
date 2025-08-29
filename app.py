import os
import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils
import pytz
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging

# Configurações
symbol = "BTCUSDT"
interval = "1m"
limit = 100
br_tz = pytz.timezone("America/Sao_Paulo")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app com SocketIO
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'sne-radar-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Estado global do sistema
sistema_estado = {
    "ativo": False,
    "ultima_atualizacao": None,
    "dados_atuais": None,
    "rupturas_detectadas": [],
    "alertas_enviados": 0,
    "inicio_execucao": None,
    "grafico_html": None,
    "estatisticas": {
        "total_ciclos": 0,
        "rupturas_detectadas": 0,
        "tempo_execucao": 0
    }
}

# Thread para execução em background
thread_background = None
stop_thread = False

def buscar_dados_binance(symbol, interval, limit):
    """Busca dados da Binance API com pandas"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if not data:
            return pd.DataFrame()
        
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
        
        return df
        
    except Exception as e:
        logger.error(f"Falha ao buscar dados: {e}")
        return pd.DataFrame()

def calcular_indicadores(df):
    """Calcula indicadores técnicos"""
    if df.empty:
        return df
    
    try:
        # Médias móveis
        df["EMA8"] = df["close"].ewm(span=8).mean()
        df["EMA21"] = df["close"].ewm(span=21).mean()
        df["SMA200"] = df["close"].rolling(window=20).mean()
        
        # Densidade (indicador personalizado)
        df["densidade"] = 1 / (abs(df["EMA8"] - df["EMA21"]) + abs(df["EMA21"] - df["SMA200"]) + 1e-6)
        
        # Sinais de compra/venda
        df["sinal_compra"] = (df["EMA8"] > df["EMA21"]) & (df["EMA8"].shift(1) <= df["EMA21"].shift(1))
        df["sinal_venda"] = (df["EMA8"] < df["EMA21"]) & (df["EMA8"].shift(1) >= df["EMA21"].shift(1))
        
        # Detecção de rupturas
        df["ruptura"] = (df["densidade"].diff().abs() > df["densidade"].diff().abs().quantile(0.98)) & \
                        (df["volume"] > df["volume"].quantile(0.9))
        
        return df
        
    except Exception as e:
        logger.error(f"Erro ao calcular indicadores: {e}")
        return df

def gerar_grafico_plotly(df):
    """Gera gráfico candlestick interativo com Plotly"""
    try:
        if df.empty:
            return None
        
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'SNE Radar: {symbol} - {interval}', 'Volume'),
            row_width=[0.7, 0.3]
        )
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC',
            increasing_line_color='#00ff00',
            decreasing_line_color='#ff0000'
        ), row=1, col=1)
        
        # Médias móveis
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA8'],
            mode='lines',
            name='EMA 8',
            line=dict(color='white', width=1)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA21'],
            mode='lines',
            name='EMA 21',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['SMA200'],
            mode='lines',
            name='SMA 200',
            line=dict(color='magenta', width=1)
        ), row=1, col=1)
        
        # Marcar rupturas
        rupturas = df[df['ruptura']]
        if not rupturas.empty:
            fig.add_trace(go.Scatter(
                x=rupturas.index,
                y=rupturas['close'],
                mode='markers',
                name='Rupturas',
                marker=dict(color='yellow', size=10, symbol='diamond')
            ), row=1, col=1)
        
        # Volume
        colors = ['red' if close < open else 'green' for close, open in zip(df['close'], df['open'])]
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker_color=colors
        ), row=2, col=1)
        
        # Layout
        fig.update_layout(
            title=f'SNE Radar - Sistema Neural Estratégico<br>{symbol} - {interval}',
            yaxis_title='Preço (USDT)',
            yaxis2_title='Volume',
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Converter para HTML
        grafico_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        return grafico_html
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        return None

def detectar_ruptura_gravitacional(df):
    """Detecta rupturas usando a lógica original"""
    try:
        rupturas = df[df["ruptura"]]
        
        for idx, linha in rupturas.iterrows():
            preco = linha["close"]
            timestamp = idx.strftime('%Y-%m-%d %H:%M:%S')
            
            # Adiciona à lista de rupturas detectadas
            ruptura_info = {
                "preco": float(preco),
                "timestamp": timestamp,
                "volume": float(linha["volume"]),
                "densidade": float(linha["densidade"]),
                "ema8": float(linha["EMA8"]),
                "ema21": float(linha["EMA21"]),
                "tipo": "ruptura_gravitacional"
            }
            
            if ruptura_info not in sistema_estado["rupturas_detectadas"]:
                sistema_estado["rupturas_detectadas"].append(ruptura_info)
                sistema_estado["alertas_enviados"] += 1
                sistema_estado["estatisticas"]["rupturas_detectadas"] += 1
                
                logger.info(f"ALERTA: Ruptura Magnética Detectada: {preco:.2f} USDT - {timestamp}")
                
                # Enviar alerta via WebSocket
                socketio.emit('ruptura_detectada', ruptura_info)
                
    except Exception as e:
        logger.error(f"Erro na detecção de rupturas: {e}")

def executar_ciclo_analise():
    """Executa um ciclo completo de análise"""
    try:
        # Busca dados
        df = buscar_dados_binance(symbol, interval, limit)
        
        if df.empty:
            logger.warning("DataFrame vazio")
            return
        
        # Calcula indicadores
        df = calcular_indicadores(df)
        
        # Gera gráfico
        grafico_html = gerar_grafico_plotly(df)
        if grafico_html:
            sistema_estado["grafico_html"] = grafico_html
        
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
        sistema_estado["estatisticas"]["total_ciclos"] += 1
        
        # Detecção de rupturas
        detectar_ruptura_gravitacional(df)
        
        # Enviar atualização via WebSocket
        socketio.emit('dados_atualizados', sistema_estado["dados_atuais"])
        socketio.emit('grafico_atualizado', {'grafico': grafico_html})
        
        logger.info(f"Ciclo executado: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Falha no ciclo de análise: {e}")

def thread_analise_continua():
    """Thread para execução contínua da análise"""
    global stop_thread
    
    while not stop_thread and sistema_estado["ativo"]:
        try:
            executar_ciclo_analise()
            time.sleep(30)  # Executar a cada 30 segundos
        except Exception as e:
            logger.error(f"Erro na thread de análise: {e}")
            time.sleep(60)  # Aguardar mais tempo em caso de erro

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

@app.route('/api/grafico')
def api_grafico():
    """API para gráfico atual"""
    if sistema_estado["grafico_html"]:
        return jsonify({"grafico": sistema_estado["grafico_html"]})
    return jsonify({"erro": "Gráfico não disponível"})

@app.route('/api/iniciar', methods=['POST'])
def api_iniciar():
    """API para iniciar o radar"""
    global thread_background, stop_thread
    
    if not sistema_estado["ativo"]:
        sistema_estado["ativo"] = True
        sistema_estado["inicio_execucao"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stop_thread = False
        
        # Executa análise imediata
        executar_ciclo_analise()
        
        # Inicia thread de análise contínua
        thread_background = threading.Thread(target=thread_analise_continua)
        thread_background.daemon = True
        thread_background.start()
        
        socketio.emit('sistema_atualizado', {'status': 'iniciado'})
        return jsonify({"status": "Radar iniciado com sucesso"})
    
    return jsonify({"status": "Radar já está ativo"})

@app.route('/api/parar', methods=['POST'])
def api_parar():
    """API para parar o radar"""
    global stop_thread
    
    if sistema_estado["ativo"]:
        sistema_estado["ativo"] = False
        stop_thread = True
        
        socketio.emit('sistema_atualizado', {'status': 'parado'})
        return jsonify({"status": "Radar parado com sucesso"})
    
    return jsonify({"status": "Radar já estava parado"})

@app.route('/health')
def health():
    """Health check para o Render"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "sistema_ativo": sistema_estado["ativo"]
    })

# Eventos WebSocket
@socketio.on('connect')
def handle_connect():
    """Cliente conectado via WebSocket"""
    logger.info('Cliente WebSocket conectado')
    emit('conectado', {'mensagem': 'Conectado ao SNE Radar'})
    
    # Enviar estado atual
    if sistema_estado["dados_atuais"]:
        emit('dados_atualizados', sistema_estado["dados_atuais"])
    
    if sistema_estado["grafico_html"]:
        emit('grafico_atualizado', {'grafico': sistema_estado["grafico_html"]})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado via WebSocket"""
    logger.info('Cliente WebSocket desconectado')

@socketio.on('solicitar_dados')
def handle_solicitar_dados():
    """Cliente solicita dados atualizados"""
    if sistema_estado["dados_atuais"]:
        emit('dados_atualizados', sistema_estado["dados_atuais"])
    
    if sistema_estado["grafico_html"]:
        emit('grafico_atualizado', {'grafico': sistema_estado["grafico_html"]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando SNE Radar na porta {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
