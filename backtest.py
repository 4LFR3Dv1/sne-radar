from xenos_bot import (
    iniciar_oraculo, enviar_oraculo, gerar_codice_fluxo, enviar_log_rupturas,
    enviar_alerta_tatico, enviar_resumo_estrategico
)
from catalogo_magnetico import (
    exibir_zonas_relevantes, verificar_ressonancia, registrar_ruptura,
    identificar_compressao, identificar_proximidade_zona
)
from memoria_neural import capturar_memoria_mercado
from mente_fluida import mente_fluidica_verificar_resonancia
from mente_fluida_ciclica import mente_fluidica_detectar_ciclos
from mapeamento_gravitacional import detectar_zonas_criticas
from previsao_magnetica import prever_movimentos
from pulso_magnetico import detectar_pulsos_massa
from datetime import datetime
import os


CAMINHO_CODICE_FLUXO = os.path.join(os.getcwd(), "codice_fluxo.txt")

# ✅ Verifica e cria o arquivo, se não existir
if not os.path.exists(CAMINHO_CODICE_FLUXO):
    with open(CAMINHO_CODICE_FLUXO, 'w') as file:
        file.write(" Codice de Fluxo Iniciado.\n")
    print(f"✅ Arquivo de códice criado em: {CAMINHO_CODICE_FLUXO}")

# === Objeto de estado compartilhado com o main.py ===
estado = {
    "capital": 1000,
    "capital_real": 1000,
    "posicao": 0,
    "preco_medio": 0,
    "historico": [],
    "ressonancias_ignoradas": 0,
    "ultima_data_processada": None,
    "cooldown": {},
    "buffer_estrategico": [],
    "zonas_mapeadas": []
}

# === Configurações Estratégicas ===
TAKE_PROFIT = 0.02    
STOP_LOSS = 0.01      
COOLDOWN_TEMPO = 900  
VARIACAO_PRECO = 30   
LIMITE_RUPTURAS = 2   
DESVIO_MINIMO = 0.003  
PERIODO_TENDENCIA = 5  
LIMITE_COMPRESSAO = 10  
INTERVALO_ANALISE = 300  # 5 minutos
LIMITE_RUPTURAS = 2  

# === Contador de tentativas de rupturas sem sucesso
tentativas_sem_sucesso = 0
def analise_estrategica(df):
    """
    Executa uma análise profunda do mercado, identificando:
    - Zonas de suporte e resistência
    - Canais de propulsão
    - Rupturas críticas
    - Fluxo mental e ressonâncias
    """
    preco_atual = df["close"].iloc[-1]
    timestamp = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')

    # 🔍 Mapeamento Gravitacional
    zonas_criticas = mapear_zonas_criticas(df)
    canais = detectar_pulsos_massa(df)

    # 🔎 Análise de Ressonância
    ressonante = mente_fluidica_verificar_resonancia(df)

    # 🔄 Previsão de Movimentos
    movimentos_futuros = prever_movimentos(df)

    # 📡 Relatório Estratégico
    relatorio = (
        f"📊 <b>Análise Estratégica - Radar Ativado:</b>\n"
        f"🕰️ <b>Horário:</b> {timestamp}\n"
        f"💲 <b>Preço Atual:</b> {preco_atual:.2f} USDT\n\n"
        f"🔎 <b>Zonas Críticas:</b> {zonas_criticas}\n"
        f"🚀 <b>Canais de Propulsão:</b> {canais}\n"
        f"🛡️ <b>Ressonância Detected:</b> {'Sim' if ressonante else 'Não'}\n"
        f"🔄 <b>Movimentos Esperados:</b> {movimentos_futuros}\n\n"
    )

    # 🚀 Se houver zona crítica próxima, alertar no Telegram
    if zonas_criticas:
        enviar_alerta_tatico("Zona Crítica Detectada", preco_atual, timestamp, "zona")

    enviar_oraculo(relatorio)
    print(relatorio)

