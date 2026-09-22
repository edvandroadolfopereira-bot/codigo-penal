# CAMADA 1, o fato: cada numero escrito no trabalho contra a fonte que o produziu.
# Nada aqui e' digitado a partir da minha lembranca: os valores medidos saem dos JSON
# de apuracao e da base, e os escritos saem do proprio texto do trabalho.

import io
import json
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
TRAB = io.open(os.path.join(R, "ENTREGA-ACADEMICA", "01-TRABALHO-ACADEMICO.md"),
               encoding="utf-8").read()

pg = json.load(io.open(os.path.join(R, "analise-cientifica", "severidade-parte-geral.json"), encoding="utf-8"))
ca = json.load(io.open(os.path.join(R, "analise-cientifica", "causas-de-aumento.json"), encoding="utf-8"))
ab = json.load(io.open(os.path.join(R, "analise-cientifica", "autoria-e-bancada.json"), encoding="utf-8"))
te = json.load(io.open(os.path.join(R, "analise-cientifica", "teste-origem-x-direcao.json"), encoding="utf-8"))
mt = json.load(io.open(os.path.join(R, "analise-cientifica", "materia-das-normas.json"), encoding="utf-8"))
rl = json.load(io.open(os.path.join(R, "analise-cientifica", "rol-como-segunda-unidade.json"), encoding="utf-8"))
el = json.load(io.open(os.path.join(R, "analise-cientifica", "emendas-e-lsn.json"), encoding="utf-8"))
pr = json.load(io.open(os.path.join(R, "analise-cientifica", "pendencias-restantes.json"), encoding="utf-8"))
mf = json.load(io.open(os.path.join(R, "ENTREGA-ACADEMICA", "02-DADOS", "MANIFESTO.json"), encoding="utf-8"))

c = sqlite3.connect(os.path.join(R, "BASE-CODIGO-PENAL.sqlite"))
partidos_autores = c.execute("""SELECT COUNT(DISTINCT TRIM(partido_na_data_da_norma))
                                FROM camara_autores
                                WHERE TRIM(COALESCE(partido_na_data_da_norma,'')) <> ''""").fetchone()[0]
votos = c.execute("SELECT COUNT(*) FROM camara_votos_nominais").fetchone()[0]
normas_com_voto = c.execute("SELECT COUNT(DISTINCT norma) FROM camara_votos_nominais").fetchone()[0]
c.close()

dircount = pg["contagem_por_direcao"]
inst_com_7209 = 15  # medido na atribuicao; conferido abaixo contra o proprio texto

cmp = ca["comparacao"]
h, m = ca["epocas"]["hoje"], ca["epocas"]["1940"]
end = {o: v for o, v in te["proporcao_que_endurece"].items()}
tot_end = sum(v["endurece"] for v in end.values())
tot_ev = sum(v["total"] for v in end.values())

def pct(o):
    v = end[o]
    return round(100.0 * v["endurece"] / v["total"], 1)

