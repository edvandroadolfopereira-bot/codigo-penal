# -*- coding: utf-8 -*-
"""Sonda da fonte oficial do Sinesp, para a serie de 2004 a 2022 (22/09/2026).

Por que existe: a serie longa de violencia deste trabalho declara que o Sinesp JC, que cobriu
de 2004 a 2022, NAO esta no acervo desta maquina. Antes de manter essa declaracao, a fonte se
sonda, porque declarar ausencia sem consultar e o defeito que esta casa combate desde
27/07/2026.

O que ela faz e o que NAO faz: ela mede o que cada endereco RESPONDE, com codigo HTTP, tipo de
conteudo e tamanho, e grava tudo integralmente. Ela nao baixa a serie e nao conclui que o dado
existe: responder nao e ter o dado, e isso se confere abrindo o que voltou.

Codigo de saida: 0 se ao menos um endereco respondeu 200 com corpo util; 1 se nenhum respondeu;
2 se a sonda nao concluiu, que e ausencia de medicao e nunca aprovacao.
"""
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(R, "analise-cientifica", "sonda-sinesp-jc.json")
ESPERA = 1.5

# Cada candidato declara o que se espera dele, para a leitura do resultado nao depender de
# lembranca. O portal de dados abertos do governo federal e o do Ministerio da Justica usam
# CKAN, cuja API de busca responde JSON.
CANDIDATOS = [
    ("dados.gov.br, busca CKAN por sinesp",
     "https://dados.gov.br/api/3/action/package_search?q=sinesp&rows=100"),
    ("dados.gov.br, busca CKAN por seguranca publica",
     "https://dados.gov.br/api/3/action/package_search?q=estatisticas+seguranca+publica&rows=100"),
    ("dados.mj.gov.br, busca CKAN por sinesp",
     "https://dados.mj.gov.br/api/3/action/package_search?q=sinesp&rows=100"),
    ("dados.mj.gov.br, lista de conjuntos",
     "https://dados.mj.gov.br/api/3/action/package_list"),
    ("gov.br do MJ, pagina de estatistica da seguranca publica",
     "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica"),
    ("gov.br do MJ, dados nacionais de seguranca publica",
     "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1"),
    ("Sinesp, portal de dados abertos",
     "https://dadosabertos.mj.gov.br/"),
    # Segunda rodada, acrescentada depois da leitura integral da pagina de estatistica do MJ,
    # que descreve o SinespJC desde 2004 e NAO oferece a serie para baixar.
    ("gov.br do MJ, pagina do proprio Sinesp",
     "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/sinesp-1"),
    ("gov.br do MJ, base de dados do Sinesp VDE de 2022 e 2023",
     "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/"
     "dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-"
     "sinesp-vde-2022-e-2023"),
    ("portal nacional, API publica de conjuntos por nome",
     "https://dados.gov.br/api/publico/conjuntos-dados?nomeConjuntoDados=sinesp"),
    ("portal nacional, API publica de conjuntos por tema seguranca",
     "https://dados.gov.br/api/publico/conjuntos-dados?isPrivado=false&nomeConjuntoDados="
     "seguranca%20publica"),
    ("dados abertos do MJ, pagina no gov.br",
     "https://www.gov.br/mj/pt-br/acesso-a-informacao/dados-abertos"),
]


def pedir(url):
    """Uma chamada, com o agente declarado. Devolve o que voltou, ou o motivo de nao ter voltado."""
    try:
        from curl_cffi import requests as cr
        r = cr.get(url, timeout=45, impersonate="chrome", verify=False)
        corpo = r.content or b""
        return {"http": r.status_code, "bytes": len(corpo),
                "tipo": r.headers.get("content-type", ""), "corpo": corpo}
    except Exception as e:
        return {"erro": "%s: %s" % (type(e).__name__, str(e)[:200])}


def main():
    resultados = []
    respondeu_com_corpo = 0
    for rotulo, url in CANDIDATOS:
        r = pedir(url)
        linha = {"o_que_e": rotulo, "url": url}
        if "erro" in r:
            linha["situacao"] = "NAO RESPONDEU"
            linha["motivo"] = r["erro"]
        else:
            linha.update({"http": r["http"], "bytes": r["bytes"], "tipo_de_conteudo": r["tipo"]})
            corpo = r["corpo"]
            if r["http"] == 200 and r["bytes"] > 0:
                respondeu_com_corpo += 1
                linha["situacao"] = "RESPONDEU"
                if "json" in r["tipo"].lower():
                    try:
                        d = json.loads(corpo.decode("utf-8", "replace"))
                        res = d.get("result")
                        if isinstance(res, dict):
                            linha["conjuntos_declarados_pela_fonte"] = res.get("count")
                            linha["titulos"] = [x.get("title") for x in res.get("results", [])]
                        elif isinstance(res, list):
                            linha["conjuntos_declarados_pela_fonte"] = len(res)
                            linha["nomes_com_sinesp"] = [x for x in res
                                                         if "sinesp" in str(x).lower()]
                    except Exception as e:
                        linha["defeito_ao_ler_json"] = str(e)[:200]
                else:
                    texto = corpo.decode("utf-8", "replace").lower()
                    for termo in ("sinesp", "2004", "ocorrencia", "csv", "xlsx"):
                        linha["ocorrencias_de_" + termo] = texto.count(termo)
            else:
                linha["situacao"] = "RESPONDEU SEM CORPO UTIL"
        resultados.append(linha)
        print("%-58s %s" % (rotulo[:58], linha.get("situacao")),
              "http", linha.get("http", "-"), "|", linha.get("bytes", 0), "bytes")
        time.sleep(ESPERA)

    res = {"gerado_por": "sondar_sinesp_jc.py", "data": time.strftime("%Y-%m-%d %H:%M:%S"),
           "o_que_se_procura": "a serie do Sinesp JC, de 2004 a 2022, por unidade da federacao",
           "o_que_esta_sonda_prova": "o que cada endereco responde, e nada alem disso; "
                                     "responder nao e ter o dado",
           "candidatos_sondados": len(CANDIDATOS), "responderam_com_corpo": respondeu_com_corpo,
           "resultados": resultados}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)
    print("gravado:", SAIDA)
    if respondeu_com_corpo == 0:
        print("FALHA REAL: nenhum dos %d enderecos respondeu com corpo util" % len(CANDIDATOS))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
