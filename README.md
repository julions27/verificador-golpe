# Verificador de golpes judiciais

Ferramenta que analisa uma mensagem recebida por quem tem processo na Justiça e aponta sinais do **golpe do falso advogado**, mostrando o trecho que comprova cada sinal e como confirmar pelos canais oficiais.

> Protótipo de portfólio. Não substitui a consulta ao processo no site do tribunal nem a conversa com o advogado.

---

## O problema

Há poucos dias, meu pai recebeu uma mensagem de um número desconhecido. A pessoa confirmou o nome dele e mandou um PDF: um "alvará" dizendo que ele tinha R$ 23 mil para receber. Quando ele disse que não tinha interesse, o golpista insistiu: o valor "tinha sido calculado por um perito judicial", "a Justiça decidiu" e ele "tinha procuração" para resolver tudo sozinho.

O documento tinha vários sinais de falsificação: citava "Tribunal de Justiça" sem dizer o estado, trazia o logo do STJ, um selo dourado imitando relevo, quatro juízes assinando com rabiscos e só o primeiro nome, e nenhum código de verificação. O número do processo era verdadeiro, justamente para dar credibilidade. Confirmei no site do TJRN: o processo existia, mas a última decisão era outra, com assinatura digital.

Em casa, percebemos o golpe. Mas muita gente não perceberia, e quase todos os sinais eram **visuais**: quem não enxerga bem, ou depende de alguém para ler a mensagem, fica mais exposto.

O golpe é recorrente: criminosos usam dados reais de processos para se passar por advogados, servidores ou juízes e pedir pagamentos. Em fevereiro de 2026, a OAB-SP informou ter recebido 4.388 denúncias em pouco mais de um ano e meio, e tribunais como o TJDFT já alertam para variantes com falsos juízes e servidores.

## O que a ferramenta faz

A pessoa cola a mensagem (ou a conversa inteira) e responde se já tinha aquele número salvo. A ferramenta devolve:

1. **O risco**, em texto claro: sinais fortes de golpe, um sinal suspeito ou nenhum sinal conhecido. Nunca responde "seguro".
2. **Os sinais encontrados**, cada um com uma explicação simples e o **trecho exato** da mensagem que o comprova, agrupados em conversa e documento.
3. **Como confirmar:** o site do tribunal indicado pelo número do processo, ligar para o advogado no número que a pessoa já tinha, o ConfirmADV da OAB e onde denunciar.

Há duas interfaces que usam o mesmo motor:

- **Página web** em Streamlit (`app.py`);
- **Bot do Telegram** (`bot.py`), que aceita a conversa em várias mensagens.

## Como funciona

```
mensagem ──┬──> regras objetivas (V1, V2, C9) ──┐
           │                                    ├──> decidir() ──> risco + sinais + como confirmar
           └──> IA (Gemini) ──> checagem ───────┘
                               de evidência
```

**Sinais.** Uma lista única de 39 sinais (`sinais.py`), em quatro camadas: conversa (pedido de pagamento para liberar valor, autoridade vaga, insistência após recusa, procuração não comprovada...), canal (número desconhecido, conta criada há pouco), documento (tribunal sem estado, logo de outro órgão, assinatura desenhada...) e verificação.

**Regras objetivas, sem IA** (`regras.py`):

- **V1:** valida o dígito verificador do número do processo (padrão CNJ, Resolução 65/2008).
- **V2:** compara o tribunal indicado pelo número com o tribunal citado no texto (por exemplo, número do TJRS em mensagem que diz ser do TJGO).
- **C9:** aponta links fora de domínios institucionais (`.jus.br`, `.gov.br`, `.oab.org.br`, `.def.br`, `.mp.br`, `.leg.br`), usando uma lista branca de domínios de topo e ignorando e-mails e nomes de arquivo.

**IA** (`ia.py`): o modelo `gemini-3.5-flash-lite` recebe a lista de sinais e devolve uma **saída estruturada** (Pydantic) com o código, o trecho e a explicação de cada sinal, com temperatura 0. O prompt:

