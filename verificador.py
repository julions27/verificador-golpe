from ia import analisar_ia
from regras import analisar_regras
from sinais import SINAIS

FORTES = {"C1", "V1", "V2"}
OBJETIVAS = {"V1", "V2", "C9"}

CABECALHOS = {
    True: "[WhatsApp | contato já salvo pela pessoa]",
    False: "[WhatsApp | número não salvo]",
}

def decidir(codigos):
    if len(codigos) >= 2 or codigos & FORTES:
        return "alto"
    if len(codigos) == 1:
        return "medio"
    return "inconclusivo"

def verificar(texto, ja_tinha_numero=None):
    sinais = {}
    for a in analisar_regras(texto):
        if a["codigo"] in OBJETIVAS:
            sinais[a["codigo"]] = {**a, "explicacao": SINAIS[a["codigo"]]["descricao"]}

    texto_ia = texto
    if ja_tinha_numero in CABECALHOS:
        texto_ia = CABECALHOS[ja_tinha_numero] + "\n" + texto

    ia_falhou = False
    try:
        validos, _ = analisar_ia(texto_ia)
        for s in validos:
            sinais.setdefault(s.codigo, s.model_dump()) 
    except Exception as e:
        print("Falha na IA:", repr(e))
        ia_falhou = True

    return {
        "risco": decidir(set(sinais)),
        "sinais": list(sinais.values()),
        "ia_falhou": ia_falhou,
    }
    
if __name__ == "__main__":
    texto = """Contato: Ana Paula Ferreira?
Pessoa: sim quem é
Contato: Senhora o valor ja foi concluido pelo perito judicial, a justiça decidiu a seu favor
Contato: Eu tenho a procuração da senhora, poderia resolver sozinho mas quero ajudar a senhora a receber logo
Pessoa: que procuração? eu nunca assinei nada com vc
Contato: Ta no sistema senhora, é só confirmar uns dados que eu finalizo"""

    resultado = verificar(texto, ja_tinha_numero=False)
    print("Risco:", resultado["risco"], "| IA falhou:", resultado["ia_falhou"])
    for s in resultado["sinais"]:
        print(s["codigo"], "|", s["trecho"], "|", s["explicacao"])