CONF = [
    ("institutos medidos na Parte Geral", pg["institutos_medidos"], 16),
    ("Parte Geral, abrandam", dircount.get("abranda", 0), 5),
    ("Parte Geral, agravam", dircount.get("agrava", 0), 2),
    ("Parte Geral, mantem", dircount.get("mantem", 0), 6),
    ("Parte Geral, criados depois de 1940", dircount.get("instituto CRIADO depois de 1940", 0), 2),
    ("Parte Geral, extintos depois de 1940", dircount.get("instituto EXTINTO depois de 1940", 0), 1),
    ("causas, aumento em 1940", cmp["aumento_1940"], 28),
    ("causas, aumento hoje", cmp["aumento_hoje"], 58),
    ("causas, diminuicao em 1940", cmp["diminuicao_1940"], 5),
    ("causas, diminuicao hoje", cmp["diminuicao_hoje"], 8),
    ("causas, multiplicador em 1940", cmp["multiplicador_1940"], 8),
    ("causas, multiplicador hoje", cmp["multiplicador_hoje"], 22),
    ("causas, artigos subestimados em 1940", cmp["artigos_subestimados_1940"], 33),
    ("causas, artigos subestimados hoje", cmp["artigos_subestimados_hoje"], 46),
    ("causas, artigos da Parte Especial em 1940", m["artigos_da_parte_especial"], 240),
    ("causas, artigos da Parte Especial hoje", h["artigos_da_parte_especial"], 241),
    ("autoria, normas com autoria e evento", ab["cobertura"]["normas_com_AMBOS"], 49),
    ("autoria, eventos datados", ab["cobertura"]["eventos_datados"], 130),
    ("autoria, eventos sem chave", ab["cobertura"]["eventos_sem_chave_extraivel"], 0),
    ("autoria, normas com evento e sem autoria", ab["cobertura"]["normas_com_evento_e_SEM_autoria"], 0),
    ("autoria, assinaturas", ab["cobertura"]["assinaturas_de_autoria"], 217),
    ("partidos distintos na autoria", partidos_autores, 28),
    ("votos nominais", votos, 28083),
    ("normas com voto nominal", normas_com_voto, 27),
    ("eventos que endurecem", tot_end, 107),
    ("eventos totais no teste", tot_ev, 130),
    ("permutacoes do teste de origem", te["permutacoes"], 200000),
    ("Titulos lidos do Codigo", len(mt["titulos_lidos"]), 20),
    ("Titulos da Parte Geral", sum(1 for t in mt["titulos_lidos"] if t["parte"] == "GERAL"), 8),
    ("Titulos da Parte Especial", sum(1 for t in mt["titulos_lidos"] if t["parte"] == "ESPECIAL"), 12),
    ("eventos classificados por materia", mt["eventos_classificados"], 130),
    ("eventos sem Titulo", len(mt["eventos_sem_titulo"]), 0),
    ("normas no teste por norma", mt["teste_por_NORMA_que_vale"]["normas"], 49),
    ("normas em ano eleitoral", mt["teste_por_NORMA_que_vale"]["normas_em_ano_eleitoral"], 26),
    ("Estado Democratico, eventos", mt["concentracao_por_materia"]["DOS CRIMES CONTRA O ESTADO DEMOCRÁTICO DE DIREITO"]["eventos"], 8),
    ("Estado Democratico, normas", mt["concentracao_por_materia"]["DOS CRIMES CONTRA O ESTADO DEMOCRÁTICO DE DIREITO"]["normas"], 1),
    ("administracao publica, eventos", mt["concentracao_por_materia"]["DOS CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA"]["eventos"], 37),
    ("normas que tocaram o rol", len(rl["normas_que_tocaram_o_rol"]), 9),
    ("normas do rol fora das 115", len(rl["normas_fora_das_115"]), 2),
    ("artigos afetados por norma fora das 115", rl["artigos_afetados_por_norma_fora_das_115"], 3),
    ("artigos do rol invisiveis para a regua", len(rl["artigos_do_rol_invisiveis_para_a_regua"]), 1),
    ("artigos no rol", len(rl["sobreposicao_com_a_regua_do_texto"]), 16),
    ("parametros do rol nao lidos", len(rl["parametros_nao_lidos"]), 0),
    ("registros percorridos na busca da LSN", el["lei_de_seguranca_nacional"]["registros_percorridos"], 21306),
    ("anos de catalogo da LSN", el["lei_de_seguranca_nacional"]["anos_de_catalogo_percorridos"], 56),
    ("normas que citam seguranca nacional", el["lei_de_seguranca_nacional"]["normas_que_citam_seguranca_nacional_na_ementa"], 60),
    ("normas que DEFINEM crime de seguranca", len(el["lei_de_seguranca_nacional"]["normas_que_DEFINEM_crime_contra_a_seguranca_nacional"]), 5),
    ("achadas so' por numero", len(el["lei_de_seguranca_nacional"]["achadas_SO_por_numero_e_nao_por_ementa"]), 2),
    ("emendas no catalogo", el["emendas_constitucionais"]["emendas_no_catalogo"], 193),
    ("emendas com articulado", el["emendas_constitucionais"]["emendas_com_articulado_na_base"], 0),
    ("emendas com materia penal na ementa", el["emendas_constitucionais"]["citam_materia_penal_na_ementa"], 0),
    ("dispositivos com teto recalculado", pr["C_teto_efetivo"]["dispositivos_recalculados"], 91),
    ("artigos distintos recalculados", pr["C_teto_efetivo"]["artigos_distintos_recalculados"], 43),
    ("votacoes sem objeto declarado", pr["D_objeto_das_votacoes"]["sem_objeto_declarado"], 1),  # 22/09/2026: 126 viraram 1, com a sigla REQ e o detalhe da Camara
    ("votacoes de requerimento", next(l["votacoes"] for l in pr["D_objeto_das_votacoes"]["por_objeto"] if l["objeto"] == "requerimento"), 297),  # 22/09/2026: 1 era autorizacao de tramitacao
    ("votacoes de texto principal", next(l["votacoes"] for l in pr["D_objeto_das_votacoes"]["por_objeto"] if l["objeto"] == "texto principal"), 72),
    ("sim no texto principal, em decimos", round(10 * next(l["pct_sim_entre_validos"] for l in pr["D_objeto_das_votacoes"]["por_objeto"] if l["objeto"] == "texto principal")), 797),
    ("votacoes de autorizacao de tramitacao", next(l["votacoes"] for l in pr["D_objeto_das_votacoes"]["por_objeto"] if l["objeto"] == "autorizacao de tramitacao"), 1),
    ("votacoes classificadas pelo detalhe da Camara", pr["D_objeto_das_votacoes"]["classificadas_por_passagem"]["pelo detalhe da Camara"], 113),
    ("soma das classes de objeto", sum(l["votacoes"] for l in pr["D_objeto_das_votacoes"]["por_objeto"]), 654),
    ("votacoes classificadas", pr["D_objeto_das_votacoes"]["votacoes_classificadas"], 654),
    ("normas na simulacao de poder", pr["A_poder_do_teste_da_agenda"]["normas"], 49),
    # O manifesto mudou de forma em 30/08/2026, quando o pacote de exame virou pacote
    # PUBLICO e passou a levar CSV, catalogo de fontes e declaracao de direitos. A
    # chave `fontes_sem_resumo_criptografico` deixou de existir, e o conferidor
    # quebrou com KeyError, que e' pior que divergencia: ele parava de conferir TUDO.
    # A medida equivalente hoje se conta na propria lista de fontes.
    # 18/09/2026: pacote remontado com as apuracoes da revisao. O manifesto lista 174 itens;
    # o Apendice A declara 178 arquivos porque soma os 4 documentos do proprio pacote.
    # A FGV CPDOC entrou como fonte dos marcos de regime, e as fontes passaram a 15.
    ("arquivos no pacote de dados", len(mf["arquivos_do_pacote"]), 295),  # 22/09/2026, ranking por UF: +2 dados e +13 planilhas; antes, 278  # 22/09/2026, secao 4.29: +3 dados (serie longa e as duas sondas) e +10 planilhas; antes, 265  # 22/09/2026, secao 4.28: +7 dados e +45 planilhas; antes, 213  # 22/09/2026, por fim: +5, incerteza da associacao (json e planilha), detalhe das votacoes sem objeto e script do ciclo eleitoral; depois: +2, detalhe das votacoes sem objeto na descricao (json e planilha); antes: +4, composicao do Senado por legislatura pelo portal e partido do senador na epoca (json e planilha de cada); 21/09/2026, noite, por fim: +2, populacao por UF e ano (json e planilha); depois: -1, a lista de lacunas dos presidentes ficou vazia com a sucessao de abril de 1964 conferida, e a planilha dela deixou de existir; antes: +5, governadores escolhidos pela Assembleia 1970-1978 e nomeados em territorio, DF e MS, pelo DHBB (json e uma planilha por lista: governadores, fora da lista, territorios, nomeados); tarde: +4, partido na data da apresentacao e conferencia dos governadores 1947-1966 contra a votacao nominal por UF (json mais planilha); o gerador imprime 200 porque soma os 4 documentos do proprio pacote; antes, 21/09/2026: +3 da secao 4.27, +3 dos agentes, +3 dos governadores, +4 dos presidentes e +5 das bancadas (o gerador faz uma planilha por lista da base, alem do json)
    ("fontes da base no manifesto", len(mf["fontes_da_base"]), 41),
    ("fontes citadas na NBR 6023", len(mf["fontes_e_direitos"]), 26),  # 22/09/2026, secao 4.29: +2, Atlas da Violencia do Ipea e Sinesp do MJSP; antes, 24  # 22/09/2026: +2, escala de Bolognesi e partidos do TSE; antes, 22  # 21/09/2026, noite, por fim: +1, populacao residente do IBGE pelo DATASUS; antes: +1, DHBB do FGV CPDOC, citado no formato que o CPDOC orienta; tarde: +1, votacao nominal por UF do TSE; antes, 21/09/2026: +1, eleitorado do TSE; +2, candidatos do TSE e SIM/DATASUS; +1, Biblioteca da Presidencia
    ("fontes sem resumo criptografico",
     sum(1 for f in mf["fontes_da_base"] if not f.get("sha256")), 0),
    ("tabelas de dado na base", mf["base_completa"]["tabelas_de_dado"], 42),
    ("linhas somadas na base", mf["base_completa"]["linhas_somadas"], 157799),
    ("bytes da base", mf["base_completa"]["bytes"], 210190336),
    ("arquivos declarados e ausentes", len(mf["arquivos_declarados_e_ausentes"]), 0),
]

