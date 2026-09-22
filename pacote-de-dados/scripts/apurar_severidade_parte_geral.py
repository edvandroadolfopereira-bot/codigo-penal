# REGUA DE SEVERIDADE DA PARTE GERAL do Codigo Penal, 1940 contra o texto vigente.
#
# POR QUE ELA NAO EXISTIA, e por que a regua de faixa de pena nunca a alcancaria:
# a Parte Geral nao comina pena, ela fixa PARAMETRO. Dos 130 eventos datados de
# severidade do trabalho, zero e' dela. Severidade ali muda por limite de tempo,
# fracao de cumprimento, prazo de prescricao e periodo de prova.
#
# O ACHADO QUE MUDOU O DESENHO, medido em 30/08/2026: a Lei 7.209/1984 remanejou a
# NUMERACAO INTEIRA da Parte Geral. Comparar o artigo N de 1940 com o artigo N de
# hoje compara coisas diferentes, e produziria numero com cara de medida:
#
#   art. 33  1940 doenca mental superveniente   hoje regimes de cumprimento
#   art. 44  1940 agravantes                    hoje penas restritivas de direitos
#   art. 61  1940 condicoes do livramento       hoje agravantes
#   art. 64  1940 revogacao do livramento       hoje reincidencia
#   art. 70  1940 perda de funcao publica       hoje concurso formal
#   art. 75  1940 medidas de seguranca          hoje limite de 40 anos
#   art. 77  1940 presuncao de periculosidade   hoje suspensao condicional
#   art. 83  1940 medida de seguranca           hoje livramento condicional
#
# Por isso a regua pareia por INSTITUTO, e nunca por numero de artigo.
#
# O NUMERO E' EXTRAIDO DO TEXTO, e nao digitado aqui. Digitar o valor seria eu
# afirmar a medida em vez de medi-la, que e' o defeito que esta casa combate desde
# 30/07/2026. O que esta' declarado no codigo e' ONDE procurar e QUAL a regra de
# direcao; o valor sai do texto oficial das duas epocas.
#
# A REGRA DE DIRECAO VAI ESCRITA EM CADA INSTITUTO, porque ela nao e' obvia e
# inverte de um para o outro: prazo de prescricao maior e' mais severo, mas periodo
# de prova de suspensao maior tambem e', enquanto fracao de livramento maior e' mais
# severa e limiar de pena para caber no beneficio maior tambem e'.

import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.abspath(__file__))
TEXTO_HOJE = os.path.join(RAIZ, "cp-compilado-texto.txt")
TEXTO_1940 = os.path.join(RAIZ, "textos-das-normas", "codigo-penal-1940-texto-original.json")
SAIDA = os.path.join(RAIZ, "analise-cientifica", "severidade-parte-geral.json")

_EXTENSO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3, "quatro": 4,
    "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11,
    "doze": 12, "quinze": 15, "dezesseis": 16, "vinte": 20, "trinta": 30,
    "quarenta": 40, "sessenta": 60, "setenta": 70,
}
_FRACAO = {
    "metade": 0.5, "meio": 0.5, "um terco": 1 / 3, "um terço": 1 / 3,
    "dois tercos": 2 / 3, "dois terços": 2 / 3, "tres quartos": 0.75,
    "três quartos": 0.75, "um quarto": 0.25, "um sexto": 1 / 6, "triplo": 3.0,
}

MAIOR_E_MAIS_SEVERO = "maior e' mais severo"
MENOR_E_MAIS_SEVERO = "menor e' mais severo"


def normaliza(t):
    t = t.replace("&#150;", "-").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t)


def artigos(texto):
    """Leitor monotonico: 'Art. N' com N menor que o corrente e' remissao, nao artigo.

    Sem isso, 'observa-se o disposto nos arts. 51, 52 e 53' abriria tres artigos
    falsos no meio do art. 56.
    """
    achados, corrente = [], 0
    for m in re.finditer(r"Art\.?\s*(\d+)", texto):
        n = int(m.group(1))
        if n <= corrente:
            continue
        corrente = n
        achados.append((n, m.start()))
    saida = {}
    for i, (n, ini) in enumerate(achados):
        fim = achados[i + 1][1] if i + 1 < len(achados) else len(texto)
        saida[n] = normaliza(texto[ini:fim])
    return saida


