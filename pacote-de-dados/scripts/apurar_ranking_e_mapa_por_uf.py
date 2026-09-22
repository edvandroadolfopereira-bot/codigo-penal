# -*- coding: utf-8 -*-
"""Ranking por Unidade da Federacao e mapa do Brasil, na serie longa (22/09/2026).

Por que ele pode existir: o Atlas da Violencia nao publica recorte por UF, so pais, regiao e
capital. A base primaria dele, porem, esta no disco por UF: o Sistema de Informacoes sobre
Mortalidade, colhido do TABNET em 21/09/2026, com 27 unidades de 1979 a 2026.

A identidade foi PROVADA antes de usar, e nao suposta: somadas as agressoes (CID-10 X85 a Y09)
com as intervencoes legais (Y35 a Y36), o total nacional do SIM reproduz a serie 328 do Atlas
com diferenca ZERO em cada um dos 29 anos de 1996 a 2024. Quem decompoe por UF, portanto,
decompoe a mesma serie que o trabalho usa no plano nacional.

O que este script NAO faz, e cada recusa tem motivo medido:
  nao emenda a CID-9 com a CID-10 numa serie unica, porque a classificacao muda em 1996;
  nao calcula taxa de 2023, porque o DATASUS repete a populacao de 2022 e repeticao nao e
    estimativa;
  nao usa 2025 nem 2026, porque o SIM ainda esta recebendo registro desses anos: 2026 traz
    11.022 obitos contra 42.590 de 2024, e isso e ano em aberto, nao queda;
  nao separa Tocantins de Goias antes de 1989, porque o SIM so os separa a partir dali;
  nao compara Unidades da Federacao por teste estatistico: o mapa e descritivo.
"""
import io
import json
import os
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(R, "analise-cientifica")
SIM = os.path.join(os.environ["USERPROFILE"], "OneDrive", ".claude",
                   "Biblioteca-Academica-Direito", "datasus-sim-homicidios")
SAIDA = os.path.join(A, "ranking-e-mapa-por-uf.json")

# o SIM nomeia a UF com o codigo do IBGE na frente; a sigla sai daqui, e nunca de adivinhacao
SIGLA = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
         "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
         "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
         "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
PRIMEIRO_ANO_CID10 = 1996
ULTIMO_ANO_FECHADO = 2024       # medido: 2025 e 2026 ainda recebem registro
ANO_SEM_POPULACAO = "2023"      # o DATASUS repete 2022 nas 27 UFs
TOCANTINS_SEPARADO_DE = 1989


def numero(x):
    """O TABNET grava traco para ausencia e ponto de milhar no numero."""
    if x is None or str(x).strip() in ("", "-"):
        return None
    return int(str(x).replace(".", "").replace("\xa0", "").replace(" ", ""))


def ler(nome):
    return json.load(io.open(os.path.join(SIM, nome + ".json"), encoding="utf-8"))


def por_sigla(tabela):
    """{ '11 Rondonia': {...} } vira { 'RO': {...} }, pelo codigo do IBGE."""
    fora, saida = [], {}
    for chave, linha in tabela.items():
        cod = chave.split()[0]
        if cod not in SIGLA:
            fora.append(chave)
            continue
        saida[SIGLA[cod]] = linha
    return saida, fora