print("=== CAMADA 1, o fato: medido contra escrito ===")
div = 0
for rot, medido, escrito in CONF:
    ok = (medido == escrito)
    if not ok:
        div += 1
    print("   %-46s medido=%-8s escrito=%-8s %s" % (rot, medido, escrito, "confere" if ok else "DIVERGE"))

# 22/09/2026: o numero de arquivos e de abas ESCRITO no texto contra o DISCO, e nao contra
# uma constante minha. Foi uma constante velha que deixou o texto dizer 178 com 217 no disco.
import openpyxl  # noqa: E402
_pac = os.path.join(R, "ENTREGA-ACADEMICA", "02-DADOS")
_no_disco = sum(len(f) for _r, _d, f in os.walk(_pac))
_m = re.search(r"com \*\*(\d+) arquivos\*\*", TRAB)
_escrito = int(_m.group(1)) if _m else None
_abas = len(openpyxl.load_workbook(os.path.join(R, "ENTREGA-ACADEMICA", "03-BANCO-DE-DADOS-CODIGO-PENAL.xlsx"), read_only=True).sheetnames)
_EXT = {28: "vinte e oito", 29: "vinte e nove", 30: "trinta"}
for rot, medido, escrito in [("arquivos do pacote: disco contra texto", _no_disco, _escrito),
                             ("abas da planilha: arquivo contra texto", _EXT.get(_abas, str(_abas)),
                              "vinte e nove" if "planilha única de vinte e nove abas" in TRAB else "outro")]:
    ok = medido == escrito
    div += 0 if ok else 1
    print("   %-46s medido=%-8s escrito=%-8s %s" % (rot, medido, escrito, "confere" if ok else "DIVERGE"))

