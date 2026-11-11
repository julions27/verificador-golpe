import pytest

from regras import (
    analisar_regras,
    checar_cnj,
    checar_links,
    checar_palavras,
    checar_tribunal,
    normalizar,
)


def codigos(achados):
    return {a["codigo"] for a in achados}

def test_normalizar_tira_acento_e_maiuscula():
    assert normalizar("AÇÃO até às 17h") == "acao ate as 17h"

def test_normalizar_mantem_o_tamanho():
    texto = "Agência, 3ª Região, São João 🙏"
    assert len(normalizar(texto)) == len(texto)

def test_cnj_valido():
    assert checar_cnj("processo 9878425-21.2022.8.26.0053") == []


def test_cnj_invalido():
    assert checar_cnj("processo 9883662-46.2022.8.16.0001")[0]["codigo"] == "V1"


def test_cnj_sem_pontuacao_valido():
    assert checar_cnj("processo 98784252120228260053") == []


def test_cnj_sem_pontuacao_invalido():
    assert checar_cnj("processo 98836624620228160001")[0]["codigo"] == "V1"

def test_cnj_numero_duplo():
    x = "9878425-21.2022.8.26.0053"
    y = "9883662-46.2022.8.16.0001"
    achados = checar_cnj(f"processo {x} e {y}")
    assert len(achados) == 1
    assert achados[0]["trecho"] == y

def test_cnj_texto_sem_numero():
    assert checar_cnj("saiu o alvará do seu processo") == []


def test_cnj_codigo_de_verificacao_nao_e_processo():
    assert checar_cnj("informe o código de verificação 26111012345678900000") == []


def test_cnj_sem_pontuacao_com_numero_simbolo():
    assert checar_cnj("Processo nº 98836624620228160001")[0]["trecho"] == "98836624620228160001"

@pytest.mark.parametrize("texto, esperado", [
    ("Alvará do TJGO, processo 9979457-98.2024.8.21.0001", 1),                     # número é do TJRS
    ("TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO SUL, processo 9885954-79.2025.5.04.0011", 1),  # número é trabalhista
    ("TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO, processo 9848524-07.2024.4.01.3500", 1),  # número é do TRF1
    ("'Tribunal de Justiça', processo 9885772-30.2022.4.01.4000", 1),               # número é federal
    ("precatório federal, processo 9983498-83.2025.8.26.0050", 1),                 # número é estadual
    
    ("TJ-SP informa: processo 9948453-96.2024.8.26.0100", 0),
    ("Tribunal de Justiça do Estado de Minas Gerais, processo 9971065-93.2022.8.13.0024", 0),
    ("TJDFT, processo 9924898-49.2022.8.07.0003", 0),
    ("Vara do Trabalho, TRT6, processo 9838140-92.2022.5.06.0311", 0),
    ("'Tribunal de Justiça' sem estado, processo 9878425-21.2022.8.26.0053", 0),  

    ("seu processo no TJGO foi liberado", 0),
    ("processo 9979457-98.2024.8.21.0001", 0),
])
def test_tribunal(texto, esperado):
    achados = checar_tribunal(texto)
    assert len(achados) == esperado
    for a in achados:
        assert a["codigo"] == "V2"
        assert a["trecho"] in texto

def test_tribunal_trecho_aponta_o_tribunal_citado():
    achados = checar_tribunal("Alvará do TJGO, processo 9979457-98.2024.8.21.0001")
    assert achados[0]["trecho"] == "TJGO"


def test_tribunal_mato_grosso_do_sul_nao_vira_mato_grosso():
    numero = "9871234-37.2023.8.12.0001"
    assert checar_tribunal(f"Tribunal de Justiça do Estado de Mato Grosso do Sul, processo {numero}") == []
    assert len(checar_tribunal(f"Tribunal de Justiça do Estado de Mato Grosso, processo {numero}")) == 1

@pytest.mark.parametrize("texto, esperado", [
    # Não são links suspeitos
    ("consulte em www.tjrn.jus.br/consulta", 0),
    ("site WWW.TJRN.JUS.BR", 0),
    ("agende em defensoria.ba.def.br/agendamento", 0),
    ("entre com sua conta gov.br", 0),
    ("acesse tjrn.jus.br.", 0),                       
    ("bom dia, tudo bem?", 0),
    ("o Dr. Marcelo cobrou R$ 1.150,00", 0),
    ("segue alvara.pdf", 0),
    ("Fica V.Sa. intimado", 0),
    ("OAB/RJ 2xx.xxx", 0),
    ("escreva para fulano@gmail.com", 0),
    ("remetente: juridico.cobrancas.br@gmail.com", 0),
    
    # Links suspeitos
    ("acesse tjrn.jus.br.liberacao-alvara.com", 1),   
    ("clique: bit.ly/alvara123", 1),
    ("responda em forms.gle/abc", 1),
    ("sala: zoom.us/j/123", 1),
    ("baixe em juspag-app.com/download.apk", 1),    
    ("acesse https://tjsp-resgate.online/consulta", 1),
])
def test_links(texto, esperado):
    achados = checar_links(texto)
    assert len(achados) == esperado
    assert all(a["codigo"] == "C9" for a in achados)

def test_links_trecho_e_o_link_inteiro():
    achados = checar_links("acesse https://tjsp-resgate.online/consulta")
    assert achados[0]["trecho"] == "https://tjsp-resgate.online"

def test_palavras_pagamento_e_urgencia():
    assert codigos(checar_palavras("precisa pagar as custas hoje")) == {"C1", "C2"}

def test_palavras_ignoram_acento_e_maiuscula():
    assert codigos(checar_palavras("me passa a AGÊNCIA e a conta")) == {"C13"}

def test_palavras_trecho_vem_do_texto_original():
    achados = checar_palavras("Pague a TAXA até às 17h")
    trechos = {a["codigo"]: a["trecho"] for a in achados}
    assert trechos == {"C1": "TAXA", "C2": "até às"}

def test_palavras_nao_pegam_pedaco_de_palavra():
    # "taxa" não pode ser achada dentro de "taxação"
    assert checar_palavras("houve uma taxação nova") == []

def test_palavras_um_achado_por_sinal():
    achados = checar_palavras("custas, taxa e imposto")
    assert [a["codigo"] for a in achados] == ["C1"]

def test_palavras_texto_neutro():
    assert checar_palavras("obrigada pelo contato, até mais") == []

def test_analisar_regras_junta_tudo():
    texto = (
        "Alvará do TJGO, processo 9979457-98.2024.8.21.0001. "
        "Pague a taxa hoje pelo link bit.ly/alvara"
    )
    assert codigos(analisar_regras(texto)) == {"V2", "C9", "C1", "C2"}

def test_analisar_regras_todos_os_trechos_existem_no_texto():
    texto = "Sr. João, o juiz vai te ligar. Envie selfie e a agência em www.tjsp-pagamentos.com"
    for a in analisar_regras(texto):
        assert a["trecho"] in texto