# ✅ Função para executar a cada 5 minutos
def iniciar_analise_estrategica():
    """
    Inicia um ciclo de análise estratégica a cada 5 minutos.
    """
    from fluxo_mental import obter_fluxo_mercado
    
    print("🔄 Iniciando análise estratégica...")
    df = obter_fluxo_mercado()
    
    if not df.empty:
        analise_estrategica(df)
    
    Timer(INTERVALO_ANALISE, iniciar_analise_estrategica).start()

# ✅ Inicia o ciclo de análise estratégica
    iniciar_analise_estrategica()

# ✅ Verifica cooldown para evitar operações repetidas
def pode_operar(preco, tipo):
    """
    Verifica se há cooldown para a operação.
    """
    tempo_atual = datetime.now()
    if tipo in estado["cooldown"]:
        ultimo_tempo, ultimo_preco = estado["cooldown"][tipo]
        if (tempo_atual - ultimo_tempo).seconds < COOLDOWN_TEMPO and abs(preco - ultimo_preco) < VARIACAO_PRECO:
            print(f"⚠️ Cooldown ativo para {tipo}. Última operação: {ultimo_preco} USDT")
            return False
    estado["cooldown"][tipo] = (tempo_atual, preco)
    return True

# ✅ Função para formatar e otimizar o log
def exibir_log_operacao(tipo, preco, timestamp, lucro=None):
    """
    Exibe no terminal o log otimizado da operação.
    """
    status = " COMPRA" if tipo == "compra" else " VENDA"
    print(f"\n[{status}] - {timestamp}")
    print(f"   ➡ Preço: {preco:.2f} USDT")

    if lucro is not None:
        status_lucro = " Lucro" if lucro > 0 else " Prejuízo"
        print(f"    {status_lucro}: {lucro:.2f} USDT")
    
    # Envia um relatório para o Oráculo de maneira detalhada
    mensagem = (
        f"{status}\n"
        f"💰 Preço: {preco:.2f} USDT\n"
        f"🕰️ Horário: {timestamp}\n"
    )
    if lucro is not None:
        mensagem += f"💵 {status_lucro}: {lucro:.2f} USDT\n"
    
    mensagem += "—" * 20
    enviar_oraculo(mensagem)
    print("-" * 40)

# ✅ Validação de Tendência
def tendencia_valida(df, index):
    """
    Verifica se há uma tendência clara nos últimos candles.
    """
    if index < PERIODO_TENDENCIA:
        return False
    
    ultimos_precos = df["close"].iloc[index - PERIODO_TENDENCIA:index]
    variacao = ultimos_precos.pct_change().sum()

    if abs(variacao) >= DESVIO_MINIMO:
        return True
    
    return False

