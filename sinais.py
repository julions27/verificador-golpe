SINAIS = {
    # --- Conversa ---
    "C1": {"camada": "conversa", "descricao": "Pede pagamento ou transferência para liberar um valor que a pessoa teria a receber (ex.: 'custas', 'taxa do alvará', 'imposto do precatório')"},
    "C2": {"camada": "conversa", "descricao": "Pressiona por decisão ou pagamento imediato (ex.: prazo de poucas horas, 'só hoje')"},
    "C3": {"camada": "conversa", "descricao": "Oferece resolver tudo sozinho em nome da pessoa, como um atalho"},
    "C4": {"camada": "conversa", "descricao": "Alega ter procuração ou representar a pessoa, sem comprovar"},
    "C5": {"camada": "conversa", "descricao": "Invoca autoridade de forma vaga, sem citar decisão, data ou documento (ex.: 'a Justiça decidiu', 'o perito avaliou')"},
    "C6": {"camada": "conversa", "descricao": "Insiste depois que a pessoa recusa ou demonstra desinteresse"},
    "C7": {"camada": "conversa", "descricao": "Pede pagamento para conta de pessoa física ou de um suposto escritório, em vez de guia oficial do tribunal"},
    "C8": {"camada": "conversa", "descricao": "Pede foto de documento, selfie ou vídeo"},
    "C9": {"camada": "conversa", "descricao": "Envia links fora de domínios institucionais (ex.: fora de .jus.br, .gov.br, .oab.org.br, .def.br, .mp.br ou .leg.br)"},
    "C10": {"camada": "conversa", "descricao": "Começa a abordagem confirmando o nome da pessoa, sem se identificar"},
    "C11": {"camada": "conversa", "descricao": "Não explica o motivo do contato nem cita o processo de forma clara"},
    "C12": {"camada": "conversa", "descricao": "Se recusa ou desconversa quando a pessoa pede identificação (ex.: 'endereço do escritório', 'CNPJ', 'número da OAB')"},
    "C13": {"camada": "conversa", "descricao": "Pede dados bancários da pessoa para depositar ou 'analisar' a conta (ex.: agência e conta, chave Pix, 'qual banco você usa', 'enviar ao BACEN')"},
    "C14": {"camada": "conversa", "descricao": "Pede para a pessoa entrar em chamada, videochamada ou 'audiência' pelo WhatsApp ou por link para concluir a liberação"},
    "C15": {"camada": "conversa", "descricao": "Pede para compartilhar a tela, instalar aplicativo ou informar código recebido por SMS ou aplicativo"},
    "C16": {"camada": "conversa", "descricao": "Anuncia que uma autoridade vai entrar em contato direto com a pessoa (ex.: 'o juiz vai te ligar', perito, servidor, BACEN, Defensoria)"},
    "C17": {"camada": "conversa", "descricao": "Pede pagamento para evitar um prejuízo (ex.: bloqueio de conta, multa, prisão, perda de prazo ou do benefício)"},
    "C18": {"camada": "conversa", "descricao": "Cobra honorários ou serviço jurídico sem contrato formal ou por serviço que a pessoa não contratou"},
    "C19": {"camada": "conversa", "descricao": "Voz ou vídeo com aparência artificial ou travando (possível deepfake), ou jeito de falar diferente do habitual do advogado (ex.: 'a voz é dele mas tá robótica', 'o rosto travava')"},
    "C20": {"camada": "conversa", "descricao": "Valor anunciado incompatível com o que a pessoa esperava do processo (ex.: 'meu processo era de 10 mil no máximo')"},

    "CN1": {"camada": "canal", "descricao": "Contato vem de número ou e-mail diferente do que a pessoa já tinha do advogado ou escritório"},
    "CN2": {"camada": "canal", "descricao": "Conta comercial desconhecida ou criada recentemente (ex.: 'Empresa cadastrada desde' poucos meses atrás)"},
    "CN3": {"camada": "canal", "descricao": "Justifica o uso de número novo (ex.: 'perdi o outro número', 'troquei de celular')"},
    "CN4": {"camada": "canal", "descricao": "DDD sem relação com o advogado, o escritório ou o local do processo"},

    "D1": {"camada": "documento", "descricao": "Identifica o tribunal de forma incompleta ou incoerente (ex.: 'TJ' sem o estado)"},
    "D2": {"camada": "documento", "descricao": "Usa logo ou brasão de um órgão diferente do que diz ter emitido o documento (ex.: STJ num documento de TJ)"},
    "D3": {"camada": "documento", "descricao": "Usa selos ou enfeites que imitam autenticidade (ex.: selo dourado com efeito de relevo)"},
    "D4": {"camada": "documento", "descricao": "Identifica os signatários só pelo primeiro nome, sem nome completo"},
    "D5": {"camada": "documento", "descricao": "Tem vários juízes assinando um ato que é de um juiz só (ex.: alvará)"},
    "D6": {"camada": "documento", "descricao": "Não tem assinatura digital verificável (código de verificação, link .jus.br ou QR code)"},
    "D7": {"camada": "documento", "descricao": "Usa rabiscos ou assinaturas desenhadas no lugar de assinatura digital"},
    "D8": {"camada": "documento", "descricao": "Partes incoerentes ou incompletas, sem classe ou assunto (ex.: cita credor e advogado, mas não identifica o réu)"},
    "D9": {"camada": "documento", "descricao": "Número do processo fora do cabeçalho, solto no meio do texto"},

    "V1": {"camada": "verificacao", "descricao": "Número do processo inválido pelo dígito verificador do padrão CNJ"},
    "V2": {"camada": "verificacao", "descricao": "Tribunal indicado pelo número do processo diferente do tribunal que a mensagem ou o documento diz ser"},
    "V3": {"camada": "verificacao", "descricao": "Dados do processo no DataJud (tribunal, classe, assunto) não batem com o que a mensagem ou o documento afirma"},
    "V4": {"camada": "verificacao", "descricao": "Movimentos do processo no DataJud não mostram expedição de alvará, levantamento ou pagamento compatível com o que a mensagem afirma (considerar defasagem de alguns dias; processos em segredo de justiça não aparecem)"},
    "V5": {"camada": "verificacao", "descricao": "Identidade do advogado não confirmada pelo ConfirmADV ou pelo CNA, ou o contato usado não corresponde aos dados oficiais dele"},
    "V6": {"camada": "verificacao", "descricao": "Código de verificação, QR code ou link presente no documento não confere no site oficial do tribunal ou leva a domínio fora de .jus.br"},
}

if __name__ == "__main__":
    camadas = {}
    for codigo, sinal in SINAIS.items():
        camadas.setdefault(sinal["camada"], []).append((codigo, sinal["descricao"]))

    for camada, itens in camadas.items():
        print(f"\n{camada.upper()} ({len(itens)})")
        for codigo, descricao in itens:
            print(f"  {codigo}: {descricao}")