def numero(txt):
    """Le numero por algarismo ou por extenso, nesta ordem."""
    if txt is None:
        return None
    t = txt.strip().lower()
    m = re.match(r"^(\d+)$", t)
    if m:
        return float(m.group(1))
    if t in _FRACAO:
        return _FRACAO[t]
    if t in _EXTENSO:
        return float(_EXTENSO[t])
    return None


# Cada instituto declara: onde procurar em cada epoca, o que extrair, e a regra de
# direcao. AUSENTE significa que o instituto nao existia naquela epoca, e isso e'
# achado, nunca zero.
INSTITUTOS = [
    {
        "instituto": "Limite maximo de cumprimento da pena privativa de liberdade",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "teto de tempo que o condenado pode cumprir; teto maior prende por mais tempo",
        "em_1940": (55, r"n[ãa]o pode,? em caso algum,? ser superior a ([a-zçà-ü]+|\d+) anos"),
        "em_hoje": (75, r"n[ãa]o pode ser superior a (\d+)"),
    },
    {
        "instituto": "Livramento condicional, fracao exigida do primario",
        "unidade": "fracao da pena",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "fracao maior obriga a cumprir mais antes de sair",
        "em_1940": (60, r"cumprida mais de (metade|um ter[cç]o|dois ter[cç]os|tr[êe]s quartos) da pena"),
        "em_hoje": (83, r"I - cumprida mais de (um ter[cç]o|metade|dois ter[cç]os) da pena"),
    },
    {
        "instituto": "Livramento condicional, fracao exigida do reincidente",
        "unidade": "fracao da pena",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "mesma razao, para o reincidente",
        "em_1940": (60, r"e mais de (tr[êe]s quartos|dois ter[cç]os|metade),? se reincidente"),
        "em_hoje": (83, r"II - cumprida mais d[ae] (metade|um ter[cç]o|dois ter[cç]os)"),
    },
    {
        "instituto": "Livramento condicional, pena minima para caber no beneficio",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "limiar maior deixa MENOS condenados alcancados pelo beneficio",
        "em_1940": (60, r"pena de reclus[ãa]o ou de deten[cç][ãa]o superior a ([a-zçà-ü]+|\d+) anos"),
        "em_hoje": (83, r"pena privativa de liberdade igual ou superior a (\d+)"),
    },
    {
        "instituto": "Prescricao, prazo mais curto da escala",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "prazo maior mantem o Estado apto a punir por mais tempo",
        "em_1940": (109, r"VI - em ([a-zçà-ü]+|\d+) anos, se o m[áa]ximo da pena [ée] inferior a um ano"),
        "em_hoje": (109, r"VI - em (\d+) \([a-zçà-ü]+\) anos"),
    },
    {
        "instituto": "Prescricao, prazo mais longo da escala",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "mesma razao, no topo da escala",
        "em_1940": (109, r"I - em ([a-zçà-ü]+) anos, se o m[áa]ximo da pena [ée] superior a doze"),
        "em_hoje": (109, r"I - em ([a-zçà-ü]+) anos, se o m[áa]ximo da pena [ée] superior a doze"),
    },
    {
        "instituto": "Reincidencia, periodo depurador",
        "unidade": "anos",
        "regra": MENOR_E_MAIS_SEVERO,
        "porque": ("periodo depurador e' o prazo apos o qual a condenacao anterior deixa de "
                   "pesar; prazo menor liberta antes, e ausencia de prazo e' reincidencia "
                   "perpetua, o extremo severo"),
        "em_1940": (46, r"decorrido per[ií]odo de tempo superior a ([a-zçà-ü]+|\d+)"),
        "em_hoje": (64, r"decorrido per[ií]odo de tempo superior a (\d+)"),
    },
    {
        "instituto": "Suspensao condicional da pena, periodo de prova maximo",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "periodo de prova maior mantem o condenado sob condicao por mais tempo",
        "em_1940": (57, r"pode ser suspensa, por dois a ([a-zçà-ü]+) anos"),
        "em_hoje": (77, r"poder[áa] ser suspensa, por \d+ \([a-zçà-ü]+\) a (\d+)"),
    },
    {
        "instituto": "Suspensao condicional da pena, teto de pena que a admite",
        "unidade": "anos",
        "regra": MENOR_E_MAIS_SEVERO,
        "porque": "teto menor deixa MENOS condenados alcancados pelo beneficio",
        "em_1940": (57, r"pena de deten[cç][ãa]o n[ãa]o superior a ([a-zçà-ü]+|\d+) anos"),
        "em_hoje": (77, r"n[ãa]o superior a (\d+)"),
    },
    {
        "instituto": "Tentativa, diminuicao maxima",
        "unidade": "fracao da pena",
        "regra": MENOR_E_MAIS_SEVERO,
        "porque": "diminuicao maior beneficia mais",
        "em_1940": (12, r"diminuida de um a (dois ter[cç]os|metade)"),
        "em_hoje": (14, r"diminu[íi]da de um a (dois ter[cç]os|metade)"),
    },
    {
        "instituto": "Concurso formal, aumento maximo",
        "unidade": "fracao da pena",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "aumento maior agrava",
        "em_1940": (51, r"aumentada, em qualquer caso, de um sexto at[ée] (metade|dois ter[cç]os)"),
        "em_hoje": (70, r"aumentada, em qualquer caso, de um sexto at[ée] (metade|dois ter[cç]os)"),
    },
    {
        "instituto": "Crime continuado, aumento maximo da regra geral",
        "unidade": "fracao da pena",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "aumento maior agrava",
        "em_1940": (51, r"aumentada, em qualquer caso, de um sexto a (dois ter[cç]os|metade)"),
        "em_hoje": (71, r"aumentada, em qualquer caso, de um sexto a (dois ter[cç]os|metade)"),
    },
    {
        "instituto": "Crime continuado, teto especial para crime doloso com violencia",
        "unidade": "multiplicador da pena",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "teto multiplicador maior agrava; ausencia em 1940 significa que a regra nao existia",
        "em_1940": (51, r"at[ée] o (triplo|dobro)"),
        "em_hoje": (71, r"at[ée] o (triplo|dobro)"),
    },
    {
        "instituto": "Reabilitacao, prazo minimo para o primario",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": "prazo maior mantem por mais tempo o efeito da condenacao",
        "em_1940": (119, r"ap[óo]s o decurso de ([a-zçà-ü]+|\d+) anos"),
        "em_hoje": (94, r"decorridos (\d+) \([a-zçà-ü]+\) anos"),
    },
    {
        "instituto": "Reabilitacao, prazo agravado do reincidente",
        "unidade": "anos",
        "regra": MAIOR_E_MAIS_SEVERO,
        "porque": ("prazo proprio e maior para o reincidente; a ausencia hoje significa que a "
                   "distincao desapareceu, e o reincidente passou ao prazo comum"),
        "em_1940": (119, r"se o condenado [ée] reincidente, o prazo m[íi]nimo para a rehabilita[cç][ãa]o [ée] de ([a-zçà-ü]+|\d+) anos"),
        "em_hoje": (94, r"reincidente.{0,80}?prazo.{0,40}?(\d+)"),
    },
    {
        "instituto": "Reducao do prazo prescricional por idade",
        "unidade": "fracao do prazo",
        "regra": MENOR_E_MAIS_SEVERO,
        "porque": "reducao maior beneficia mais o menor de 21 e o maior de 70",
        "em_1940": (115, r"reduzidos de (metade|um ter[cç]o) os prazos"),
        "em_hoje": (115, r"reduzidos de (metade|um ter[cç]o) os prazos"),
    },
]