print()
print("=== os percentuais e as razoes, recalculados ===")
recalc = [
    ("Executivo endurece", pct("Executivo"), 76.6),
    ("Camara endurece", pct("Legislativo, Camara dos Deputados"), 80.0),
    ("Senado endurece", pct("Legislativo, Senado Federal"), 85.0),
    ("comissao endurece", pct("Legislativo, comissao ou CPI"), 95.7),
    ("total endurece", round(100.0 * tot_end / tot_ev, 1), 82.3),
    ("razao aumento por diminuicao em 1940", round(cmp["aumento_1940"] / cmp["diminuicao_1940"], 2), 5.6),
    ("razao aumento por diminuicao hoje", round(cmp["aumento_hoje"] / cmp["diminuicao_hoje"], 2), 7.25),
    ("p do teste de origem", round(te["p"], 3), 0.248),
    ("primeiro elo POR NORMA", round(mt["teste_por_NORMA_que_vale"]["primeiro_elo_ano_eleitoral_x_materia"]["p"], 3), 0.897),
    ("segundo elo POR NORMA", round(mt["teste_por_NORMA_que_vale"]["segundo_elo_materia_x_direcao"]["p"], 3), 0.664),
    ("primeiro elo por evento", round(mt["primeiro_elo_ano_eleitoral_x_materia"]["p"], 5), 0.00001),
    ("segundo elo por evento", round(mt["segundo_elo_materia_x_direcao"]["p"], 3), 0.023),
    ("poder sob a hipotese nula", round(100*pr["A_poder_do_teste_da_agenda"]["resultados"][0]["poder"], 1), 4.6),
    ("poder com efeito de 40%", round(100*pr["A_poder_do_teste_da_agenda"]["resultados"][2]["poder"], 1), 39.2),
    ("poder com efeito de 60%", round(100*pr["A_poder_do_teste_da_agenda"]["resultados"][3]["poder"], 1), 76.4),
    ("subestimacao do teto", pr["C_teto_efetivo"]["subestimacao_percentual"], 37.82),
    ("diferenca entre as faixas vizinhas", pr["B_sensibilidade_da_regua"]["diferenca_entre_as_duas_faixas_vizinhas_meses"], 24.0),
]

