import pandas as pd
import os
from datetime import datetime

# Caminho para o arquivo CSV que armazena as zonas magnéticas
CAMINHO_CATALOGO = "zonas_magneticas.csv"

# ✅ Atualização do Catálogo de Zonas Magnéticas
def atualizar_catalogo(df):
    """
    Atualiza o catálogo de zonas magnéticas com base nas rupturas detectadas no DataFrame.
    """
    if "ruptura" not in df.columns or not df["ruptura"].any():
        print("[CATÁLOGO] Nenhuma ruptura detectada.")
        return

    df_rupturas = df[df["ruptura"]].copy()
    df_rupturas["zona"] = (df_rupturas["close"] // 50) * 50
    df_rupturas["forca"] = df_rupturas["densidade"]

    try:
        catalogo = pd.read_csv(CAMINHO_CATALOGO)
    except FileNotFoundError:
        catalogo = pd.DataFrame(columns=["zona", "forca_total", "ocorrencias", "ultima_data"])

    zonas_existentes = catalogo["zona"].values if not catalogo.empty else []

    for timestamp, row in df_rupturas.iterrows():
        zona = row["zona"]
        densidade = row["forca"]
        data = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        if zona in zonas_existentes:
            idx = catalogo.index[catalogo["zona"] == zona][0]
            catalogo.at[idx, "forca_total"] += densidade
            catalogo.at[idx, "ocorrencias"] += 1
            catalogo.at[idx, "ultima_data"] = data
        else:
            novo = {
                "zona": zona,
                "forca_total": densidade,
                "ocorrencias": 1,
                "ultima_data": data
            }
            catalogo = pd.concat([catalogo, pd.DataFrame([novo])], ignore_index=True)

    catalogo.to_csv(CAMINHO_CATALOGO, index=False)
    print(f"[CATÁLOGO] Atualizado com {len(df_rupturas)} rupturas.")

# ✅ Exibir Zonas Relevantes
def exibir_zonas_relevantes(limite=5):
    """
    Retorna uma lista das zonas magnéticas mais relevantes com base na força média.
    """
    try:
        catalogo = pd.read_csv(CAMINHO_CATALOGO)
    except FileNotFoundError:
        print("[CATÁLOGO] Nenhuma zona registrada ainda.")
        return []

    if catalogo.empty:
        print("[CATÁLOGO] O catálogo está vazio.")
        return []

    catalogo["forca_media"] = catalogo["forca_total"] / catalogo["ocorrencias"]
    catalogo = catalogo.sort_values(by="forca_media", ascending=False)

    zonas_relevantes = []
    for _, row in catalogo.head(limite).iterrows():
        zonas_relevantes.append({
            "zona": float(row["zona"]),
            "forca_total": round(row["forca_total"], 2),
            "ocorrencias": int(row["ocorrencias"]),
            "ultima_data": row["ultima_data"]
        })

    return zonas_relevantes

# ✅ Verificação de Ressonância
def verificar_ressonancia(preco_atual, margem=10):
    """
    Verifica se o preço atual está em uma zona de ressonância mapeada.
    """
    try:
        catalogo = pd.read_csv(CAMINHO_CATALOGO)
    except FileNotFoundError:
        print("[ERRO] Catálogo Magnético não encontrado.")
        return False

    if catalogo.empty:
        print("[CATÁLOGO] O catálogo está vazio.")
        return False

    # Verifica se o preço está dentro da margem de alguma zona
    zonas = catalogo["zona"].values
    for zona in zonas:
        if abs(preco_atual - zona) <= margem:
            print(f"[RESSONÂNCIA] Preço {preco_atual} em zona magnética {zona}")
            return True
    
    return False

# ✅ Identificação de Proximidade com Zona Magnética
def identificar_proximidade_zona(preco_atual, limite=50):
    """
    Verifica se o preço está se aproximando de uma zona magnética.
    """
    zonas = exibir_zonas_relevantes()
    for zona in zonas:
        if abs(preco_atual - zona["zona"]) <= limite:
            print(f"[ALERTA] Preço se aproximando da Zona {zona['zona']}")
            return zona
    return None

# ✅ Registro de Rupturas
def registrar_ruptura(preco, timestamp):
    """
    Registra uma nova ruptura magnética no catálogo.
    """
    if not os.path.exists(CAMINHO_CATALOGO):
        df = pd.DataFrame(columns=["zona", "timestamp"])
    else:
        df = pd.read_csv(CAMINHO_CATALOGO)

    nova_entrada = {"zona": preco, "timestamp": timestamp}
    df = pd.concat([df, pd.DataFrame([nova_entrada])], ignore_index=True)
    df.to_csv(CAMINHO_CATALOGO, index=False)
    print(f"🔴 Ruptura registrada em {preco} USDT | ⏱ {timestamp}")

# ✅ Identificação de Compressão Magnética
def identificar_compressao(df, margem=5):
    """
    Verifica se há compressão magnética no DataFrame, evitando alertas duplicados.
    Compressão ocorre quando os preços ficam restritos em uma faixa estreita por um período.
    """
    if not isinstance(df, pd.DataFrame):
        print("[ERRO] O argumento passado para identificar_compressao não é um DataFrame.")
        return False

    zonas_ativas = []
    preco_atual = df["close"].iloc[-1]
    agora = datetime.now()

    # 🔎 Identifica zonas próximas de compressão
    zona_proxima = identificar_proximidade_zona(preco_atual, margem)
    if zona_proxima:
        zona_valor = zona_proxima["zona"]

        # Verifica cooldown para evitar spam
        if zona_valor not in cooldown_zonas or (agora - cooldown_zonas[zona_valor]) > COOLDOWN_TEMPO:
            cooldown_zonas[zona_valor] = agora
            zonas_ativas.append(zona_valor)
            print(f"[COMPRESSÃO] Zona ativa detectada em {zona_valor} USDT")

    if zonas_ativas:
        print(f"[COMPRESSÃO] Detecção de compressão em zonas: {zonas_ativas}")
        return True

    return False
