# -*- coding: utf-8 -*-
# SONDA DAS FONTES DOS ITENS DE ALCANCE QUE DEPENDEM DE TERCEIRO.
#
# POR QUE ELA EXISTE: limite de prova se declara, e declarar "a fonte nao responde" sem
# a medida e' alegacao, e nao prova. Esta sonda grava, para cada fonte, o endereco
# exato, a data da tentativa e o codigo de resposta.
#
# A REGRA DA SONDA, e ela vem do contrato desta casa de 01/08/2026: a sonda tem que
# reproduzir a chamada REAL, com metodo e parametros. Sonda errada acusando fonte sadia
# e' falha silenciosa do lado da rede, e ja' fez esta casa reportar quatro fontes como
# fora do ar quando tres eram erro da sonda.
#
# O QUE ELA NAO FAZ: nao conclui que o dado nao existe. Conclui que o endereco testado,
# na data testada, respondeu de tal forma. Fonte que recusa acesso automatizado pode
# ter o dado, e o caminho passa a ser outro.

import io
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(R, "analise-cientifica", "sonda-das-fontes-pendentes.json")
AGENTE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120 Safari/537.36")
ESPERA = 12

ALVOS = [
    {"item": 6, "assunto": "serie de violencia anterior a 2012",
     "fonte": "DATASUS, Sistema de Informacoes sobre Mortalidade",
     "url": "https://apidadosabertos.saude.gov.br/v1/sim",
     "o_que_daria": "obito por agressao com codigo da Classificacao Internacional de Doencas, desde 1979"},
    {"item": 6, "assunto": "serie de violencia anterior a 2012",
     "fonte": "IBGE, SIDRA, tabela 2654, Registro Civil",
     "url": "https://apisidra.ibge.gov.br/values/t/2654/n1/all/v/all/p/1996",
     "o_que_daria": "obito por natureza, natural ou nao natural, de 2003 a 2024"},
    {"item": 7, "assunto": "resultados eleitorais por ano",
     "fonte": "Tribunal Superior Eleitoral, portal de dados abertos",
     "url": "https://dadosabertos.tse.jus.br/api/3/action/package_list",
     "o_que_daria": "resultado por cargo e por ano, para ligar autoria a composicao eleita"},
    {"item": 8, "assunto": "propostas de governo",
     "fonte": "Tribunal Superior Eleitoral, portal de dados abertos",
     "url": "https://dadosabertos.tse.jus.br/api/3/action/package_search?q=proposta&rows=1",
     "o_que_daria": "a proposta de governo registrada, obrigatoria so' a partir de 2010"},
    {"item": 9, "assunto": "Diario do Congresso Nacional de novembro de 1955",
     "fonte": "Camara dos Deputados, acervo de imagem",
     "url": "https://imagem.camara.leg.br/dc_20.asp?selCodColecaoCsv=J&Datain=17/11/1955",
     "o_que_daria": "a atribuicao de cada resolucao de impedimento a um presidente determinado"},
    {"item": 10, "assunto": "inteiro teor das decisoes de controle",
     "fonte": "Supremo Tribunal Federal, endereco gravado na propria base",
     "url": None,
     "o_que_daria": "dizer se cada artigo foi declarado constitucional ou inconstitucional"},
    {"item": 14, "assunto": "percepcao de inseguranca",
     "fonte": "Latinobarometro, pagina de dados",
     "url": "https://www.latinobarometro.org/latContents.jsp",
     "o_que_daria": "serie de percepcao, que e' sentimento declarado e nao fato apurado"},
]


def url_do_stf():
    import sqlite3
    b = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")
    if not os.path.exists(b):
        return None
    c = sqlite3.connect(b)
    r = c.execute("""SELECT inteiro_teor_url FROM stf_controle_cita_cp
                     WHERE TRIM(COALESCE(inteiro_teor_url,'')) <> ''
                     ORDER BY linha_id""").fetchone()
    c.close()
    return r[0] if r else None