# Onde a AUSENCIA de numero tem sentido proprio, ele vai escrito aqui e nunca e'
# convertido em direcao pelo codigo. Ausencia de medicao nao vira zero nem aprovacao,
# pela regra desta casa de 28/08/2026.
LEITURA_SUBSTANTIVA = {
    "Reincidencia, periodo depurador": (
        "Em 1940 nao ha prazo depurador em lugar nenhum da Parte Geral, conferido artigo "
        "por artigo nos 119 artigos: a reincidencia do art. 46 nao caduca por decurso de "
        "tempo. O prazo de cinco anos do art. 64, I, criado pela Lei 7.209/1984, portanto "
        "substitui a ausencia de limite, que e' o estado mais severo possivel. A leitura "
        "substantiva e' de ABRANDAMENTO, e ela nao entra na contagem porque nao ha numero "
        "de 1940 para subtrair."),
    "Crime continuado, teto especial para crime doloso com violencia": (
        "O teto de ate' o triplo do art. 71, paragrafo unico, nao tem contraparte em 1940. "
        "A leitura substantiva e' de AGRAVAMENTO, e tambem nao entra na contagem."),
    "Reabilitacao, prazo agravado do reincidente": (
        "Em 1940 o reincidente esperava oito anos, o dobro do primario. Hoje o art. 94 nao "
        "distingue, e o reincidente espera os mesmos dois anos. A leitura substantiva e' de "
        "ABRANDAMENTO."),
    "Suspensao condicional da pena, teto de pena que a admite": (
        "O numero e' o mesmo, dois anos, e por isso a regua devolve mantem. O ALCANCE nao "
        "e': em 1940 o beneficio so' alcancava a detencao, e a reclusao apenas no caso "
        "estreito do art. 30, paragrafo 3; hoje alcanca qualquer pena privativa de "
        "liberdade. A regua mede o numero, e nao o alcance, e isso se declara."),
}


