import pandas as pd
import requests
from datetime import datetime, timedelta
from xenos_bot import enviar_oraculo

# === Configurações ===
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 100
URL = "https://api.binance.com/api/v3/klines"

# ✅ Função para obter o fluxo de mercado em tempo real
def obter_fluxo_mercado():
    """
    Busca dados do mercado em tempo real da Binance e retorna um DataFrame
    estruturado para análise gravitacional.
    """
    print("[SNE] 🔄 Buscando dados da Binance...")
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": LIMIT}
    r = requests.get(URL, params=params, timeout=10)
    data = r.json()

    # Estruturação do DataFrame
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbb", "tbq", "ignore"
    ])

    # Converte os valores para float
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

    # Converte o tempo para datetime
    df["time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("time", inplace=True)

    # Adicionar médias móveis e densidade
    df["EMA8"] = df["close"].ewm(span=8).mean()
    df["EMA21"] = df["close"].ewm(span=21).mean()
    df["SMA200"] = df["close"].rolling(window=20).mean()
    df["densidade"] = 1 / (abs(df["EMA8"] - df["EMA21"]) + abs(df["EMA21"] - df["SMA200"]) + 1e-6)

    print("[SNE] ✅ Dados do mercado carregados com sucesso.")
    return df
def analisar_fluxo_mental(df):
    alertas = []

    # 1️⃣ Zonas de Congestão Magnética (compressão de médias)
    compressao = (
        abs(df["EMA8"] - df["EMA21"]) +
        abs(df["EMA21"] - df["SMA200"])
    )
    if compressao.iloc[-1] < compressao.rolling(window=10).mean().iloc[-1] * 0.5:
        mensagem = "[ALERTA] Preço se aproximando de zona de congestão magnética."
        alertas.append(mensagem)

    # 2️⃣ Túneis gravitacionais (alta densidade com baixo volume)
    if df["densidade"].iloc[-1] > df["densidade"].quantile(0.9) and df["volume"].iloc[-1] < df["volume"].quantile(0.4):
        mensagem = "[ANÁLISE] Túneis gravitacionais ativos: movimento pode ganhar propulsão."
        alertas.append(mensagem)

    # 3️⃣ Ressonância com padrões históricos
    for i in range(len(df) - 30):
        trecho_antigo = df["close"].iloc[i:i+10].pct_change().dropna()
        trecho_recente = df["close"].iloc[-10:].pct_change().dropna()
        erro = abs(trecho_antigo.values - trecho_recente.values).mean()
        if erro < 0.012:
            data_similar = df.index[i].strftime('%Y-%m-%d %H:%M')
            mensagem = f"[RESSONÂNCIA HISTÓRICA] Padrão de movimento semelhante ao de {data_similar}"
            alertas.append(mensagem)
            break

    # ✅ Exibir os alertas no terminal
    for alerta in alertas:
        print(alerta)

    # ✅ Enviar para o Telegram
    for alerta in alertas:
        try:
            enviar_oraculo(alerta)
            print(f"[DEBUG] Envio para Telegram bem-sucedido: {alerta}")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar alerta para o Telegram: {e}")
    
    # ✅ Retorna os alertas para envio estratégico
    return alertas