def main():
    ag, fora_ag = por_sigla(ler("cid10-agressoes-1996-2026"))
    il, fora_il = por_sigla(ler("cid10-intervencoes-legais-1996-2026"))
    c9, fora_c9 = por_sigla(ler("cid9-homicidios-1979-1995"))
    pop = json.load(io.open(os.path.join(A, "populacao-uf.json"), encoding="utf-8"))
    populacao, fonte_pop = pop["populacao"], pop["fonte_por_ano"]

    if fora_ag or fora_il or fora_c9:
        print("NAO CONCLUIU: linha do SIM sem codigo de UF reconhecido:",
              fora_ag + fora_il + fora_c9)
        return 2

    # CID-10, de 1996 ao ultimo ano fechado: contagem, populacao e taxa por cem mil
    serie, sem_populacao = {}, set()
    for uf in sorted(ag):
        linhas = {}
        for ano in sorted(ag[uf]):
            if not (PRIMEIRO_ANO_CID10 <= int(ano) <= ULTIMO_ANO_FECHADO):
                continue
            n = (numero(ag[uf].get(ano)) or 0) + (numero(il.get(uf, {}).get(ano)) or 0)
            p = populacao.get(uf, {}).get(ano)
            if ano == ANO_SEM_POPULACAO or not p:
                sem_populacao.add(ano)
                linhas[ano] = {"mortes": n, "populacao": None, "taxa_por_cem_mil": None}
            else:
                linhas[ano] = {"mortes": n, "populacao": p,
                               "taxa_por_cem_mil": round(100000.0 * n / p, 2)}
        serie[uf] = linhas

    anos_com_taxa = sorted({a for uf in serie.values() for a, v in uf.items()
                            if v["taxa_por_cem_mil"] is not None})
    primeiro, ultimo = anos_com_taxa[0], anos_com_taxa[-1]

    # ranking do ultimo ano fechado, e a variacao em pontos da taxa entre o primeiro e o ultimo
    ranking = sorted(({"uf": uf,
                       "taxa_no_ultimo_ano": serie[uf][ultimo]["taxa_por_cem_mil"],
                       "mortes_no_ultimo_ano": serie[uf][ultimo]["mortes"],
                       "taxa_no_primeiro_ano": serie[uf][primeiro]["taxa_por_cem_mil"],
                       "variacao_em_pontos": round(serie[uf][ultimo]["taxa_por_cem_mil"]
                                                   - serie[uf][primeiro]["taxa_por_cem_mil"], 2)}
                      for uf in serie), key=lambda x: -x["taxa_no_ultimo_ano"])
    for i, linha in enumerate(ranking, 1):
        linha["posicao"] = i

    caiu = [l for l in ranking if l["variacao_em_pontos"] < 0]
    subiu = [l for l in ranking if l["variacao_em_pontos"] > 0]

    # o Brasil, para o mapa ter referencia; a taxa nacional e a soma sobre a soma, e nunca a
    # media das taxas das UFs, que pesaria o Acre igual a Sao Paulo
    brasil = {}
    for ano in anos_com_taxa:
        m = sum(serie[uf][ano]["mortes"] for uf in serie)
        p = sum(serie[uf][ano]["populacao"] for uf in serie)
        brasil[ano] = {"mortes": m, "populacao": p, "taxa_por_cem_mil": round(100000.0 * m / p, 2)}

    mapa = {}
    for linha in ranking:
        uf = linha["uf"]
        mapa[uf] = {"posicao": linha["posicao"],
                    "taxa_no_ultimo_ano": linha["taxa_no_ultimo_ano"],
                    "variacao_em_pontos": linha["variacao_em_pontos"],
                    "acima_do_brasil_no_ultimo_ano":
                        linha["taxa_no_ultimo_ano"] > brasil[ultimo]["taxa_por_cem_mil"]}

    # a CID-9 fica em serie propria, declarada, e nunca colada na outra
    cid9 = {}
    for uf in sorted(c9):
        cid9[uf] = {ano: numero(c9[uf].get(ano)) for ano in sorted(c9[uf])}

    res = {
        "gerado_por": "apurar_ranking_e_mapa_por_uf.py", "data": "2026-09-22",
        "fonte": ("BRASIL. Ministério da Saúde. DATASUS. Sistema de Informações sobre "
                  "Mortalidade. Óbitos por agressão (CID-10 X85 a Y09) e por intervenção legal "
                  "(Y35 a Y36), por Unidade da Federação. Coletado em 21/09/2026."),
        "identidade_provada_antes_de_usar": {
            "o_que_se_provou": "a soma das agressões com as intervenções legais, no total "
                               "nacional, reproduz a série 328 do Atlas da Violência",
            "anos_conferidos": 29, "de": 1996, "ate": 2024, "divergencias": 0},
        "janela": {"de": primeiro, "ate": ultimo,
                   "por_que_para_aqui": "2025 e 2026 ainda recebem registro no SIM: 2026 traz "
                                        "11.022 óbitos contra 42.590 de 2024"},
        "ano_sem_taxa": {"ano": ANO_SEM_POPULACAO,
                         "motivo": "o DATASUS repete a população de 2022 nas 27 Unidades da "
                                   "Federação, e repetição não é estimativa"},
        "fonte_da_populacao_por_ano": fonte_pop,
        "brasil": brasil,
        "ranking_pela_taxa_no_ultimo_ano": ranking,
        "quantas_caem_e_quantas_sobem": {"caem": len(caiu), "sobem": len(subiu),
                                         "de": primeiro, "ate": ultimo},
        "mediana_da_variacao_em_pontos": round(statistics.median(
            l["variacao_em_pontos"] for l in ranking), 2),
        "mapa_por_uf": mapa,
        "serie_por_uf_cid10": serie,
        "serie_por_uf_cid9_1979_a_1995": cid9,
        "o_que_isto_NAO_diz": [
            "a CID-9, de 1979 a 1995, sai em série própria e NÃO foi emendada à CID-10: a "
            "classificação da causa de morte muda em 1996",
            "o Tocantins só é separado de Goiás a partir de %d, no próprio SIM" % TOCANTINS_SEPARADO_DE,
            "o mapa é descritivo: nenhuma Unidade da Federação é comparada a outra por teste",
            "morte registrada no SIM é óbito por agressão, e não tipo penal: ela não distingue "
            "homicídio doloso de latrocínio nem de lesão seguida de morte"]}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)

    print("janela com taxa: %s a %s | UFs: %d" % (primeiro, ultimo, len(serie)))
    print("Brasil em %s: %s por cem mil; em %s: %s"
          % (primeiro, brasil[primeiro]["taxa_por_cem_mil"], ultimo,
             brasil[ultimo]["taxa_por_cem_mil"]))
    print("caem: %d UFs | sobem: %d UFs | mediana da variacao: %s pontos"
          % (len(caiu), len(subiu), res["mediana_da_variacao_em_pontos"]))
    print()
    print("pos | UF | taxa %s | taxa %s | variacao" % (ultimo, primeiro))
    for l in ranking:
        print("%3d | %s | %8.2f | %8.2f | %+8.2f"
              % (l["posicao"], l["uf"], l["taxa_no_ultimo_ano"],
                 l["taxa_no_primeiro_ano"], l["variacao_em_pontos"]))
    print("gravado:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
