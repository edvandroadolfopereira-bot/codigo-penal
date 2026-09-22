# -*- coding: utf-8 -*-
"""O que as notas dos gestores estaduais do Sinesp JC declaram (22/09/2026).

De onde veio: a pagina oficial "Notas dos Gestores Estaduais - Sinesp JC (2004-2022)" do
Ministerio da Justica e Seguranca Publica, publicada em 14/02/2019 e atualizada em 15/08/2023.
Ela NAO publica a serie: publica as notas metodologicas que cada Unidade da Federacao enviou.

Por que ela importa mais do que a serie importaria: as notas declaram, pela palavra do proprio
gestor estadual, que a mesma rubrica conta coisas diferentes em cada estado. Isso nao e
suposicao deste trabalho, e citacao literal da fonte, e sustenta a decisao de nao emendar as
series de violencia numa so.

O que este script faz: separa o texto por Unidade da Federacao e procura, em cada uma, a
declaracao sobre os pontos que mudam o numero. Cada achado sai com o TRECHO LITERAL ao lado,
porque afirmacao sobre o que a fonte diz se prova citando a fonte.
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(os.environ["USERPROFILE"], ".claude", "memoria-claude",
                     "projeto-codigo-penal-material-interno", "_sinesp-jc-notas-texto.txt")
SAIDA = os.path.join(R, "analise-cientifica", "notas-sinesp-jc.json")

# na ordem em que a pagina as apresenta; o cabecalho de cada uma vem em caixa alta
UFS = ["ACRE", "BAHIA", "CEARÁ", "GOIÁS", "MINAS GERAIS", "MATO GROSSO DO SUL", "MATO GROSSO",
       "PARÁ", "PARAÍBA", "PERNAMBUCO", "PIAUÍ", "PARANÁ", "RIO DE JANEIRO", "RONDÔNIA",
       "SÃO PAULO", "TOCANTINS"]

# cada ponto traz o padrao que o localiza e o que ele decide no numero final
PONTOS = [
    ("morte por intervencao policial", r"(interven[çc][ãa]o (?:de agente|policial|de agentes)"
                                       r"[^.]{0,400}\.)"),
    ("feminicidio dentro do homicidio doloso", r"(feminic[íi]dio[^.]{0,300}\.)"),
    ("doloso e culposo nao separados", r"(sem a diferencia[çc][ãa]o[^.]{0,200}\.)"),
    ("morte a esclarecer somada ao homicidio", r"(morte a esclarecer[^.]{0,300}\.)"),
    ("ano ou periodo sem dado", r"((?:n[ãa]o (?:foi poss[íi]vel|existiam|est[ãa]o dispon[íi]veis)|"
                                r"dispon[íi]veis apenas a partir|ficaram temporariamente inst[áa]veis|"
                                r"n[ãa]o foram consolidados|dados referentes aos temas estarem retidos)"
                                r"[^.]{0,300}\.)"),
]


def fatiar(texto):
    """Devolve {UF: trecho}, cortando do cabecalho de uma ate o da seguinte."""
    pos = []
    for uf in UFS:
        # o cabecalho e a ocorrencia em caixa alta sozinha na linha, ou seguida de quebra
        for m in re.finditer(r"(?:^|\n|\s)" + re.escape(uf) + r"(?:\s*\n|\s{2,})", texto):
            pos.append((m.start(), uf))
            break
    pos.sort()
    fatias = {}
    for i, (ini, uf) in enumerate(pos):
        fim = pos[i + 1][0] if i + 1 < len(pos) else len(texto)
        fatias[uf] = texto[ini:fim]
    return fatias


def main():
    if not os.path.exists(FONTE):
        print("NAO MEDIU: o texto da pagina nao esta em %s" % FONTE)
        return 2
    texto = io.open(FONTE, encoding="utf-8").read()
    fatias = fatiar(texto)
    faltando = [u for u in UFS if u not in fatias]
    achados, por_ponto = {}, {p: 0 for p, _ in PONTOS}
    for uf, tr in fatias.items():
        linhas = []
        for ponto, padrao in PONTOS:
            for m in re.finditer(padrao, tr, re.I | re.S):
                linhas.append({"ponto": ponto,
                               "trecho_literal": re.sub(r"\s+", " ", m.group(1)).strip()})
                por_ponto[ponto] += 1
        achados[uf] = {"caracteres_da_nota": len(tr), "declaracoes": linhas}

    res = {
        "gerado_por": "apurar_notas_sinesp_jc.py", "data": "2026-09-22",
        "fonte": ("BRASIL. Ministério da Justiça e Segurança Pública. Notas dos Gestores "
                  "Estaduais: Sinesp JC (2004-2022). Publicado em 14/02/2019, atualizado em "
                  "15/08/2023. Disponível em: https://www.gov.br/mj/pt-br/assuntos/"
                  "sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/"
                  "notas-dos-gestores-estaduais. Acesso em: 22 set. 2026."),
        "o_que_a_pagina_publica": ("as notas metodológicas enviadas pelas Unidades da Federação, "
                                   "e NAO a série do Sinesp JC"),
        "unidades_da_federacao_com_nota": len(fatias),
        "unidades_da_federacao_sem_nota": 27 - len(fatias),
        "unidades_procuradas_e_nao_encontradas": faltando,
        "declaracoes_por_ponto": por_ponto,
        "por_unidade_da_federacao": achados,
        "o_que_isto_sustenta": [
            "a mesma rubrica conta coisas diferentes em cada Unidade da Federação, pela "
            "declaração do próprio gestor estadual",
            "a comparação entre estados na série do Sinesp JC não se sustenta sem essas notas "
            "ao lado, e por isso ela não foi emendada às demais séries deste trabalho"],
        "o_que_isto_NAO_diz": [
            "não diz que algum estado informou dado errado: diz que os critérios declarados "
            "diferem entre si",
            "não substitui a série: a página publica as notas, e a série não está nela"]}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)

    print("unidades com nota: %d de 27 | sem nota: %d" % (len(fatias), 27 - len(fatias)))
    if faltando:
        print("NAO ENCONTRADAS no texto:", ", ".join(faltando))
    for p, n in por_ponto.items():
        print("   %-42s %d declaracao(oes)" % (p, n))
    print("gravado:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
