# -*- coding: utf-8 -*-
"""Serie longa de violencia contra a serie de severidade penal (22/09/2026).

Por que existe: o cruzamento de 30/08/2026 usava apenas as Mortes Violentas Intencionais
do Anuario do Forum, de 2012 a 2025, n de catorze. Ha series mais longas no acervo, e elas
NAO se emendam numa so: cada uma conta coisa diferente. Aqui cada serie e apurada
separada, com a definicao e a janela ao lado, e o teste roda uma vez por serie.

Fontes lidas do disco, sem rede:
  Atlas da Violencia (Ipea e FBSP), serie 328 "Homicidios registrados", Brasil
  Atlas da Violencia, serie 20 "Taxa de homicidios registrados", Brasil
  Anuario Brasileiro de Seguranca Publica, MVI do Brasil, pela edicao de 2026
  cp-eventos-de-severidade.csv, eventos que agravam o teto da pena ou criam pena nova

A mudanca de categoria se declara, porque juntar sem declarar falsifica: o Anuario passa a
publicar CVLI na edicao de 2011 e MVI na de 2017; o Sinesp VDE, que alimenta os indicadores
por estado, comeca em 2015; e o homicidio registrado do Atlas vem do SIM do DATASUS, que
nao e a mesma categoria que MVI. Por isso tres linhas, nunca uma.
"""
import collections
import csv
import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(R, "analise-cientifica")
ATLAS = os.path.join(os.environ["USERPROFILE"], "OneDrive", ".claude",
                     "Biblioteca-Academica-Direito", "ipea-atlas-violencia")
SAIDA = os.path.join(A, "serie-longa-violencia.json")
SEMENTE = 20260922
SORTEIOS = 200000
BRASIL = 1076
EDICAO_MVI = "anuario-2026-planilha.xlsx"

sys.path.insert(0, R)
from apurar_incerteza_da_associacao import spearman, intervalo_fisher, p_permutacao


def serie_atlas(sid, regiao):
    """Le uma serie do Atlas no recorte pais e devolve {ano: valor} da regiao pedida."""
    p = os.path.join(ATLAS, "series", "%d-pais.json" % sid)
    if not os.path.exists(p):
        return None
    v = json.load(io.open(p, encoding="utf-8"))
    return {int(x["periodo"][:4]): x["valor"] for x in v if x["regiao_id"] == regiao}


def eventos_por_ano():
    """Conta, por ano, evento que agrava o teto ou cria pena nova. Ano sem evento vale zero."""
    linhas = list(csv.DictReader(io.open(os.path.join(R, "cp-eventos-de-severidade.csv"),
                                         encoding="utf-8"), delimiter=";"))
    return collections.Counter(int(x["ano"]) for x in linhas
                               if x["direcao"] in ("agrava", "cria pena"))


def testar(nome, violencia, eventos, rnd):
    """Spearman do mesmo ano e das DUAS defasagens, que respondem a perguntas opostas.

    A defasagem de 30/08/2026, ja publicada, e violencia[t] contra agravamento[t+1]: a lei
    do ano seguinte respondendo a violencia deste ano. A direcao contraria,
    violencia[t] contra agravamento[t-1], pergunta se a lei do ano anterior precede a
    variacao da violencia. Elas nao sao a mesma medida e por isso saem nomeadas.
    """
    anos = sorted(violencia)
    x = [violencia[a] for a in anos]
    y = [eventos.get(a, 0) for a in anos]
    r = spearman(x, y)
    res = {"serie": nome, "de": anos[0], "ate": anos[-1], "n": len(anos),
           "spearman_mesmo_ano": round(r, 4),
           "p_permutacao_mesmo_ano": p_permutacao(x, y, spearman, rnd, SORTEIOS),
           "ic95_fisher_mesmo_ano": [round(q, 4) for q in intervalo_fisher(r, len(anos))]}
    for rotulo, desloc, recorte in (("lei_responde_a_violencia", +1, anos[:-1]),
                                    ("violencia_apos_a_lei", -1, anos[1:])):
        xd = [violencia[a] for a in recorte]
        yd = [eventos.get(a + desloc, 0) for a in recorte]
        rd = spearman(xd, yd)
        res["defasagem_" + rotulo] = {
            "o_que_compara": ("violencia[t] contra agravamento[t+1]" if desloc > 0
                              else "violencia[t] contra agravamento[t-1]"),
            "n": len(recorte), "spearman": round(rd, 4),
            "p_permutacao": p_permutacao(xd, yd, spearman, rnd, SORTEIOS)}
    # Sem a tendencia. Ela e obrigatoria aqui, e nao zelo: a proporcao de morte violenta por
    # causa indeterminada cai de 120% em 1979 para 14,9% em 2017, ou seja a serie em nivel sobe
    # em parte porque o REGISTRO melhorou. A serie de agravamento tambem sobe ao longo do tempo,
    # e duas series com tendencia comum produzem coeficiente que nao mede relacao nenhuma.
    dx = [x[i + 1] - x[i] for i in range(len(x) - 1)]
    dy = [y[i + 1] - y[i] for i in range(len(y) - 1)]
    rdif = spearman(dx, dy)
    res["primeira_diferenca_sem_tendencia"] = {
        "o_que_compara": "variacao anual da violencia contra variacao anual do agravamento",
        "n": len(dx), "spearman": round(rdif, 4),
        "p_permutacao": p_permutacao(dx, dy, spearman, rnd, SORTEIOS)}
    return res


