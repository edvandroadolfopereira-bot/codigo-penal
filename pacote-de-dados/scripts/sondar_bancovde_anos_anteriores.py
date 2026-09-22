# -*- coding: utf-8 -*-
"""Existe banco do Sinesp VDE antes de 2015? Teste discriminante (22/09/2026).

A pagina oficial do Ministerio da Justica lista, para baixar, bancovde-2015.xlsx ate
bancovde-2026.xlsx, sempre no mesmo padrao de endereco. O acervo desta maquina ja tem esses
doze. A pergunta que decide se a serie do Sinesp JC, de 2004 a 2022, esta ao alcance e outra:
o mesmo padrao responde para os anos ANTERIORES, que a pagina nao lista?

Por que o teste precisa olhar o BYTE, e nao o codigo HTTP: esta casa ja mediu, no CJF em
02/08/2026, que pedir arquivo inexistente devolve HTTP 200 com a pagina inicial em HTML.
Codigo 200 nao prova arquivo. Um xlsx e um zip, e comeca com os bytes 50 4B, que sao "PK".

Ano de controle: 2015 e 2016 sao listados pela pagina e TEM que responder com xlsx de verdade.
Se eles falharem, quem esta errado e a sonda, e nao a fonte, e o veredito sai como nao medido.

Codigo de saida: 0 se os anos de controle responderam e a medicao valeu; 2 se os controles
falharam, que e ausencia de medicao e nunca conclusao.
"""
import io
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(R, "analise-cientifica", "sonda-bancovde-anos-anteriores.json")
PADRAO = ("https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/"
          "download/dnsp-base-de-dados/bancovde-%d.xlsx/@@download/file")
ANOS_TESTADOS = list(range(2004, 2015))   # os que a pagina NAO lista
ANOS_DE_CONTROLE = [2015, 2016]           # os que a pagina lista, e tem que funcionar
ESPERA = 1.5
ASSINATURA_XLSX = b"PK"


def pedir(ano):
    from curl_cffi import requests as cr
    try:
        r = cr.get(PADRAO % ano, timeout=60, impersonate="chrome", verify=False)
    except Exception as e:
        return {"ano": ano, "situacao": "NAO RESPONDEU",
                "motivo": "%s: %s" % (type(e).__name__, str(e)[:200])}
    corpo = r.content or b""
    # so' a assinatura, dois bytes: nao e amostra de acervo, e leitura de formato
    e_xlsx = corpo.startswith(ASSINATURA_XLSX)
    return {"ano": ano, "http": r.status_code, "bytes": len(corpo),
            "tipo_de_conteudo": r.headers.get("content-type", ""),
            "comeca_com_PK_logo_e_xlsx": e_xlsx,
            "situacao": "XLSX DE VERDADE" if e_xlsx and len(corpo) > 1000
                        else "NAO E XLSX"}


def main():
    controles = []
    for ano in ANOS_DE_CONTROLE:
        c = pedir(ano)
        controles.append(c)
        print("controle %d: %s | http %s | %s bytes"
              % (ano, c["situacao"], c.get("http", "-"), c.get("bytes", 0)))
        time.sleep(ESPERA)
    if not all(c["situacao"] == "XLSX DE VERDADE" for c in controles):
        print("NAO CONCLUIU: os anos de controle nao responderam com xlsx, entao a sonda nao "
              "esta medindo o que diz medir. Nada se conclui sobre os anos anteriores.")
        io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(json.dumps(
            {"situacao": "NAO CONCLUIU", "controles": controles}, ensure_ascii=False, indent=1))
        os.replace(SAIDA + ".tmp", SAIDA)
        return 2

    testados, achados = [], []
    for ano in ANOS_TESTADOS:
        t = pedir(ano)
        testados.append(t)
        if t["situacao"] == "XLSX DE VERDADE":
            achados.append(ano)
        print("%d: %s | http %s | %s bytes"
              % (ano, t["situacao"], t.get("http", "-"), t.get("bytes", 0)))
        time.sleep(ESPERA)

    res = {"gerado_por": "sondar_bancovde_anos_anteriores.py",
           "data": time.strftime("%Y-%m-%d %H:%M:%S"),
           "pergunta": "o padrao de endereco do banco do Sinesp VDE responde para os anos "
                       "anteriores a 2015, que a pagina oficial nao lista?",
           "padrao_de_endereco": PADRAO % 0,
           "anos_de_controle": controles, "anos_testados": testados,
           "anos_com_arquivo_de_verdade": achados,
           "criterio": "o corpo tem que comecar com os bytes PK, que e a assinatura do xlsx, e "
                       "passar de mil bytes; codigo HTTP 200 sozinho nao prova arquivo",
           "resposta": ("a fonte oficial oferece %d ano(s) anterior(es) a 2015" % len(achados))
                       if achados else
                       "a fonte oficial NAO oferece nenhum ano anterior a 2015 neste padrao"}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)
    print("\n%s" % res["resposta"])
    print("gravado:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
