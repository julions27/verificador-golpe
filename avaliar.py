import json
import os
import time
import sys
from ia import analisar_ia, MODELO, PROMPT_VERSAO, SINAIS_IA
from collections import Counter
from verificador import decidir, OBJETIVAS

from regras import analisar_regras, PALAVRAS

COBERTOS = {"V1", "V2", "C9"} | set(PALAVRAS)
SO_CABECALHO = {"CN1", "CN2", "CN4"}
CACHE = "resultados/cache_ia.jsonl"

def remover_cabecalho(texto):
    linhas = texto.split("\n")
    if linhas[0].startswith("["):
        return "\n".join(linhas[1:])
    return texto

def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]

def avaliar(casos, modo, cenario, cache):
    matriz = Counter()
    acertos, perdidos, a_mais = Counter(), Counter(), Counter()
    erros, falhas = [], []
    cobertos = COBERTOS if cenario == "regras" else set(SINAIS_IA)

    for caso in casos:
        texto = caso["texto"]
        esperados = set(caso["sinais_esperados"])

        if modo == "so_texto":
            texto = remover_cabecalho(texto)
            esperados = esperados - SO_CABECALHO
            
        regras = {a["codigo"] for a in analisar_regras(texto)}
        if cenario == "regras":
            apontados = regras
        else:
            try:
                r = ia_com_cache(cache, caso["id"], modo, texto)
            except Exception as e:
                falhas.append((caso["id"], str(e)))
                continue                     
            ia = {s["codigo"] for s in r["validos"]}
            if cenario == "ia":
                apontados = ia
            elif cenario == "ia_objetivas":
                apontados = ia | (regras & OBJETIVAS)
            else:
                apontados = ia | regras

        alerta = decidir(apontados) == "alto"
        golpe = caso["rotulo"] == "golpe"

        if golpe and alerta:
            matriz["golpe_com_alerta"] += 1
        elif golpe and not alerta:
            matriz["golpe_sem_alerta"] += 1
            erros.append((caso["id"], "golpe_sem_alerta", apontados))
        elif alerta and not golpe:
            matriz["alerta_sem_golpe"] += 1
            erros.append((caso["id"], "alerta_sem_golpe", apontados))
        elif not alerta and not golpe:
            matriz["sem_alerta_sem_golpe"] += 1
        
        esp = esperados & cobertos
        apo = apontados & cobertos
        
        for codigo in esp & apo:      
            acertos[codigo] += 1

        for codigo in esp - apo:     
            perdidos[codigo] += 1

        for codigo in apo - esp:        
            a_mais[codigo] += 1

    return matriz, acertos, perdidos, a_mais, erros, falhas

def carregar_cache():
    if not os.path.exists(CACHE):
        return{}
    with open(CACHE, encoding="utf-8") as f:
        return {r["chave"]: r for r in map(json.loads, f)}

def ia_com_cache(cache, caso_id, modo, texto):
    chave = f"{MODELO}|{PROMPT_VERSAO}|{modo}|{caso_id}"
    if chave not in cache:
        validos, descartados = analisar_ia(texto)
        registro = {
            "chave": chave,
            "validos": [s.model_dump() for s in validos],
            "descartados": [s.model_dump() for s in descartados],
        }
        with open(CACHE, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        cache[chave] = registro
        time.sleep(4)
    return cache[chave]

def resumo(matriz):
    golpes = matriz["golpe_com_alerta"] + matriz["golpe_sem_alerta"]
    legitimos = matriz["alerta_sem_golpe"] + matriz["sem_alerta_sem_golpe"]
    return (f"golpes com alerta: {matriz['golpe_com_alerta']}/{golpes} | "
            f"alarmes falsos: {matriz['alerta_sem_golpe']}/{legitimos}")

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "dados/dev.jsonl"
    casos = carregar(caminho)
    #casos = carregar("dados/dev.jsonl")
    cache = carregar_cache()

    for modo in ["completo", "so_texto"]:
        print(f"\n=== {modo} ===")
        for cenario in ["regras", "ia", "ia_objetivas", "regras_ia"]:
            matriz, acertos, perdidos, a_mais, erros, falhas = avaliar(casos, modo, cenario, cache)
            print(f"{cenario:12} {resumo(matriz)} | falhas: {len(falhas)}")

    for modo in ["completo", "so_texto"]:
        matriz, acertos, perdidos, a_mais, erros, falhas = avaliar(casos, modo, "ia", cache)
        print(f"\n--- erros da IA ({modo}) ---")
        for e in erros:
            print(e)
        for codigo in ["V1", "V2", "C9", "C6", "C12"]:
            print(codigo, "| acertos:", acertos[codigo], "| perdidos:", perdidos[codigo], "| a mais:", a_mais[codigo])