# ✅ Executa o Backtest
def executar_backtest(df):
    """
    Executa o backtest em modo Radar Tático (100% Síncrono).
    Apenas realiza operações em momentos estratégicos.
    """
    global tentativas_sem_sucesso
    capital = estado["capital"]
    capital_real = estado["capital_real"]
    posicao = estado["posicao"]
    preco_medio = estado["preco_medio"]
    historico = estado["historico"]

    for i in range(PERIODO_TENDENCIA, len(df)):
        preco_atual = df["close"].iloc[i]
        timestamp = df.index[i].strftime('%Y-%m-%d %H:%M:%S')

        # === Verifica Zonas de Ressonância ===
        if verificar_ressonancia(preco_atual):
            registrar_ruptura(preco_atual, timestamp)
            estado["ressonancias_ignoradas"] += 1
            estado["buffer_estrategico"].append(f"️ Ressonância Ignorada em {preco_atual} USDT")
            continue

        # === Verifica Compressões Magnéticas ===
        if identificar_compressao(df):
            estado["buffer_estrategico"].append(f" Compressão Magnética Detectada em {preco_atual} USDT")
        
        # === Verifica Proximidade de Zonas Magnéticas ===
        zona_proxima = identificar_proximidade_zona(preco_atual)
        if zona_proxima:
            estado["buffer_estrategico"].append(f" Aproximação da Zona Magnética: {zona_proxima}")

        # === Verifica Sinal de Compra ===
        if df["sinal_compra"].iloc[i] and posicao == 0 and pode_operar(preco_atual, "compra"):
            if tendencia_valida(df, i):
                posicao += capital / preco_atual
                preco_medio = preco_atual
                capital = 0
                historico.append({
                "tipo": "Compra",
                "data": df.index[i],
                "preco": preco_atual
                })
                tentativas_sem_sucesso = 0

                mensagem_compra = f" Entrada Tática - COMPRA em {preco_atual} USDT"
                estado["buffer_estrategico"].append(mensagem_compra)
                enviar_oraculo(mensagem_compra)
                exibir_log_operacao("compra", preco_atual, timestamp)

        # === Verifica Sinal de Venda ou Stop Loss ===
        elif posicao > 0:
            take_profit = preco_medio * (1 + TAKE_PROFIT)
            stop_loss = preco_medio * (1 - STOP_LOSS)

            if (preco_atual >= take_profit or preco_atual <= stop_loss):
                capital = posicao * preco_atual
                lucro = capital - (posicao * preco_medio)
                capital_real += lucro
                status = "✅" if lucro > 0 else "❌"
                historico.append({
                "tipo": "Venda",
                "status": status,
                "data": df.index[i],
                "preco": preco_atual,
                "lucro": lucro
                })

                mensagem_venda = f"💡 Saída Tática - VENDA {status} em {preco_atual} USDT"
                estado["buffer_estrategico"].append(mensagem_venda)
                enviar_oraculo(mensagem_venda)
                exibir_log_operacao("venda", preco_atual, timestamp, lucro)

                posicao = 0
                preco_medio = 0

    # Atualização do estado global
    estado["capital"] = capital
    estado["capital_real"] = capital_real
    estado["posicao"] = posicao
    estado["preco_medio"] = preco_medio
    estado["historico"] = historico
    estado["ultima_data_processada"] = df.index[-1]

    # ✅ Apenas gera relatório se houver alterações
    if len(estado["buffer_estrategico"]) > 0:
        enviar_resumo_estrategico(estado)
        gerar_codice_fluxo(estado)
        enviar_log_rupturas()
        estado["buffer_estrategico"].clear()
        print(f"\n[SNE] Operações finalizadas. Capital Atual: {estado['capital_real']:.2f} USDT")
def gerar_codice_fluxo(estado):
    """
    Gera um códice de fluxo com os últimos movimentos estratégicos.
    """
    with open(CAMINHO_CODICE_FLUXO, 'a') as file:
        file.write(f"🔄 Atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write("📌 Movimentos Estratégicos Recentes:\n")
        
        for movimento in estado.get("buffer_estrategico", []):
            file.write(f"{movimento}\n")
        
        file.write("-" * 50 + "\n")
    
    print("✅ Códice de Fluxo atualizado com sucesso.")
def enviar_relatorio_estrategico():
    """
    Envia um relatório detalhado da última operação para o Oráculo.
    """
    mensagem = (
        f"📌 <b>Relatório Estratégico:</b>\n"
        f"💰 <b>Capital Atual:</b> {estado['capital']:.2f} USDT\n"
        f"💵 <b>Capital Real:</b> {estado['capital_real']:.2f} USDT\n"
        f"📈 <b>Posição Atual:</b> {estado['posicao']:.6f} BTC\n"
        f"🛡️ <b>Ressonâncias Ignoradas:</b> {estado['ressonancias_ignoradas']}\n"
        f"📍 <b>Zonas Mapeadas:</b> {estado['zonas_mapeadas']}\n"
        f"📅 <b>Última Operação:</b> {estado['ultima_data_processada']}\n"
    )
    enviar_oraculo(mensagem)