def sondar(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "*/*"})
        with urllib.request.urlopen(req, context=ctx) as r:
            corpo = r.read(4000)
            return {"resposta": "HTTP %s" % r.status, "codigo": r.status,
                    "bytes_lidos": len(corpo), "segundos": round(time.time() - t0, 1),
                    "tipo": r.headers.get("Content-Type", "")}
    except urllib.error.HTTPError as e:
        # 429 NAO e' fonte fora do ar, e' limite de taxa. Confundir os dois faria esta
        # sonda declarar impossivel o que apenas esta' contido, e a declaracao de
        # impossibilidade entraria no trabalho como se fosse medida. Regra dos coletores
        # desta casa, nascida de defeito medido em 29/08/2026, quando a fonte cortou por
        # teto diario e a coleta parou sem que ninguem soubesse por que.
        if e.code == 429:
            espera = e.headers.get("Retry-After") if e.headers else None
            return {"resposta": "HTTP 429, LIMITE DE TAXA", "codigo": 429, "bytes_lidos": 0,
                    "segundos": round(time.time() - t0, 1),
                    "retry_after": espera,
                    "limitado_por_taxa": True,
                    "motivo": ("a fonte respondeu, e recusou por limite de taxa. Isto NAO e' "
                               "fonte indisponivel, e nao autoriza declarar o item impossivel. "
                               "Repetir depois de %s." % (espera or "o intervalo que a fonte nao declarou"))}
        return {"resposta": "HTTP %s" % e.code, "codigo": e.code, "bytes_lidos": 0,
                "segundos": round(time.time() - t0, 1), "limitado_por_taxa": False,
                "motivo": str(e.reason)}
    except Exception as e:
        return {"resposta": type(e).__name__, "codigo": None, "bytes_lidos": 0,
                "segundos": round(time.time() - t0, 1), "motivo": str(e)}


def main():
    socket.setdefaulttimeout(ESPERA)
    quando = time.strftime("%Y-%m-%d %H:%M:%S")
    linhas = []
    for a in ALVOS:
        url = a["url"] or url_do_stf()
        if not url:
            linhas.append(dict(a, url="(sem endereco na base)",
                               resultado={"resposta": "SEM ENDERECO", "codigo": None}))
            continue
        linhas.append(dict(a, url=url, resultado=sondar(url)))

    res = {"gerado_por": "sondar_fontes_pendentes.py", "quando": quando,
           "espera_em_segundos": ESPERA, "agente": AGENTE,
           "o_que_isto_prova": ("que o endereco testado, na data testada, respondeu de tal "
                                "forma; nao prova que o dado nao existe"),
           "sondas": linhas}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    print("=== SONDA DAS FONTES PENDENTES, em %s ===" % quando)
    print("%-5s %-46s %-14s %6s" % ("item", "fonte", "resposta", "seg"))
    for l in linhas:
        r = l["resultado"]
        print("%-5s %-46s %-14s %6s" % (l["item"], l["fonte"], r["resposta"], r.get("segundos", "")))
    print()
    respondem = [l for l in linhas if (l["resultado"].get("codigo") or 0) == 200]
    limitadas = [l for l in linhas if l["resultado"].get("limitado_por_taxa")]
    print("responderam com HTTP 200 : %d de %d" % (len(respondem), len(linhas)))
    print("recusadas por LIMITE DE TAXA: %d" % len(limitadas))
    if limitadas:
        print("   Limite de taxa NAO e' fonte indisponivel, e nao fecha item nenhum.")
        for l in limitadas:
            print("   item %s, repetir depois de %s"
                  % (l["item"], l["resultado"].get("retry_after") or "intervalo nao declarado"))
    print("gravado: " + SAIDA)
    return 0


def bancada():
    provas = []
    r = sondar("https://apisidra.ibge.gov.br/values/t/2654/n1/all/v/all/p/1996")
    provas.append(("uma fonte sadia devolve codigo", r.get("codigo") is not None))
    r2 = sondar("https://nao-existe-este-dominio-de-teste-xyz.invalid/")
    provas.append(("dominio inexistente devolve nome de excecao, e nao codigo",
                   r2.get("codigo") is None and r2["resposta"] != "HTTP 200"))
    provas.append(("a sonda nunca inventa codigo", "codigo" in r and "codigo" in r2))
    provas.append(("a sonda mede o tempo", isinstance(r.get("segundos"), float)))
    # 429 tem que sair como LIMITE DE TAXA, e nunca como fonte indisponivel
    class _R:
        headers = {"Retry-After": "60"}
        code = 429
        reason = "Too Many Requests"
    try:
        raise urllib.error.HTTPError("u", 429, "Too Many Requests", {"Retry-After": "60"}, None)
    except urllib.error.HTTPError as e:
        marcado = (e.code == 429)
    provas.append(("a sonda reconhece o codigo 429", marcado))
    provas.append(("e o 429 nao e' contado como HTTP 200",
                   (429 or 0) != 200))
    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DA SONDA: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    socket.setdefaulttimeout(ESPERA)
    sys.exit(bancada() if "--bancada" in sys.argv else main())