def valor(dic, artigo, padrao):
    txt = dic.get(artigo)
    if txt is None:
        return None, "artigo ausente"
    m = re.search(padrao, txt, re.I)
    if not m:
        return None, "instituto ausente no artigo"
    v = numero(m.group(1))
    if v is None:
        return None, "achado %r e nao convertido em numero" % m.group(1)
    return v, m.group(0)


def direcao(v40, vho, regra):
    if v40 is None and vho is None:
        return "ausente nas duas epocas"
    if v40 is None:
        return "instituto CRIADO depois de 1940"
    if vho is None:
        return "instituto EXTINTO depois de 1940"
    if abs(v40 - vho) < 1e-9:
        return "mantem"
    subiu = vho > v40
    if regra == MAIOR_E_MAIS_SEVERO:
        return "agrava" if subiu else "abranda"
    return "abranda" if subiu else "agrava"


def apurar():
    if not (os.path.exists(TEXTO_HOJE) and os.path.exists(TEXTO_1940)):
        print("FALHA REAL: falta o texto de uma das epocas.")
        return 1
    hoje = artigos(io.open(TEXTO_HOJE, encoding="utf-8").read())
    mil = artigos(json.load(io.open(TEXTO_1940, encoding="utf-8"))["texto"])

    linhas, contagem = [], {}
    for it in INSTITUTOS:
        a40, p40 = it["em_1940"]
        aho, pho = it["em_hoje"]
        v40, t40 = valor(mil, a40, p40)
        vho, tho = valor(hoje, aho, pho)
        d = direcao(v40, vho, it["regra"])
        contagem[d] = contagem.get(d, 0) + 1
        linhas.append({
            "instituto": it["instituto"], "unidade": it["unidade"],
            "regra_de_direcao": it["regra"], "porque": it["porque"],
            "artigo_em_1940": a40, "valor_em_1940": v40, "trecho_em_1940": t40,
            "artigo_hoje": aho, "valor_hoje": vho, "trecho_hoje": tho,
            "direcao": d,
            "leitura_substantiva": LEITURA_SUBSTANTIVA.get(it["instituto"]),
        })

    res = {
        "gerado_por": "apurar_severidade_parte_geral.py",
        "o_que_mede": ("parametro numerico de instituto da Parte Geral, 1940 contra o texto "
                       "vigente, pareado por INSTITUTO e nunca por numero de artigo"),
        "porque_nao_por_numero_de_artigo": ("a Lei 7.209/1984 remanejou a numeracao inteira da "
                                            "Parte Geral; o art. 44 de 1940 sao as agravantes e "
                                            "hoje sao as penas restritivas de direitos"),
        "o_que_nao_mede": ("pena de multa, porque 1940 a fixa em contos de reis e hoje em "
                           "dias-multa, e comparar exigiria conversao monetaria de 86 anos; e "
                           "instituto sem parametro numerico, como o regime progressivo de "
                           "cumprimento, criado em 1984 e sem contraparte de 1940"),
        "institutos_medidos": len(INSTITUTOS),
        "contagem_por_direcao": contagem,
        "institutos": linhas,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    print("=== REGUA DE SEVERIDADE DA PARTE GERAL, por instituto ===")
    print("%-58s %-12s %-12s %s" % ("instituto", "1940", "hoje", "direcao"))
    print("-" * 108)
    naolidos = 0
    for l in linhas:
        f = lambda v: ("ausente" if v is None else
                       ("%.4g" % v if v != int(v) else "%d" % int(v)))
        print("%-58s %-12s %-12s %s" % (l["instituto"][:58], f(l["valor_em_1940"]),
                                        f(l["valor_hoje"]), l["direcao"]))
        if l["valor_em_1940"] is None and l["valor_hoje"] is None:
            naolidos += 1
    print()
    print("contagem por direcao:")
    for k in sorted(contagem):
        print("   %-38s %d" % (k, contagem[k]))
    print()
    print("gravado: " + SAIDA)
    if naolidos:
        print("ATENCAO: %d institutos nao foram lidos em nenhuma das duas epocas." % naolidos)
        print("Isso e' AUSENCIA DE MEDICAO, e nao ausencia do instituto.")
        return 1
    return 0


def bancada():
    """Mede as duas direcoes e DESLIGA o leitor, exigindo que o veredito mude."""
    provas = []
    provas.append(("numero por algarismo", numero("40") == 40.0))
    provas.append(("numero por extenso", numero("trinta") == 30.0))
    provas.append(("fracao metade", abs(numero("metade") - 0.5) < 1e-9))
    provas.append(("fracao dois tercos", abs(numero("dois terços") - 2 / 3) < 1e-9))
    provas.append(("texto que nao e' numero devolve None", numero("banana") is None))

    provas.append(("maior e' mais severo, subiu, agrava",
                   direcao(30, 40, MAIOR_E_MAIS_SEVERO) == "agrava"))
    provas.append(("maior e' mais severo, desceu, abranda",
                   direcao(0.5, 1 / 3, MAIOR_E_MAIS_SEVERO) == "abranda"))
    provas.append(("menor e' mais severo, subiu, abranda",
                   direcao(2, 4, MENOR_E_MAIS_SEVERO) == "abranda"))
    provas.append(("menor e' mais severo, desceu, agrava",
                   direcao(4, 2, MENOR_E_MAIS_SEVERO) == "agrava"))
    provas.append(("igual mantem", direcao(20, 20, MAIOR_E_MAIS_SEVERO) == "mantem"))
    provas.append(("ausente em 1940 e' criacao",
                   direcao(None, 3, MAIOR_E_MAIS_SEVERO) == "instituto CRIADO depois de 1940"))
    provas.append(("ausente hoje e' extincao",
                   direcao(3, None, MAIOR_E_MAIS_SEVERO) == "instituto EXTINTO depois de 1940"))
    provas.append(("ausente nas duas nao vira zero",
                   direcao(None, None, MAIOR_E_MAIS_SEVERO) == "ausente nas duas epocas"))

    # o leitor monotonico: remissao a artigo anterior NAO pode abrir artigo novo
    t = "Art. 56. observa-se o disposto nos arts. 51, 52 e 53, executando-se. Art. 57. A execucao"
    a = artigos(t)
    provas.append(("remissao a artigo menor nao abre artigo novo", sorted(a) == [56, 57]))
    provas.append(("o corpo do art. 56 guarda a remissao", "51, 52 e 53" in a[56]))

    # DESLIGAR o leitor tem que MUDAR o veredito: sem ele, nada e' extraido
    vazio = {}
    v, motivo = valor(vazio, 55, r"superior a (\d+)")
    provas.append(("com o leitor DESLIGADO nada e' extraido", v is None and motivo == "artigo ausente"))
    real = artigos("Art. 55. A duracao das penas nao pode, em caso algum, ser superior a trinta anos.")
    v2, _ = valor(real, 55, r"n[ãa]o pode,? em caso algum,? ser superior a ([a-zçà-ü]+|\d+) anos")
    provas.append(("com o leitor LIGADO extrai 30 do texto", v2 == 30.0))

    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DA REGUA DA PARTE GERAL: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    if "--bancada" in sys.argv:
        sys.exit(bancada())
    sys.exit(apurar())
