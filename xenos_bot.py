import requests
import os
from datetime import datetime, timedelta
from threading import Timer
from memoria_neural import capturar_memoria_mercado
from mente_fluida import mente_fluidica_verificar_resonancia
from mente_fluida_ciclica import mente_fluidica_detectar_ciclos
from mapeamento_gravitacional import detectar_zonas_criticas
from previsao_magnetica import prever_movimentos
from pulso_magnetico import detectar_pulsos_massa
from catalogo_magnetico import (
    exibir_zonas_relevantes, verificar_ressonancia, registrar_ruptura,
    identificar_compressao, identificar_proximidade_zona
)

# === Configurações do Telegram ===
TELEGRAM_TOKEN = "7970664442:AAHTBoX69oRH-r_FxMXWDw8EZjnxxeBd69Y"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
CHAT_ID = "6457067653"

# === Caminhos para salvar logs temporários e códices ===
CAMINHO_LOG_RUPTURAS = os.path.join(os.getcwd(), "log_rupturas.txt")
CAMINHO_CODICE_FLUXO = os.path.join(os.getcwd(), "codice_fluxo.txt")

estado = {
    "capital": 1000,
    "capital_real": 1000,
    "posicao": 0,
    "preco_medio": 0,
    "historico": [],
    "ressonancias_ignoradas": 0,
    "ultima_data_processada": None,
    "zonas_mapeadas": [],
    "rupturas_estrategicas": []
}

# === Buffer de mensagens e controle de tempo ===
buffer_mensagens = []
ultima_mensagem_enviada = datetime.now()
intervalo_envio = timedelta(minutes=5)  # Envio de 5 em 5 minutos
ultima_mensagem = ""  # Armazena o último conteúdo enviado


# === Verificação de conexão com a internet ===
def verificar_conexao():
    """
    Testa conexão com a API do Telegram para evitar falhas contínuas.
    """
    try:
        response = requests.get('https://api.telegram.org', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# ✅ Verifica e cria os arquivos de log e códice, se não existirem
for caminho, nome in [(CAMINHO_LOG_RUPTURAS, "Log de Rupturas"), (CAMINHO_CODICE_FLUXO, "Códice de Fluxo")]:
    if not os.path.exists(caminho):
        with open(caminho, 'w') as file:
            file.write(f"🔍 {nome} Iniciado.\n")
        print(f"✅ Arquivo criado em: {caminho}")

# ✅ Envia mensagem para o Telegram de forma síncrona
ultima_mensagem_enviada = None

def enviar_oraculo(mensagem, max_tentativas=3):
    """
    Envia uma mensagem para o Oráculo via Telegram.
    Apenas envia se houver mudanças estratégicas.
    """
    global ultima_mensagem_enviada

    # Evita duplicidade
    if mensagem == ultima_mensagem_enviada:
        print("🔄 Mensagem duplicada detectada. Ignorando envio.")
        return False

    params = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'HTML'
    }

    tentativas = 0
    while tentativas < max_tentativas:
        try:
            response = requests.post(TELEGRAM_URL, params=params, timeout=10)
            if response.status_code == 200:
                print(f"✅ Mensagem enviada com sucesso: {mensagem}")
                ultima_mensagem_enviada = mensagem
                return True
            else:
                erro = response.text
                print(f"[ERRO ENVIO] Status {response.status_code}: {erro}")
        except requests.ConnectionError:
            print(f"[ERRO ENVIO] Conexão falhou. Tentativa {tentativas + 1} de {max_tentativas}.")
        except requests.Timeout:
            print(f"[ERRO ENVIO] Timeout excedido. Tentativa {tentativas + 1} de {max_tentativas}.")
        except Exception as e:
            print(f"[ERRO ENVIO] Tentativa {tentativas + 1} falhou: {e}")
        
        tentativas += 1
    
    print("[ERRO ENVIO] Máximo de tentativas atingido. Mensagem não enviada.")
    return False

# ✅ Função para agrupar mensagens e enviar de forma otimizada
def enviar_buffer_estrategico():
    """
    Envia todas as mensagens acumuladas no buffer a cada intervalo definido.
    """
    global buffer_mensagens, ultima_mensagem_enviada

    if buffer_mensagens:
        buffer_mensagens = list(set(buffer_mensagens))
        mensagem_estrategica = "📡 <b>Resumo Estratégico:</b>\n"
        mensagem_estrategica += "\n".join(buffer_mensagens)
        
        if enviar_oraculo(mensagem_estrategica):
            buffer_mensagens = []
            ultima_mensagem_enviada = datetime.now()

    # Apenas reinicia se houve alteração no buffer
    if buffer_mensagens:
        Timer(intervalo_envio.total_seconds(), enviar_buffer_estrategico).start()
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

    # 🔎 Médias Móveis
    ema8 = df["EMA8"].iloc[-1]
    ema21 = df["EMA21"].iloc[-1]
    sma200 = df["SMA200"].iloc[-1]

    tendencia = "Neutra"
    if ema8 > ema21 > sma200:
        tendencia = "🔼 Tendência de Alta"
    elif ema8 < ema21 < sma200:
        tendencia = "🔻 Tendência de Baixa"
    
    # 📡 Relatório Estratégico Completo
    relatorio = (
        f"📊 <b>Análise Estratégica - Radar Ativado:</b>\n"
        f"🕰️ <b>Horário:</b> {timestamp}\n"
        f"💲 <b>Preço Atual:</b> {preco_atual:.2f} USDT\n\n"
        f"🔎 <b>Zonas Críticas:</b> {zonas_criticas}\n"
        f"🚀 <b>Canais de Propulsão:</b> {canais}\n"
        f"🛡️ <b>Ressonância Detectada:</b> {'Sim' if ressonante else 'Não'}\n"
        f"🔄 <b>Movimentos Esperados:</b> {movimentos_futuros}\n"
        f"📈 <b>Tendência Atual:</b> {tendencia}\n\n"
        f"🗒️ <b>Recomendações Estratégicas:</b>\n"
    )

    # 📌 Recomendações de Ação
    if ressonante and tendencia == "🔼 Tendência de Alta":
        relatorio += "🔵 Possível oportunidade de COMPRA detectada.\n"
    elif ressonante and tendencia == "🔻 Tendência de Baixa":
        relatorio += "🔴 Possível oportunidade de VENDA detectada.\n"
    else:
        relatorio += "⚠️ Mercado neutro, aguardar confirmação de direção.\n"
    
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

