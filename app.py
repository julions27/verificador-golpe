import streamlit as st

from ia import MODELO, PROMPT_VERSAO
from regras import UFS, _numeros_cnj
from verificador import verificar
from sinais import SINAIS

MENSAGENS_RISCO = {
    "alto": (
        st.error,
        "Sinais fortes de golpe. Não pague nada e não envie dados antes de confirmar.",
    ),
    "medio": (
        st.warning,
        "Atenção: encontramos um sinal suspeito. Confirme antes de qualquer pagamento.",
    ),
    "inconclusivo": (
        st.info,
        "Não encontramos sinais conhecidos de golpe. Isso não garante que a mensagem "
        "seja verdadeira: confirme antes de qualquer pagamento.",
    ),
}

OPCOES_NUMERO = {"Sim": True, "Não": False, "Não sei": None}

TITULOS = {
    "conversa": "Na conversa",
    "canal": "No contato",
    "documento": "No documento",
    "verificacao": "Verificação automática",
}

def site_do_tribunal(texto):
    """Devolve o site do tribunal indicado pelo primeiro número de processo válido.

    Só usa números com dígito verificador correto. O endereço segue o padrão
    dos tribunais (tjsp.jus.br, trt4.jus.br, trf1.jus.br); a pessoa ainda precisa
    procurar a consulta processual no site.
    """
    for _, valido, ramo, tribunal in _numeros_cnj(texto):
        if not valido:
            continue
        if ramo == "8" and 1 <= tribunal <= len(UFS):
            uf = UFS[tribunal - 1]
            return "www.tjdft.jus.br" if uf == "DF" else f"www.tj{uf.lower()}.jus.br"
        if ramo == "5":
            return f"www.trt{tribunal}.jus.br"
        if ramo == "4":
            return f"www.trf{tribunal}.jus.br"
    return None

st.set_page_config(page_title="Verificador de golpes judiciais")

st.title("Recebeu mensagem sobre um processo? Verifique antes de pagar")
st.write(
    "Cole abaixo a mensagem ou a conversa que você recebeu. A ferramenta aponta "
    "sinais comuns do golpe do falso advogado e mostra como confirmar."
)

texto = st.text_area(
    "Mensagem ou conversa",
    height=250,
    placeholder="Cole aqui o texto. Se for uma conversa, pode colar as falas dos dois lados.",
)

resposta = st.radio(
    "Você já tinha esse número salvo antes desta mensagem?",
    list(OPCOES_NUMERO),
    index=2,
    horizontal=True,
)

st.caption(
    "Não cole CPF, endereço nem dados bancários. A mensagem é analisada por um "
    "serviço de inteligência artificial externo."
)

if st.button("Verificar", type="primary"):
    if not texto.strip():
        st.warning("Cole uma mensagem para verificar.")
    else:
        with st.spinner("Analisando..."):
            resultado = verificar(texto, OPCOES_NUMERO[resposta])

        st.subheader("Resultado")
        mostrar, mensagem = MENSAGENS_RISCO[resultado["risco"]]
        mostrar(mensagem)

        if resultado["ia_falhou"]:
            st.warning(
                "A análise por inteligência artificial está indisponível agora. "
                "O resultado considera só as verificações automáticas "
                "(número do processo e links)."
            )

        if resultado["sinais"]:
            st.subheader("O que chamou atenção")
            grupos = {}
            for s in resultado["sinais"]:
                grupos.setdefault(SINAIS[s["codigo"]]["camada"], []).append(s)
            for camada, titulo in TITULOS.items():
                if camada in grupos:
                    st.markdown(f"**{titulo}**")
                    for s in grupos[camada]:
                        st.markdown(f"- **{s['explicacao']}**  \n  Trecho: “{s['trecho']}”")

        st.subheader("Como confirmar")
        site = site_do_tribunal(texto)
        if site:
            st.markdown(
                f"- **Consulte o processo no site do tribunal:** {site} "
                "(procure por “consulta processual”)."
            )
        else:
            st.markdown(
                "- **Consulte o processo no site do tribunal.** O endereço oficial "
                "sempre termina em “.jus.br”."
            )
        st.markdown(
            "- **Ligue para o seu advogado no número que você já tinha**, não no "
            "número que mandou a mensagem.\n"
            "- **Confira se o advogado é real** no ConfirmADV, da OAB: "
            "confirmadv.oab.org.br\n"
            "- **Tribunais não cobram pagamento por WhatsApp** para liberar dinheiro "
            "de processo.\n"
            "- **Se for golpe**, denuncie em fiscalizacao.oab.org.br e registre um "
            "boletim de ocorrência."
        )

        with st.expander("Detalhes técnicos"):
            codigos = ", ".join(s["codigo"] for s in resultado["sinais"]) or "nenhum"
            st.write(f"Sinais: {codigos}")
            st.write(f"Risco calculado: {resultado['risco']}")
            st.write(f"Modelo: {MODELO} | Prompt: {PROMPT_VERSAO}")

st.divider()
st.caption(
    "Protótipo de apoio. Não substitui a confirmação no site do tribunal nem a "
    "conversa com o seu advogado."
)