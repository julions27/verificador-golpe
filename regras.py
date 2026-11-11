import re
import unicodedata


def normalizar(texto):
    saida = []
    for ch in texto:
        decomposto = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in decomposto if not unicodedata.combining(c)).lower()
        saida.append(base if len(base) == 1 else ch)
    return "".join(saida)

CNJ_FORMATADO = re.compile(r"\b(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})\b")
CNJ_CORRIDO = re.compile(r"\b(?:processo|autos)\s*(?:n[o.]*\s*)?(\d{7})(\d{2})(\d{4})(\d)(\d{2})(\d{4})\b")

def _numeros_cnj(texto):
    achados = [(m, texto) for m in CNJ_FORMATADO.finditer(texto)]
    achados += [(m, texto) for m in CNJ_CORRIDO.finditer(normalizar(texto))]
    numeros = []
    for m, original in achados:
        n, dd, ano, j, tr, orig = m.groups()
        valido = int(n + ano + j + tr + orig + dd) % 97 == 1
        trecho = original[m.start(1):m.end(6)]
        numeros.append((trecho, valido, j, int(tr)))
    return numeros

def checar_cnj(texto):
    return [
        {"codigo": "V1", "trecho": trecho}
        for trecho, valido, _, _ in _numeros_cnj(texto)
        if not valido
    ]

RAMOS = {"4": "federal", "5": "trabalho", "8": "estadual"}
UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
       "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SE", "SP", "TO"]
CODIGO_UF = {uf: i + 1 for i, uf in enumerate(UFS)}
ESTADOS = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM", "bahia": "BA",
    "ceara": "CE", "distrito federal": "DF", "espirito santo": "ES", "goias": "GO",
    "maranhao": "MA", "mato grosso do sul": "MS", "mato grosso": "MT", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE", "piaui": "PI",
    "rio de janeiro": "RJ", "rio grande do norte": "RN", "rio grande do sul": "RS",
    "rondonia": "RO", "roraima": "RR", "santa catarina": "SC", "sergipe": "SE",
    "sao paulo": "SP", "tocantins": "TO",
}
NOMES_ESTADOS = sorted(ESTADOS, key=len, reverse=True)
SIGLA_TJ = re.compile(r"\bTJ[-\s]?(DFT|[A-Z]{2})\b")
TJ_ESTADO = re.compile(r"tribunal de justica do estado d[eoa] ")
TJ_GENERICO = re.compile(r"tribunal de justica")
TRT = re.compile(r"\b(?:trt[-\s]?|trt da |tribunal regional do trabalho da )(\d{1,2})")
TRABALHO = re.compile(r"justica do trabalho|vara do trabalho")
TRF = re.compile(r"\b(?:trf[-\s]?|trf da |tribunal regional federal da )(\d)")
FEDERAL = re.compile(r"justica federal|precatorios? federa(?:l|is)")


def _tribunais_citados(texto):
    norm = normalizar(texto)
    citados = []

    for m in SIGLA_TJ.finditer(texto):
        uf = "DF" if m.group(1) == "DFT" else m.group(1)
        if uf in CODIGO_UF:
            citados.append(("estadual", CODIGO_UF[uf], m.group(0)))

    for m in TJ_ESTADO.finditer(norm):
        resto = norm[m.end():]
        uf, tamanho = None, 0
        if len(resto) >= 2 and resto[:2].upper() in CODIGO_UF and not resto[2:3].isalpha():
            uf, tamanho = resto[:2].upper(), 2
        else:
            for nome in NOMES_ESTADOS:
                if resto.startswith(nome):
                    uf, tamanho = ESTADOS[nome], len(nome)
                    break
        if uf:
            citados.append(("estadual", CODIGO_UF[uf], texto[m.start():m.end() + tamanho]))

    for m in TJ_GENERICO.finditer(norm):
        citados.append(("estadual", None, texto[m.start():m.end()]))
    for m in TRT.finditer(norm):
        citados.append(("trabalho", int(m.group(1)), texto[m.start():m.end()]))
    for m in TRABALHO.finditer(norm):
        citados.append(("trabalho", None, texto[m.start():m.end()]))
    for m in TRF.finditer(norm):
        citados.append(("federal", int(m.group(1)), texto[m.start():m.end()]))
    for m in FEDERAL.finditer(norm):
        citados.append(("federal", None, texto[m.start():m.end()]))

    return citados