# ✅ Envio de Resumo Estratégico
def enviar_resumo_estrategico(estado):
    """
    Adiciona um resumo estratégico ao buffer para envio otimizado.
    """
    mensagem = "📋 <b>Resumo Estratégico:</b>\n"
    mensagem += f"💰 <b>Capital Atual:</b> {estado['capital']:.2f} USDT\n"
    mensagem += f"📈 <b>Posição Atual:</b> {estado['posicao']:.6f} BTC\n"
    mensagem += f"🔄 <b>Operações Realizadas:</b> {len(estado['historico'])}\n"
    mensagem += f"🛡️ <b>Ressonâncias Ignoradas:</b> {estado['ressonancias_ignoradas']}\n\n"
    
    if estado["historico"]:
        ultima_operacao = estado["historico"][-1]
        mensagem += f"📌 <b>Última Operação:</b> {ultima_operacao['tipo']} em {ultima_operacao['preco']} USDT\n"
    
    buffer_mensagens.append(mensagem)
    enviar_oraculo(mensagem)

# ✅ Envio de Relatório de Rupturas
def enviar_log_rupturas():
    """
    Adiciona o relatório de rupturas ao buffer para envio otimizado.
    """
    if os.path.exists(CAMINHO_LOG_RUPTURAS):
        with open(CAMINHO_LOG_RUPTURAS, 'r') as file:
            logs = file.read().strip()
            if logs:
                # 🔍 Formatação clara e estratégica
                mensagem = (
                    f"📊 <b>Relatório de Rupturas:</b>\n"
                    f"<pre>{logs}</pre>\n"
                    f"⚠️ <b>Atenção:</b> Verificar zonas críticas para possível entrada ou saída estratégica.\n"
                    f"📡 Monitoramento contínuo em execução.\n"
                )
                # Evitar duplicidade no buffer
                if mensagem not in buffer_mensagens:
                    buffer_mensagens.append(mensagem)
                    enviar_oraculo(mensagem)
            else:
                print("⚠️ Nenhuma ruptura relevante detectada.")
    else:
        print(f"[ERRO] O arquivo de log não foi encontrado: {CAMINHO_LOG_RUPTURAS}")

# ✅ Geração do códice de fluxo
def gerar_codice_fluxo(estado):
    """
    Gera um códice de fluxo com os últimos movimentos estratégicos.
    """
    movimentos_unicos = list(set(estado.get("buffer_estrategico", [])))  # Remove duplicidades

    if movimentos_unicos:
        with open(CAMINHO_CODICE_FLUXO, 'a') as file:
            file.write(f"\n🔄 <b>Atualização:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write("📌 <b>Movimentos Estratégicos Recentes:</b>\n")
            
            for movimento in movimentos_unicos:
                file.write(f"{movimento}\n")
            
            file.write("—" * 50 + "\n")
        
        print("✅ Códice de Fluxo atualizado com sucesso.")
    else:
        print("⚠️ Nenhum movimento estratégico recente detectado.")
def iniciar_oraculo():
    """
    Envia uma mensagem inicial para o Oráculo no Telegram.
    """
    mensagem = "🔮 <b>Oráculo iniciado. Aguardando instruções...</b>"
    enviar_oraculo(mensagem)
    print("✅ Oráculo iniciado e mensagem enviada.")

def enviar_alerta_tatico(movimento, preco, timestamp, tipo="neutro"):
    """
    Adiciona um alerta tático ao buffer para envio otimizado.
    """
    icone = "🛡️" if tipo == "ressonancia" else ("🚀" if tipo == "compra" else "💡")
    mensagem = f"{icone} <b>{movimento}</b>\n"
    mensagem += f"💰 <b>Preço:</b> {preco:.2f} USDT\n"
    mensagem += f"⏱ <b>Horário:</b> {timestamp}\n"
    buffer_mensagens.append(mensagem)
# ✅ Fechar a sessão do Oráculo
def fechar_sessao():
    """
    Finaliza a sessão do Telegram e limpa buffers temporários.
    """
    print("[INFO] Finalizando sessão com o Oráculo...")
    buffer_mensagens.clear()
