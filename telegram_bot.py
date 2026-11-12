import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from verificador import verificar
from sinais import SINAIS

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

MENSAGENS_RISCO = {
    "alto": "Sinais fortes de golpe. Não pague nada e não envie dados antes de confirmar.",
    "medio": "Atenção: encontrei um sinal suspeito. Confirme antes de qualquer pagamento.",
    "inconclusivo": "Não encontrei sinais conhecidos de golpe. Isso não garante que a mensagem seja verdadeira.",
}

OPCOES = {"sim": True, "nao": False, "nao_sei": None}

TITULOS = {
    "conversa": "NA CONVERSA",
    "canal": "NO CONTATO",
    "documento": "NO DOCUMENTO",
    "verificacao": "VERIFICAÇÃO AUTOMÁTICA",
}

COMO_CONFIRMAR = (
    "COMO CONFIRMAR\n"
    "- Consulte o processo no site do tribunal (o endereço oficial termina em .jus.br).\n"
    "- Ligue para o seu advogado no número que você já tinha, não no número que mandou a mensagem.\n"
    "- Confira se o advogado é real no ConfirmADV, da OAB: confirmadv.oab.org.br\n"
    "- Tribunais não cobram pagamento por WhatsApp para liberar dinheiro de processo.\n"
    "- Se for golpe, denuncie em fiscalizacao.oab.org.br e registre um boletim de ocorrência."
)

LIMITE_TELEGRAM = 4096

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bem-vindo. Sou um robô projetado para lhe ajudar a identificar o golpe do falso advogado. Por favor cole as mensagens da conversa, não envie CPF, endereço nem dados bancários: a mensagem é analisada por um serviço de inteligência artificial externo.")
    
def formatar(resultado):
    partes = []

    if resultado["ia_falhou"] and resultado["risco"] == "inconclusivo":
        partes.append(
            "Não consegui concluir a análise agora. Tente de novo em alguns minutos. "
            "Enquanto isso, não pague nada nem envie dados."
        )
    else:
        partes.append(MENSAGENS_RISCO[resultado["risco"]])
        if resultado["ia_falhou"]:
            partes.append(
                "Aviso: a análise por inteligência artificial está indisponível agora. "
                "O resultado considera só as verificações automáticas."
            )

    grupos = {}
    for s in resultado["sinais"]:
        grupos.setdefault(SINAIS[s["codigo"]]["camada"], []).append(s)

    for camada, titulo in TITULOS.items():
        if camada in grupos:
            linhas = [titulo]
            for s in grupos[camada]:
                linhas.append(f"- {s['explicacao']}\n  Trecho: \"{s['trecho']}\"")
            partes.append("\n".join(linhas))

    partes.append(COMO_CONFIRMAR)
    texto = "\n\n".join(partes)

    if len(texto) > LIMITE_TELEGRAM:
        corte = LIMITE_TELEGRAM - len(COMO_CONFIRMAR) - 10
        texto = texto[:corte] + "\n[...]\n\n" + COMO_CONFIRMAR
    return texto

async def botao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagens = context.user_data.setdefault("mensagens", [])
    mensagens.append(update.message.text)

    if len(mensagens) > 1:
        await update.message.reply_text(
            "Recebi mais uma parte. Quando terminar, responda à pergunta acima."
        )
        return

    teclado = InlineKeyboardMarkup([[
        InlineKeyboardButton("Sim", callback_data="sim"),
        InlineKeyboardButton("Não", callback_data="nao"),
        InlineKeyboardButton("Não sei", callback_data="nao_sei"),
    ]])
    await update.message.reply_text(
        "Você já tinha esse número salvo?\n\n"
        "Se a conversa tiver mais mensagens, pode enviar todas antes de responder.",
        reply_markup=teclado,
    )


async def analisar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    consulta = update.callback_query
    await consulta.answer()

    mensagens = context.user_data.pop("mensagens", None)
    if not mensagens:
        await consulta.message.reply_text("Não encontrei a mensagem. Envie de novo, por favor.")
        return

    texto = "\n".join(mensagens)
    ja_tinha = OPCOES[consulta.data]
    await consulta.message.reply_text("Analisando...")
    resultado = await asyncio.to_thread(verificar, texto, ja_tinha)
    await consulta.message.reply_text(formatar(resultado))
    
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", inicio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, botao))
app.add_handler(CallbackQueryHandler(analisar))
app.run_polling()