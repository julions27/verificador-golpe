import json
import random

with open("dados/dev.jsonl", encoding= "utf-8") as f:
    casos = [json.loads(linha) for linha in f if linha.strip()]
    
golpes = [c for c in casos if c["rotulo"] == "golpe"]
legitimos = [c for c in casos if c["rotulo"] == "legitimo"]

random.seed(1)
teste = random.sample(golpes,20) + random.sample(legitimos, 10)
ids_teste = {c["id"] for c in teste}
dev = [c for c in casos if c["id"] not in ids_teste]

def gravar(caminho, lista):
    with open(caminho, "w", encoding="utf-8") as f:
        for c in lista:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
            
gravar("dados/teste.jsonl", teste)
gravar("dados/dev.jsonl", dev)

for nome, lista in [("teste", teste), ("dev", dev)]:
    g = sum(c["rotulo"] == "golpe" for c in lista)
    print(f"{nome}: {len(lista)} casos ({g} golpes, {len(lista) - g} legítimos)")