- usa um papel neutro e lembra que tribunais, defensorias e advogados também se comunicam por mensagem;
- exige o trecho copiado do texto, só códigos da lista e lista vazia quando não houver sinal;
- avalia as falas do contato, mas considera a reação da pessoa (para sinais como "insiste depois da recusa");
- delimita a mensagem e manda ignorar instruções dentro dela (proteção contra *prompt injection*).

**Checagem de evidência.** Todo sinal da IA é descartado se o trecho citado não existir na mensagem (comparação sem acento, maiúsculas e espaços extras). Isso impede que a ferramenta mostre um "trecho" inventado.

**Decisão de risco** (`verificador.py`): **alto** com dois ou mais sinais ou um sinal forte (pedido de pagamento para liberar valor, número inválido, tribunal incoerente); **médio** com um sinal; **inconclusivo** sem sinais. A mesma função é usada pelo produto e pela avaliação, então os números abaixo descrevem exatamente o que a pessoa usa.

**Quando a IA falha** (limite da API, servidor ocupado), a ferramenta tenta de novo com espera crescente e, se não conseguir, mostra o resultado das regras com um aviso. Se nada foi encontrado nesse caso, a primeira frase diz que a análise não foi concluída, e não "nenhum sinal encontrado". O erro é registrado no servidor, nunca mostrado à pessoa.

## Como foi avaliado

**Dataset.** 120 conversas fictícias (80 golpes e 40 legítimas), geradas com o Gemini a partir de fontes reais pesquisadas por mim (cartilhas da OAB, alertas de tribunais e Defensorias, notícias, relatos no Reclame Aqui e prints publicados em redes sociais). Cada caso tem um rótulo (golpe ou legítimo) e os sinais esperados. Os legítimos incluem casos difíceis, como advogados de verdade falando de custas, alvará e dados bancários. Os números de processo são fictícios, escolhidos para reduzir a chance de coincidir com processos reais.

**Separação.** Sorteio estratificado com semente fixa: 90 casos para desenvolvimento (`dev`, 60 golpes e 30 legítimos) e 30 para teste (`teste`, 20 e 10). O prompt foi ajustado olhando só o `dev`. Depois foi congelado (versão v2), e o `teste` rodou **uma única vez**.

**Modos.** Com o cabeçalho do canal (por exemplo, "número não salvo") e só com o texto da conversa.

**Cenários.** Só regras de palavras-chave (linha de base), só IA, IA mais regras objetivas (a arquitetura final) e tudo junto.

### Resultados no conjunto de teste (30 casos nunca vistos)

| Cenário (modo completo)                | Golpes com alerta     | Alarmes falsos |
| --------------------------------------- | --------------------- | -------------- |
| Só regras                              | 14/20 (70%)           | 3/10           |
| Só IA                                  | 19/20 (95%)           | 0/10           |
| **IA + regras objetivas (final)** | **19/20 (95%)** | **0/10** |
| Tudo junto                              | 20/20                 | 3/10           |

### Resultados no desenvolvimento (90 casos)

| Cenário                        | Completo: golpes | Completo: alarmes falsos | Só texto: golpes | Só texto: alarmes falsos |
| ------------------------------- | ---------------- | ------------------------ | ----------------- | ------------------------- |
| Só regras                      | 44/60 (73%)      | 12/30 (40%)              | 44/60             | 12/30                     |
| Só IA                          | 58/60 (97%)      | 3/30 (10%)               | 58/60             | 6/30                      |
| **IA + regras objetivas** | **58/60**  | **3/30**           | **58/60**   | **6/30**            |
| Tudo junto                      | 58/60            | 14/30                    | 58/60             | 16/30                     |

"Alerta" é risco alto. Nos dois golpes que a IA deixou passar no `dev`, ela encontrou um sinal, então a tela mostraria risco médio, com aviso.

## O que aprendi