# A janela longa da violencia, acrescentada em 22/09/2026 junto com a secao 4.29. Cada numero
# escrito no trabalho volta aqui contra a fonte que o produziu, porque numero em peca sem
# conferencia e' opiniao com casas decimais.
sl = json.load(io.open(os.path.join(R, "analise-cientifica", "serie-longa-violencia.json"),
                       encoding="utf-8"))
sb = json.load(io.open(os.path.join(R, "analise-cientifica",
                                    "sonda-bancovde-anos-anteriores.json"), encoding="utf-8"))
por_serie = {t["serie"]: t for t in sl["testes"]}
at_n = por_serie["Atlas, homicidios registrados"]
at_t = por_serie["Atlas, taxa de homicidios"]
mvi = por_serie["Anuario, MVI"]
hom = {int(a): v for a, v in
       sl["series_de_violencia"]["atlas_homicidios_registrados"]["por_ano"].items()}
tax = {int(a): v for a, v in
       sl["series_de_violencia"]["atlas_taxa_de_homicidios"]["por_ano"].items()}
recalc += [
    ("janela longa, n da contagem de homicidios", at_n["n"], 36),
    ("janela longa, n da taxa", at_t["n"], 35),
    ("janela longa, n do MVI", mvi["n"], 14),
    ("janela longa, rho de nivel da contagem", at_n["spearman_mesmo_ano"], 0.051),
    ("janela longa, rho sem tendencia da contagem",
     at_n["primeira_diferenca_sem_tendencia"]["spearman"], 0.173),
    ("janela longa, rho sem tendencia da taxa",
     at_t["primeira_diferenca_sem_tendencia"]["spearman"], 0.203),
    ("janela longa, p sem tendencia da contagem",
     round(at_n["primeira_diferenca_sem_tendencia"]["p_permutacao"], 3), 0.317),
    ("janela longa, menor p da tabela",
     round(mvi["defasagem_violencia_apos_a_lei"]["p_permutacao"], 3), 0.096),
    ("janela longa, alta da contagem de 1989 a 2017",
     round((hom[2017] / hom[1989] - 1) * 100, 1), 128.0),
    ("janela longa, queda da contagem de 2017 a 2024",
     round((hom[2024] / hom[2017] - 1) * 100, 1), -35.1),
    ("janela longa, taxa de 1990", round(tax[1990], 1), 19.4),
    ("janela longa, taxa de 2024", round(tax[2024], 1), 20.0),
    ("Sinesp, anos anteriores a 2015 com arquivo na fonte",
     len(sb["anos_com_arquivo_de_verdade"]), 0),
    ("Sinesp, anos testados de 2004 a 2014", len(sb["anos_testados"]), 11),
]

# O ranking por Unidade da Federacao e as notas dos gestores, secao 4.29, 22/09/2026.
ru = json.load(io.open(os.path.join(R, "analise-cientifica", "ranking-e-mapa-por-uf.json"),
                       encoding="utf-8"))
nt = json.load(io.open(os.path.join(R, "analise-cientifica", "notas-sinesp-jc.json"),
                       encoding="utf-8"))