def checar_tribunal(texto):
    citados = _tribunais_citados(texto)
    for _, _, j, tr in _numeros_cnj(texto):
        ramo = RAMOS.get(j)
        if ramo is None:  # STF, STJ, Eleitoral, Militar: fora do escopo
            continue
        for ramo_citado, tr_citado, trecho in citados:
            if ramo_citado != ramo or (tr_citado is not None and tr_citado != tr):
                return [{"codigo": "V2", "trecho": trecho}]
    return []


LINK = re.compile(r"(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.IGNORECASE)
TLDS = {"com", "br", "net", "org", "us", "online", "site", "gle", "ly", "io",
        "app", "info", "xyz", "link", "me"}
INSTITUCIONAIS = ("jus.br", "gov.br", "oab.org.br", "def.br", "mp.br", "leg.br")

def _institucional(dominio):
    # Igual ("gov.br") ou terminando com ".jus.br" etc.
    # "tjrn.jus.br.liberacao-alvara.com" não passa, porque termina em ".com"
    return any(dominio == d or dominio.endswith("." + d) for d in INSTITUCIONAIS)

def _parte_de_email(texto, inicio, fim):
    antes = texto[inicio - 1] if inicio > 0 else ""
    depois = texto[fim] if fim < len(texto) else ""
    return antes == "@" or depois == "@"

def checar_links(texto):
    achados = []
    for m in LINK.finditer(texto):
        dominio = m.group(1).lower()
        if dominio.rsplit(".", 1)[-1] not in TLDS:
            continue  # não é link (arquivo, abreviação etc.)
        if _parte_de_email(texto, m.start(), m.end()):
            continue  # e-mail não é link; o canal é avaliado pelo CN1
        if _institucional(dominio):
            continue
        achados.append({"codigo": "C9", "trecho": m.group(0)})
    return achados


PALAVRAS = {
    "C1": ["custas", "taxa", "imposto", "guia", "recolher", "recolhimento", "iof", "darf", "tarifa"],
    "C2": ["hoje", "urgente", "urgencia", "ate as", "imediato", "imediata", "imediatamente",
           "expira", "nao perde", "so hoje"],
    "C8": ["selfie", "foto do rg", "foto do documento", "foto do cartao", "foto sua",
           "mostrar o rosto", "biometria"],
    "C13": ["agencia", "dados bancarios", "dados da conta", "dados da sua conta", "qual banco",
            "numero da conta"],
    "C14": ["chamada", "videochamada", "chamada de video", "ligacao", "me liga",
            "audiencia virtual"],
    "C15": ["compartilhar a tela", "compartilha a tela", "instalar", "baixa o", "baixar o",
            "aplicativo", "codigo", "anydesk"],
    "C16": ["vai entrar em contato", "vai te ligar", "vai ligar", "gerente", "bacen",
            "banco central"],
    "C17": ["bloqueio", "bloqueado", "multa", "penhora", "preso", "presidio", "fianca",
            "arquivado", "arquivamento", "arquiva"],
    "CN3": ["numero novo", "troquei de numero", "perdi o outro numero", "perdi o numero",
            "esse aqui e o novo", "foi clonado"],
}
_PADROES = {
    codigo: re.compile(r"\b(?:" + "|".join(re.escape(p) for p in palavras) + r")\b")
    for codigo, palavras in PALAVRAS.items()
}


def checar_palavras(texto):
    norm = normalizar(texto)
    achados = []
    for codigo, padrao in _PADROES.items():
        m = padrao.search(norm)
        if m:
            achados.append({"codigo": codigo, "trecho": texto[m.start():m.end()]})
    return achados

def analisar_regras(texto):
    return checar_cnj(texto) + checar_tribunal(texto) + checar_links(texto) + checar_palavras(texto)