- **As regras de palavras-chave erram justamente onde é preciso contexto.** Elas deixaram passar o caso do meu pai (perito, procuração, insistência: nada disso é palavra-chave) e acusaram de golpe a mensagem de uma advogada **alertando** o cliente sobre o golpe, porque ela citava "custas".
- **A IA não faz a conta do dígito verificador.** Errou os números inválidos nas duas rodadas (0 de 2 no `dev` e 0 de 2 no `teste`), e foi pior que as regras também em links e tribunal incoerente. Por isso a arquitetura final deixa cada parte fazer o que faz melhor: a IA interpreta o contexto e o código cuida do que é verificável.
- **Juntar tudo piorou.** Somar as palavras-chave à IA manteve os golpes detectados, mas trouxe de volta os alarmes falsos (de 3 para 14 no `dev`).
- **O canal ajuda a evitar alarme falso, não a achar golpe.** Sem o cabeçalho, a IA continuou pegando 58 de 60 golpes, mas os alarmes falsos dobraram (3 para 6). Isso justificou perguntar à pessoa se ela já tinha o número.
- **Há um trade-off que eu não resolvi.** Os alarmes falsos restantes são pedidos legítimos que parecem golpe (urgência, fotos, videochamada). Ensinar a IA a confiar em contatos já salvos os reduziria, mas deixaria passar o golpe feito pelo WhatsApp invadido do próprio advogado.

## Limitações

- **Dataset pequeno e fictício.** Os números indicam tendência, não desempenho em produção. Com 10 legítimos no teste, "0 alarmes falsos" não prova que a taxa real é zero (no `dev`, foram 3 em 30).
- **Os casos foram escritos pelo Gemini e avaliados pelo próprio Gemini**, o que pode deixar a avaliação mais otimista do que seria com mensagens reais escritas por golpistas.
- **Documentos foram avaliados como descrições em texto** ("[PDF: logo do STJ, sem código de verificação...]"). A leitura de PDF e imagem não foi implementada.
- **O dataset não tem golpes vindos do número verdadeiro do advogado** (WhatsApp invadido), um formato citado pela OAB.
- **Conversas copiadas do WhatsApp** (com data, hora e número em cada linha) foram testadas manualmente, mas não medidas.
- **Links:** domínios de topo fora da lista branca passam sem alerta, e o assinador oficial do governo (`assinador.iti.br`) gera alarme falso.
- **A checagem de evidência confere se o trecho existe, não se ele comprova o sinal.** Num teste, o modelo associou o trecho "sem código de verificação" ao sinal de assinatura desenhada.
- **O modelo não é totalmente determinístico,** mesmo com temperatura 0: a mesma mensagem teve explicações com e sem acento em execuções diferentes.
- **Sinais que dependem de consulta externa** (DataJud, ConfirmADV, código de verificação no site do tribunal) estão na lista, mas não foram implementados. O DataJud confirmaria que o processo existe, o que o golpista já sabe, e tem atraso e não inclui processos em segredo de justiça.
- **A ferramenta só ajuda quem já desconfiou.** Quem acredita no golpe não vai verificar a mensagem.
- **O bot só funciona com o computador rodando** e não recebe mensagens encaminhadas do WhatsApp (a pessoa copia e cola). O Telegram também transforma partes do número do processo em link.

## Privacidade e uso responsável

- A ferramenta **nunca diz que uma mensagem é segura** e sempre termina com a orientação de confirmar no tribunal ou com o advogado.
- As mensagens **não são guardadas**: ficam na memória só até a resposta.
- A interface e o bot avisam para **não enviar CPF, endereço nem dados bancários**.
- **A interface não foi publicada** de propósito: a camada gratuita da API do Gemini pode usar os dados enviados para melhorar os produtos do Google. Para uso real, seria preciso um plano pago e uma política de privacidade (LGPD).

## Próximos passos