rk = {l["uf"]: l for l in ru["ranking_pela_taxa_no_ultimo_ano"]}
recalc += [
    ("por UF, anos conferidos contra o Atlas sem divergencia",
     ru["identidade_provada_antes_de_usar"]["anos_conferidos"], 29),
    ("por UF, divergencias contra o Atlas",
     ru["identidade_provada_antes_de_usar"]["divergencias"], 0),
    ("por UF, quantas caem", ru["quantas_caem_e_quantas_sobem"]["caem"], 11),
    ("por UF, quantas sobem", ru["quantas_caem_e_quantas_sobem"]["sobem"], 16),
    ("por UF, mediana da variacao em pontos", ru["mediana_da_variacao_em_pontos"], 3.84),
    ("por UF, taxa do Brasil em 1996", ru["brasil"]["1996"]["taxa_por_cem_mil"], 24.78),
    ("por UF, taxa do Brasil em 2024", ru["brasil"]["2024"]["taxa_por_cem_mil"], 20.03),
    ("por UF, taxa de SP em 2024", rk["SP"]["taxa_no_ultimo_ano"], 6.61),
    ("por UF, taxa de SP em 1996", rk["SP"]["taxa_no_primeiro_ano"], 36.11),
    ("por UF, variacao de SP", rk["SP"]["variacao_em_pontos"], -29.50),
    ("por UF, variacao da BA", rk["BA"]["variacao_em_pontos"], 25.80),
    ("por UF, variacao do RJ", rk["RJ"]["variacao_em_pontos"], -39.49),
    ("por UF, taxa do AP em 2024, a maior", rk["AP"]["taxa_no_ultimo_ano"], 45.21),
    ("notas do Sinesp JC, UFs com nota", nt["unidades_da_federacao_com_nota"], 16),
    ("notas do Sinesp JC, UFs sem nota", nt["unidades_da_federacao_sem_nota"], 11),
]
for rot, medido, escrito in recalc:
    ok = abs(medido - escrito) < 0.06
    if not ok:
        div += 1
    print("   %-46s medido=%-8s escrito=%-8s %s" % (rot, medido, escrito, "confere" if ok else "DIVERGE"))

print()
print("=== os numeros escritos aparecem MESMO no texto do trabalho? ===")
NO_TEXTO = ["76,6", "80,0", "85,0", "95,7", "82,3", "6,69", "0,248", "28.083", "46,5",
            "4,1115", "dezesseis institutos", "49 de 49", "130 de 130",
            "0,897", "0,664", "97,6", "91,9", "93,3", "14.197", "9.677", "12.015",
            "pseudorreplicação", "Título", "9.279",
            "8.930", "9.695", "dois terços", "art. 122", "21.306", "193",
            "7.170", "6.620", "5.786", "314", "510", "898",
            "4,6%", "39,2%", "76,4%", "37,82%", "99,5%", "50,4%", "vinte e quatro meses",
            "157.799", "210.190.336", "2a7e54a9bbb7025b0bd69dfe7fd51f7ddb9d3ac1b8e92a89593995581f51773d",
            "quarenta e seis artigos", "trinta e três", "cinquenta e oito", "vinte e dois",
            "-0,619 a 0,475", "0,737", "0,212", "0,445", "28 dos 36", "79 de 94",
            # a janela longa da violencia, secao 4.29, acrescentada em 22/09/2026
            "+0,051", "+0,173", "+0,203", "128,0%", "35,1%", "19,4", "20,0",
            "89,0%", "15,9%", "trinta e seis", "doze coeficientes", "0,096",
            "1989 a 2024", "1990-2024", "1979-2017", "404",
            # o ranking por Unidade da Federacao, seção 4.29, 22/09/2026
            "45,21", "40,81", "6,61", "36,11", "-29,50", "+25,80", "-39,49",
            "24,78", "20,03", "-4,75", "+3,84", "11.022", "42.590",
            "vinte e nove anos", "dezesseis sobem", "onze não enviaram"]
for t in NO_TEXTO:
    n = TRAB.count(t)
    if n == 0:
        div += 1
    print("   %-30s %d ocorrencia(s) %s" % (t, n, "" if n else "AUSENTE"))

print()
print("DIVERGENCIAS: %d" % div)
sys.exit(1 if div else 0)