def main():
    ev = eventos_por_ano()
    rnd = random.Random(SEMENTE)
    series, testes, ausentes = {}, [], []

    contagem = serie_atlas(328, BRASIL)
    if not contagem:
        ausentes.append("Atlas, serie 328: arquivo ausente no disco ou sem a regiao do Brasil")
    else:
        series["atlas_homicidios_registrados"] = {
            "indicador": "Homicidios registrados, numeros absolutos, Brasil",
            "fonte": "Atlas da Violencia, Ipea e Forum Brasileiro de Seguranca Publica, serie 328",
            "fonte_primaria": "Sistema de Informacoes sobre Mortalidade do Ministerio da Saude",
            "o_que_a_categoria_conta": "obito por agressao no registro de mortalidade, "
                                       "e nao o registro policial",
            "por_ano": {str(a): contagem[a] for a in sorted(contagem)}}
        testes.append(testar("Atlas, homicidios registrados", contagem, ev, rnd))

    taxa = serie_atlas(20, BRASIL)
    if not taxa:
        ausentes.append("Atlas, serie 20, taxa de homicidios: a regiao do Brasil nao foi "
                        "identificada no recorte pais desta serie, que traz comparacao "
                        "internacional; a taxa NAO entrou em teste nenhum")
    else:
        series["atlas_taxa_de_homicidios"] = {
            "indicador": "Taxa de homicidios registrados por cem mil habitantes, Brasil",
            "fonte": "Atlas da Violencia, Ipea e Forum, serie 20",
            "por_ano": {str(a): taxa[a] for a in sorted(taxa)}}
        testes.append(testar("Atlas, taxa de homicidios", taxa, ev, rnd))

    mvi_disco = json.load(io.open(os.path.join(A, "mvi-serie-historica.json"), encoding="utf-8"))
    mvi = {int(a): v[EDICAO_MVI] for a, v in mvi_disco["serie"].items() if EDICAO_MVI in v}
    if not mvi:
        ausentes.append("a edicao de 2026 do Anuario nao consta de mvi-serie-historica.json")
    else:
        series["anuario_mvi"] = {
            "indicador": "Mortes Violentas Intencionais, numeros absolutos, Brasil",
            "fonte": "Anuario Brasileiro de Seguranca Publica, 20a edicao, de 2026",
            "o_que_a_categoria_conta": "homicidio doloso, latrocinio, lesao corporal seguida "
                                       "de morte e morte decorrente de intervencao policial",
            "por_ano": {str(a): mvi[a] for a in sorted(mvi)}}
        testes.append(testar("Anuario, MVI", mvi, ev, rnd))

    # Ressalva MEDIDA, e nao apenas citada: Machado (2015, p. 11, nota 14), citando Adorno
    # (1999), registra que o registro de mortalidade cobre cerca de 75% dos casos, com deficit
    # regional e elevada proporcao de causa mal definida. A serie 328 vem desse registro, entao
    # o tamanho dessa zona cinzenta entra aqui medido, para que a leitura da serie longa saiba
    # sobre o que esta pisando. Ela NAO entra em teste: e ressalva, e nao variavel.
    ressalva = {}
    for sid, rotulo in ((78, "mortes_violentas_por_causa_indeterminada"),
                        (95, "proporcao_da_causa_indeterminada_sobre_o_total_de_homicidios")):
        v = serie_atlas(sid, BRASIL)
        if v:
            ressalva[rotulo] = {"fonte": "Atlas da Violencia, serie %d" % sid,
                                "de": min(v), "ate": max(v),
                                "por_ano": {str(a): v[a] for a in sorted(v)}}
        else:
            ausentes.append("Atlas, serie %d (%s): sem a regiao do Brasil no disco" % (sid, rotulo))

    res = {
        "gerado_por": "apurar_serie_longa_violencia.py",
        "data": "2026-09-22",
        "semente": SEMENTE, "sorteios_por_teste": SORTEIOS,
        "serie_de_agravamento": {
            "indicador": "eventos que aumentam o teto da pena ou criam pena nova",
            "fonte": "cp-eventos-de-severidade.csv",
            "criterio": "direcao igual a agrava ou a cria pena; ano sem evento conta zero",
            "de": min(ev), "ate": max(ev)},
        "series_de_violencia": series,
        "testes": testes,
        "mudanca_de_categoria_ao_longo_do_tempo": [
            "o Anuario passa a publicar CVLI na edicao de 2011 e MVI na de 2017; antes disso a "
            "serie publicada e de homicidio doloso, e as tres nao sao intercambiaveis",
            "o Sinesp VDE, fonte dos indicadores por estado, comeca em 2015, e isso foi MEDIDO "
            "na fonte oficial em 22/09/2026, nao suposto: a pagina do Ministerio da Justica "
            "oferece bancovde-2015.xlsx ate bancovde-2026.xlsx, e o mesmo padrao de endereco "
            "responde 404 para cada um dos onze anos de 2004 a 2014, com os anos de controle "
            "de 2015 e 2016 entregando xlsx de verdade (sonda-bancovde-anos-anteriores.json)",
            "o Sinesp JC, implantado em 2004 segundo a propria pagina do Ministerio, NAO tem "
            "serie publicada para baixar em nenhum dos doze enderecos oficiais sondados, e os "
            "dois hosts de dados abertos do Ministerio nao resolvem em DNS "
            "(sonda-sinesp-jc.json). A serie dele so alcanca este trabalho por via indireta, "
            "pelas edicoes antigas do Anuario do Forum, que a reproduzem",
            "o homicidio registrado do Atlas vem do registro de mortalidade da Saude, e o MVI vem "
            "do registro das policias: medem coisas diferentes e nao se somam"],
        "limite_da_fonte_medido_e_nao_apenas_citado": {
            "o_que_a_literatura_lida_declara": "Machado (2015, p. 11, nota 14), citando Adorno "
                "(1999), registra que o registro de mortalidade cobre cerca de 75% dos casos, "
                "com deficit regional e elevada proporcao de causa mal definida",
            "por_que_importa_aqui": "a serie de homicidios registrados do Atlas vem desse mesmo "
                "registro, entao a zona cinzenta entra medida ao lado dela",
            "series": ressalva},
        "o_que_isto_NAO_diz": [
            "nao diz que a lei causou a variacao da violencia, nem o contrario",
            "sem desenho de identificacao, associacao nao vira causa por aumento de n",
            "series de fontes diferentes nao foram emendadas: cada teste roda numa serie so",
            "a morte violenta por causa indeterminada entra como ressalva da fonte, e nunca "
            "como variavel de teste"],
        "nao_medido": ausentes}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)

    for t in testes:
        a, b = t["defasagem_lei_responde_a_violencia"], t["defasagem_violencia_apos_a_lei"]
        d = t["primeira_diferenca_sem_tendencia"]
        print("%-32s n=%2d (%d a %d)\n   nivel        rho=%+.4f p=%.5f\n   lei responde rho=%+.4f "
              "p=%.5f\n   violencia apos rho=%+.4f p=%.5f\n   sem tendencia  rho=%+.4f p=%.5f (n=%d)"
              % (t["serie"], t["n"], t["de"], t["ate"], t["spearman_mesmo_ano"],
                 t["p_permutacao_mesmo_ano"], a["spearman"], a["p_permutacao"],
                 b["spearman"], b["p_permutacao"], d["spearman"], d["p_permutacao"], d["n"]))
    for a in ausentes:
        print("NAO MEDIDO:", a)
    print("gravado:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