1. **Leitura de PDF e imagem**, com uma etapa que descreve o documento antes da análise e uma avaliação separada em três grupos: documentos falsos reais, falsos recriados e verdadeiros.
2. **Distribuição por instituições**: o canal certo seria o WhatsApp da ouvidoria de um tribunal, da OAB ou da Defensoria, ou a própria página de consulta processual ("recebeu uma mensagem sobre este processo? Verifique aqui").
3. **Dataset maior com denúncias reais** (anonimizadas), incluindo golpes pelo número verdadeiro do advogado. Com volume, um classificador pequeno poderia filtrar as mensagens antes da IA, de forma mais barata.

## Como rodar

Requisitos: Python 3 (testado no 3.14), uma chave da API do Gemini (gratuita no [Google AI Studio](https://aistudio.google.com)) e, para o bot, um token do Telegram (criado com o [@BotFather](https://t.me/BotFather)).

```bash
git clone [url do repositório]
cd verificador-golpe
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install google-genai pydantic python-dotenv streamlit python-telegram-bot pytest
```

Crie um arquivo `.env` na raiz:

```
GEMINI_API_KEY=sua_chave
TELEGRAM_TOKEN=seu_token   # só para o bot
```

| Comando                                 | O que faz                             |
| --------------------------------------- | ------------------------------------- |
| `streamlit run app.py`                | Abre a página web                    |
| `python bot.py`                       | Liga o bot do Telegram                |
| `python -m pytest`                    | Roda os testes das regras             |
| `python avaliar.py`                   | Avalia no conjunto de desenvolvimento |
| `python avaliar.py dados/teste.jsonl` | Avalia no conjunto de teste           |

A avaliação guarda as respostas da IA em `resultados/cache_ia.jsonl`. Com o cache do repositório, os números acima são reproduzidos sem novas chamadas à API.

## Estrutura

| Arquivo            | Papel                                                                   |
| ------------------ | ----------------------------------------------------------------------- |
| `sinais.py`      | Lista única dos 39 sinais                                              |
| `regras.py`      | Regras sem IA (V1, V2, C9 e palavras-chave da linha de base)            |
| `ia.py`          | Prompt, chamada ao Gemini, novas tentativas e checagem de evidência    |
| `verificador.py` | Motor usado pela página e pelo bot: junta regras e IA e decide o risco |
| `app.py`         | Página web (Streamlit)                                                 |
| `bot.py`         | Bot do Telegram                                                         |
| `avaliar.py`     | Avaliação: cenários, modos, matriz e erros                           |
| `separar.py`     | Sorteio do `dev` e do `teste`                                       |
| `dados/`         | `casos.jsonl`, `dev.jsonl` e `teste.jsonl`                        |
| `testes/`        | Testes das regras (pytest)                                              |

## Uso de IA no desenvolvimento

Usei o Claude (Anthropic) como assistente durante todo o projeto: para orientação, revisão de código e para escrever partes importantes da implementação, como a interface web, o motor que junta regras e IA e parte das regras e dos testes. O dataset foi gerado com o Gemini a partir das fontes que pesquisei. A escolha do problema, as decisões de escopo, o prompt, os rótulos e a leitura dos resultados foram meus.

## Fontes

- [Rota Jurídica: denúncias do golpe do falso advogado à OAB-SP](https://www.rotajuridica.com.br/?p=179951)
- [TJDFT: golpe do falso advogado](https://www.tjdft.jus.br/institucional/imprensa/noticias/2026/julho/golpe-do-falso-advogado-saiba-como-identificar-a-fraude-e-proteger-se)
- [TJDFT: golpe do falso contato judicial](https://www.tjdft.jus.br/institucional/imprensa/noticias/2026/setembro/golpe-do-falso-contato-judicial-tjdft-alerta-para-nova-forma-de-fraude)
- [OAB-SP: cartilha do golpe do falso advogado](https://oabsp.org.br/upload/1164693296.pdf)
- [OAB: ConfirmADV](https://www.oab.org.br/noticia/63063/oab-lanca-campanha-nacional-e-plataforma-de-verificacao-contra-golpe-do-falso-advogado)
