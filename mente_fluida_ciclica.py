from datetime import datetime
import numpy as np
import pytz
import platform
import os

zona = pytz.timezone("America/Sao_Paulo")

def tocar_alerta_ciclo():
    if platform.system() == "Darwin":  # macOS
        os.system("afplay /System/Library/Sounds/Blow.aiff")
    elif platform.system() == "Windows":
        import winsound
        winsound.Beep(1000, 300)
    else:
        print("[ALERTA CICLO] Ciclo detectado (sem som em seu sistema).")

def mente_fluidica_detectar_ciclos(df):
    if df is None or len(df) < 20:
        return

    caminho_ciclos = "sne_memoria_ciclica.txt"
    timestamp_atual = df.index[-1]

    if timestamp_atual.tzinfo is None:
        timestamp_atual = zona.localize(timestamp_atual)

    janela = 12
    ultimos = df["densidade"].tail(janela).values

    similares = []
    for i in range(len(df) - janela * 2):
        trecho = df["densidade"].iloc[i:i+janela].values
        if len(trecho) == janela:
            erro = np.mean(np.abs(trecho - ultimos))
            if erro < 0.015:
                similares.append((df.index[i], erro))

    if similares:
        melhor_ciclo = min(similares, key=lambda x: x[1])
        data_ciclo = melhor_ciclo[0]
        erro_ciclo = melhor_ciclo[1]

        print(f"[CICLO] Padrão cíclico detectado com erro médio {erro_ciclo:.4f}")
        tocar_alerta_ciclo()

        with open(caminho_ciclos, "a") as f:
            f.write(f"[{datetime.now(tz=zona)}] Ciclo semelhante a {data_ciclo} com erro {erro_ciclo:.4f}\n")

def avaliar_ciclo_ruptura(df, tempo_ruptura):
    """
    Avalia se uma ruptura é iminente com base em comportamento cíclico.
    """
    try:
        janela = df[df.index <= tempo_ruptura].tail(20)
        variacao = janela["densidade"].std()
        media = janela["densidade"].mean()

        if variacao > 0.5 and janela["densidade"].iloc[-1] > media * 1.5:
            print(f"[MFC] Ruptura iminente identificada via ciclo energético.")
            return True
    except Exception as e:
        print(f"[MFC ERRO] {e}")
    return False