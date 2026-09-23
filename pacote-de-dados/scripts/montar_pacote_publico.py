# -*- coding: utf-8 -*-
# MONTA O PACOTE DE DADOS PARA DISPONIBILIZACAO PUBLICA.
#
# Ele substitui `montar_pacote_de_dados.py`, que montava o pacote de exame. A diferenca
# nao e' de tamanho, e' de destino: aquele ia com a entrega, este vai ao publico, e por
# isso tem que resolver tres coisas a mais.
#
# 1. FORMATO ABERTO. Dado em JSON serve a quem programa. Quem abre planilha precisa de
#    CSV, e por isso toda tabela sai TAMBEM em CSV, com ponto e virgula e cabecalho.
#
# 2. CITACAO DE CADA FONTE, na ABNT NBR 6023. Publicar dado derivado de terceiro sem a
#    referencia da origem e' apropriacao, ainda que involuntaria. Cada arquivo do pacote
#    aponta a fonte de onde veio o dado que ele resume.
#
# 3. DIREITOS, e este e' o ponto que quase passou. MEDIDO em 30/08/2026 na base: dos
#    13.448 itens da Biblioteca Digital da Justica Eleitoral, 7.278 declaram licenca
#    Creative Commons, e a maioria e' NaoComercial ou SemDerivacoes, o que RESTRINGE
#    redistribuicao. Por isso este pacote NAO redistribui obra de terceiro: ele leva a
#    apuracao propria e a referencia de onde ela saiu.
#
# O QUE E' DE DOMINIO PUBLICO, e por isso entra sem restricao: texto de lei, decisao
# judicial e ato oficial, pelo art. 8, inciso IV, da Lei n. 9.610, de 1998, que os
# exclui da protecao autoral.

import collections
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

# a partir de quantos itens uma lista de valores simples merece planilha propria
LISTA_LONGA = 20

R = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(R, "ENTREGA-ACADEMICA", "02-DADOS")
BASE = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")

# Cada fonte traz a referencia na NBR 6023 e o regime de direito, para que quem use o
# pacote saiba citar e saiba o que pode redistribuir.
FONTES = [
    {"sigla": "planalto",
     "referencia": ("BRASIL. Presidência da República. Casa Civil. Legislação. Brasília, DF. "
                    "Disponível em: https://www.planalto.gov.br/ccivil_03/. Acesso em: 30 ago. 2026."),
     "regime": "domínio público, art. 8º, IV, da Lei n. 9.610/1998, texto de lei"},
    {"sigla": "camara-legin",
     "referencia": ("BRASIL. Câmara dos Deputados. Legislação Informatizada. Brasília, DF. "
                    "Disponível em: https://www2.camara.leg.br/legin. Acesso em: 30 ago. 2026."),
     "regime": "domínio público, texto de lei e ficha de publicação oficial"},
    {"sigla": "camara-dados-abertos",
     "referencia": ("BRASIL. Câmara dos Deputados. Dados Abertos. Brasília, DF. "
                    "Disponível em: https://dadosabertos.camara.leg.br. Acesso em: 30 ago. 2026."),
     "regime": "dado público, Lei n. 12.527/2011"},
    {"sigla": "senado-dados-abertos",
     "referencia": ("BRASIL. Senado Federal. Dados Abertos. Brasília, DF. "
                    "Disponível em: https://legis.senado.leg.br/dadosabertos. Acesso em: 30 ago. 2026."),
     "regime": "dado público, Lei n. 12.527/2011"},
    {"sigla": "normas-leg",
     "referencia": ("BRASIL. Senado Federal; Câmara dos Deputados; Congresso Nacional. "
                    "Normas.leg.br: portal da legislação federal. Brasília, DF. "
                    "Disponível em: https://normas.leg.br. Acesso em: 30 ago. 2026."),
     "regime": "domínio público, texto de lei"},
    {"sigla": "tse-cronologia",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Cronologia das eleições. Brasília, DF. "
                    "Disponível em: https://www.tse.jus.br/eleicoes/eleicoes-anteriores/eleicoes-anteriores. "
                   "Acesso em: 30 ago. 2026."),
     "regime": "dado público de ato oficial"},
    {"sigla": "tse-eleitorado",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Estatísticas do eleitorado: perfil do "
                    "eleitorado, posição de 1º set. 2026. Brasília, DF. Disponível em: "
                    "https://dadosabertos.tse.jus.br. Acesso em: 21 set. 2026."),
     "regime": "dado público agregado por Unidade da Federação, sem dado pessoal"},
    {"sigla": "escala-bolognesi",
     "referencia": ("BOLOGNESI, Bruno; RIBEIRO, Ednaldo; CODATO, Adriano. Uma nova classificação ideológica "
                    "dos partidos políticos brasileiros. Dados, v. 66, n. 2, e20210164, 2023; e BOLOGNESI, Bruno "
                    "et al. O desaparecimento do centro ideológico no sistema partidário brasileiro. Opinião "
                    "Pública, v. 31, e31120, 2025. Disponível em: https://www.scielo.br. Acesso em: 22 set. 2026."),
     "regime": "artigo científico de acesso aberto; do artigo se usa só a média publicada de cada partido"},
    {"sigla": "tse-partidos",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Partidos registrados no TSE e registros de partidos "
                    "políticos de 1945 a 1979. Brasília, DF. Disponível em: https://www.tse.jus.br/partidos. "
                    "Acesso em: 22 set. 2026."),
     "regime": "documento público de registro partidário; o pacote leva só a contagem, e não os documentos"},
    {"sigla": "tse-candidatos",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Candidatos: consulta de candidatos, eleições de 1994 "
                    "a 2022. Brasília, DF. Disponível em: https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/. "
                    "Acesso em: 21 set. 2026."),
     "regime": "dado público de ato oficial; só nome, partido e turno do eleito; CPF e demais dados pessoais não lidos"},
    {"sigla": "tse-votacao-uf",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Resultados: votação nominal por unidade da federação, "
                    "eleições de 1945 a 1990. Brasília, DF. Disponível em: https://dadosabertos.tse.jus.br/dataset/?q=resultados. "
                    "Acesso em: 21 set. 2026."),
     "regime": "dado público de ato oficial; nome, partido, votos e situação do candidato, sem CPF nem dado pessoal"},
    {"sigla": "datasus-sim",
     "referencia": ("BRASIL. Ministério da Saúde. Departamento de Informática do Sistema Único de Saúde. "
                    "Sistema de Informações sobre Mortalidade (SIM): óbitos por causas externas, por Unidade da "
                    "Federação, 1979 a 2026. Brasília, DF. Disponível em: "
                    "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sim/cnv/ext10uf.def. Acesso em: 21 set. 2026."),
     "regime": "dado público agregado por Unidade da Federação e ano, sem dado pessoal"},
    {"sigla": "ipea-atlas",
     "referencia": ("INSTITUTO DE PESQUISA ECONÔMICA APLICADA; FÓRUM BRASILEIRO DE SEGURANÇA "
                    "PÚBLICA. Atlas da violência: séries de homicídios registrados, taxa por "
                    "cem mil habitantes e morte violenta por causa indeterminada, Brasil, 1979 "
                    "a 2024. Brasília, DF: Ipea, 2026. Disponível em: "
                    "https://www.ipea.gov.br/atlasviolencia/. Acesso em: 22 set. 2026."),
     "regime": ("série agregada nacional por ano, sem dado pessoal. O Atlas é coproduzido pelo "
                "mesmo Fórum que publica o Anuário, e por isso as duas não são fontes "
                "institucionalmente independentes: o que difere entre elas é a base primária")},
    {"sigla": "mjsp-sinesp",
     "referencia": ("BRASIL. Ministério da Justiça e Segurança Pública. Dados Nacionais de "
                    "Segurança Pública: Sinesp VDE. Brasília, DF. Disponível em: "
                    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/"
                    "estatistica. Acesso em: 22 set. 2026."),
     "regime": ("dado público agregado. O pacote leva o registro da sondagem da fonte, e não "
                "os bancos do Sinesp VDE, que são redistribuídos pelo próprio Ministério")},
    {"sigla": "biblioteca-pr",
     "referencia": ("BRASIL. Presidência da República. Biblioteca da Presidência. Ex-presidentes. Brasília, DF. "
                    "Disponível em: http://www.biblioteca.presidencia.gov.br/presidencia/ex-presidentes. Acesso em: 21 set. 2026."),
     "regime": "dado público de ato oficial"},
    {"sigla": "tse-bdje",
     "referencia": ("BRASIL. Tribunal Superior Eleitoral. Biblioteca Digital da Justiça "
                    "Eleitoral. Brasília, DF. Disponível em: https://bibliotecadigital.tse.jus.br. "
                    "Acesso em: 30 ago. 2026."),
     "regime": ("ATENÇÃO: 7.278 dos 13.448 itens declaram licença Creative Commons, a maioria "
                "NãoComercial ou SemDerivações. Este pacote NÃO redistribui o acervo: leva "
                "apenas o catálogo de metadados e a apuração própria")},
    {"sigla": "cnj-datajud",
     "referencia": ("BRASIL. Conselho Nacional de Justiça. DataJud: base nacional de dados do "
                    "Poder Judiciário. Brasília, DF. Disponível em: https://www.cnj.jus.br. "
                    "Acesso em: 30 ago. 2026."),
     "regime": "dado público, Resolução CNJ n. 331/2020"},
    {"sigla": "stf",
     "referencia": ("BRASIL. Supremo Tribunal Federal. Jurisprudência. Brasília, DF. "
                    "Disponível em: https://portal.stf.jus.br. Acesso em: 30 ago. 2026."),
     "regime": "domínio público, art. 8º, IV, da Lei n. 9.610/1998, decisão judicial"},
    {"sigla": "stj",
     "referencia": ("BRASIL. Superior Tribunal de Justiça. Precedentes qualificados e súmulas. "
                    "Brasília, DF. Disponível em: https://www.stj.jus.br. Acesso em: 30 ago. 2026."),
     "regime": "domínio público, decisão judicial"},
    {"sigla": "fbsp",
     "referencia": ("FÓRUM BRASILEIRO DE SEGURANÇA PÚBLICA. Anuário Brasileiro de Segurança "
                    "Pública. São Paulo: FBSP, 2007-2026. Disponível em: "
                    "https://forumseguranca.org.br. Acesso em: 30 ago. 2026."),
     "regime": ("obra de entidade privada. Este pacote NÃO redistribui os relatórios: leva a "
                "série extraída, com a edição de origem declarada em cada valor")},
    {"sigla": "fbsp-percepcao",
     "referencia": ("FÓRUM BRASILEIRO DE SEGURANÇA PÚBLICA. Violência e democracia: panorama "
                    "brasileiro pré-eleições 2022. São Paulo: FBSP, 2022. Disponível em: "
                    "https://forumseguranca.org.br. Acesso em: 30 ago. 2026."),
     "regime": "obra de entidade privada, citada e não redistribuída"},
    {"sigla": "fgv-cpdoc",
     "referencia": ("FUNDAÇÃO GETULIO VARGAS. Centro de Pesquisa e Documentação de História "
                    "Contemporânea do Brasil. Rio de Janeiro: FGV CPDOC. Disponível em: "
                    "https://cpdoc.fgv.br. Acesso em: 18 set. 2026."),
     "regime": "obra de entidade privada, citada e não redistribuída; dela saem só as datas dos marcos de regime"},
    {"sigla": "pop-uf",
     "referencia": ("INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. População residente por Unidade da Federação, 1980 a 2012 e 2022: "
                    "censos, contagem de 1996 e estimativas. Brasília, DF: Ministério da Saúde, DATASUS, 2026. Disponível em: "
                    "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?ibge/cnv/popuf.def. Acesso em: 21 set. 2026."),
     "regime": "dado público agregado por Unidade da Federação e ano, sem dado pessoal"},
    {"sigla": "cpdoc-dhbb",
     "referencia": ("CENTRO DE PESQUISA E DOCUMENTAÇÃO DE HISTÓRIA CONTEMPORÂNEA DO BRASIL. Dicionário Histórico-Biográfico "
                    "Brasileiro. Rio de Janeiro: FGV CPDOC, [2025]. Disponível em: https://cpdoc.fgv.br/acervo/dicionarios/dhbb. "
                    "Corpus aberto, versão de 1º abr. 2025, disponível em: https://github.com/cpdoc/dhbb. Acesso em: 21 set. 2026."),
     "regime": "obra do FGV CPDOC sob licença CC BY-NC 4.0, citada no formato que o próprio CPDOC orienta; dela saem só o nome, a UF e o ano do cargo de cada governador, com o número do verbete, nunca o texto"},
    {"sigla": "abnt",
     "referencia": ("ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 14724: informação e "
                    "documentação: trabalhos acadêmicos: apresentação. 4. ed. Rio de Janeiro: "
                    "ABNT, 2024."),
     "regime": "norma técnica sob direito autoral da ABNT, citada e não redistribuída"},
    {"sigla": "gil",
     "referencia": ("GIL, Antonio Carlos. Como elaborar projetos de pesquisa. 8. ed. "
                    "Barueri: Atlas, 2026."),
     "regime": "obra sob direito autoral, citada e não redistribuída"},
]

# arquivo do pacote: caminho de origem, o que sustenta, e a sigla da fonte do dado
PACOTE = [
    ("cp-severidade-por-artigo.csv", "a direção de severidade de cada dispositivo, 1940 a 2026", "planalto"),
    ("cp-eventos-de-severidade.csv", "os 130 eventos datados de severidade", "planalto"),
    ("cp-dispositivos-com-artigo.csv", "cada anotação de dispositivo ancorada ao artigo", "planalto"),
    ("cp-normas-alteradoras.csv", "as normas alteradoras lidas do texto compilado", "planalto"),
    ("cp-sancao-veto-publicacao.csv", "a ficha de sanção, veto e publicação de cada norma", "camara-legin"),
    ("cp-serie-anual.csv", "a série anual de normas alteradoras", "planalto"),
    ("cp-compilado-texto.txt", "o texto compilado do Código Penal", "planalto"),
    ("textos-das-normas/codigo-penal-1940-texto-original.json", "o texto original de 1940", "camara-legin"),
    ("textos-das-normas/codigo-penal-1940-retificacao.json", "a Retificação de 3/1/1941", "camara-legin"),
    ("textos-das-normas/texto-integral-planalto.jsonl", "o texto integral das normas", "planalto"),
    ("textos-das-normas/texto-integral-normas-cp.jsonl", "o texto integral pelo Congresso", "camara-legin"),
    ("textos-das-normas/AUDITORIA-DO-TEXTO-DAS-NORMAS.json", "a auditoria de cobertura do texto", "planalto"),
    ("analise-cientifica/calendario-eleitoral-1940-2026.csv", "os 42 pleitos, de 1932 a 2024", "tse-cronologia"),
    ("analise-cientifica/teste-ciclo-eleitoral.json", "o teste do ciclo de 29/08/2026, sobre as 114 fichas do Legin, substituído pelo teste sobre o universo de 115 normas", "tse-cronologia"),
    ("analise-cientifica/teste-severidade-ciclo-eleitoral.json", "o teste sobre o agravamento", "tse-cronologia"),
    ("analise-cientifica/poder-do-teste.json", "o poder do teste de 29/08/2026, sobre o recorte 1940-2025, substituído pelo poder medido no teste sobre o universo de 115 normas, que está em teste-ciclo-eleitoral-universo-115.json e é o que o texto usa", "tse-cronologia"),
    ("analise-cientifica/incerteza-da-associacao.json", "o intervalo de confiança e o p por permutação dos seis coeficientes da Tabela 11", "fbsp"),
    ("analise-cientifica/validade-criterio-regua.json", "o teste de validade da régua", "planalto"),
    ("analise-cientifica/rol-hediondos.json", "o rol vigente de crimes hediondos", "planalto"),
    ("analise-cientifica/rol-como-segunda-unidade.json", "o agravamento fora do texto do Código", "planalto"),
    ("analise-cientifica/severidade-parte-geral.json", "a régua da Parte Geral, 16 institutos", "planalto"),
    ("analise-cientifica/causas-de-aumento.json", "causas de aumento, diminuição e multiplicador", "planalto"),
    ("analise-cientifica/autoria-e-bancada.json", "autoria, partido e direção da norma", "camara-dados-abertos"),
    ("analise-cientifica/teste-origem-x-direcao.json", "o teste de origem contra direção", "camara-dados-abertos"),
    ("analise-cientifica/materia-das-normas.json", "a matéria pelo Título do Código", "planalto"),
    ("analise-cientifica/emendas-e-lsn.json", "a cadeia das leis de segurança nacional", "normas-leg"),
    ("analise-cientifica/emendas-e-lsn.txt", "o detalhe integral das mesmas", "normas-leg"),
    ("analise-cientifica/cruzamento-violencia-e-severidade.json", "violência contra agravamento", "fbsp"),
    ("analise-cientifica/percepcao-e-serie.json", "a percepção de insegurança e a série corrigida", "fbsp-percepcao"),
    ("analise-cientifica/mvi-serie-historica.json", "a série de MVI por edição do Anuário", "fbsp"),
    ("analise-cientifica/regimes-e-pleitos.json", "os regimes políticos e os pleitos", "tse-cronologia"),
    ("analise-cientifica/defasagem-projeto-lei.json", "a defasagem entre o projeto e a lei", "camara-dados-abertos"),
    ("analise-cientifica/pendencias-restantes.json", "poder, sensibilidade, teto efetivo e objeto do voto", "camara-dados-abertos"),
    ("analise-cientifica/sonda-das-fontes-pendentes.json", "a sonda das fontes externas", "planalto"),
    ("analise-cientifica/REVISAO-DE-LITERATURA.md", "a revisão de literatura, 346 artigos", "planalto"),
    ("analise-cientifica/territorio-e-eleitorado.json", "eleitores, habitantes e as correlações da seção 4.27", "tse-eleitorado"),
    ("analise-cientifica/agentes-politicos.json", "quem sancionou ou promulgou, autores com partido e UF, e votações nominais por partido de cada lei", "camara-dados-abertos"),
    ("analise-cientifica/presidentes-mandatos.json", "quem exerceu a Presidência de 1937 a 2026, com o trecho da fonte e a marca declarado ou deduzido", "biblioteca-pr"),
    ("analise-cientifica/bancadas-e-autoria.json", "bancadas da Câmara por legislatura, 1946 a 2027, e leis propostas por 100 deputados", "camara-dados-abertos"),
    ("analise-cientifica/governadores-e-homicidios.json", "governadores eleitos de 1982 a 2022 e os óbitos por agressão do SIM em cada mandato", "tse-candidatos"),
    ("analise-cientifica/governadores-indiretos-dhbb.json", "governadores escolhidos pela Assembleia Legislativa em 1970, 1974 e 1978 e nomeados em território, Distrito Federal e MS, pelo cargo registrado no DHBB, com o número do verbete", "cpdoc-dhbb"),
    ("analise-cientifica/populacao-uf.json", "população residente por UF e ano, 1980 a 2026 sem 2023, com a fonte de cada ano, para a taxa por 100 mil", "pop-uf"),
    ("analise-cientifica/partido-na-epoca.json", "partido de cada deputado autor na data em que apresentou o projeto, pelo histórico da Câmara", "camara-dados-abertos"),
    ("analise-cientifica/conferencia-governadores-1947-1966.json", "a leitura a olho dos governadores de 1947 a 1966 conferida contra a votação nominal por UF", "tse-votacao-uf"),
    # --------------------------------------------------------------------------
    # Acrescentados em 30/08/2026, quando o autoteste mediu 26 apuracoes que existiam
    # no disco e nao chegavam nem ao texto nem ao pacote. Apuracao que fica na gaveta
    # nao sustenta nada: quem examina nao pode conferir o que nao recebeu.
    ("analise-cientifica/CRUZAMENTO-VIOLENCIA-E-SEVERIDADE.md", "o cruzamento da série de violência com a de agravamento, em detalhe", "fbsp"),
    ("analise-cientifica/FONTE-IMPEACHMENT-E-IMPEDIMENTO.md", "a proveniência dos atos de impedimento, na fonte primária", "senado-dados-abertos"),
    ("analise-cientifica/FONTE-TSE-cronologia-das-eleicoes.md", "a proveniência do calendário eleitoral", "tse-cronologia"),
    ("analise-cientifica/FONTES-PROPOSTAS-E-FALAS-medicao.md", "a medição do que existe em proposta de governo e fala de parlamentar", "camara-dados-abertos"),
    ("analise-cientifica/camara-legislaturas.json", "as 57 legislaturas, para situar a autoria no tempo", "camara-dados-abertos"),
    ("analise-cientifica/camara-partidos-historicos.json", "os partidos por legislatura, base da composição de bancada", "camara-dados-abertos"),
    ("analise-cientifica/camara-partidos.json", "os partidos em atividade", "camara-dados-abertos"),
    ("analise-cientifica/comparacao-municipal-x-nacional.json", "o teste do pleito municipal contra o nacional", "tse-cronologia"),
    ("analise-cientifica/conferencia-lei-14197.txt", "a conferência da Lei n. 14.197, de 2021, nas duas direções", "normas-leg"),
    ("analise-cientifica/divergencia-calendario-eleitoral.json", "a divergência medida entre duas fontes oficiais do próprio Tribunal Superior Eleitoral", "tse-cronologia"),
    ("analise-cientifica/emendas-constitucionais-penais.txt", "as emendas constitucionais que citam matéria penal", "normas-leg"),
    ("analise-cientifica/lei-seguranca-nacional.txt", "o texto das leis de segurança nacional, colhido da fonte", "normas-leg"),
    ("analise-cientifica/periodicos-classificacao-relatorio.json", "o relatório da classificação do corpus de literatura", "planalto"),
    ("analise-cientifica/periodicos-juridicos-cp-preciso.jsonl", "o corpus preciso da revisão de literatura, 3.138 registros", "planalto"),
    ("analise-cientifica/senado-discursos-codigo-penal.jsonl", "os 755 pronunciamentos de plenário sobre o Código Penal", "senado-dados-abertos"),
    ("analise-cientifica/senado-partidos.xml", "os partidos no Senado Federal", "senado-dados-abertos"),
    ("analise-cientifica/detalhe-votacoes-sem-objeto.json", "o detalhe da Câmara de cada votação cuja descrição registra só o resultado, que classifica o objeto de 113 votações na Tabela 20", "camara-dados-abertos"),
    ("analise-cientifica/senado-composicao-por-legislatura.json", "os senadores de cada legislatura, de 1946 a 2027, pelo portal do Senado, com a divergência contra as listas da API declarada nos dois sentidos", "senado-dados-abertos"),
    ("analise-cientifica/partido-senador-na-epoca.json", "o partido de cada senador autor na data da apresentação do projeto, pela filiação datada da API do Senado", "senado-dados-abertos"),
    ("textos-das-normas/engolidas-pela-elipse.json", "as normas cujo rastro o texto compilado apagou", "planalto"),
    ("textos-das-normas/faltam-na-fonte-do-congresso.json", "a cobertura que faltou na fonte do Congresso", "camara-legin"),
    ("textos-das-normas/nao-achadas-no-planalto.json", "a cobertura que faltou no Planalto", "planalto"),
    # --------------------------------------------------------------------------
    # Acrescentados em 18/09/2026, na revisão que seguiu a auditoria de 16/09/2026. As
    # Tabelas 4 a 7 do texto saem destes três arquivos.
    ("analise-cientifica/universo-e-regimes.json", "o universo de 115 normas, a data de publicação no DOU de cada uma e o regime vigente nessa data", "camara-legin"),
    ("analise-cientifica/universo-e-regimes.csv", "a mesma apuração, norma a norma, em planilha", "camara-legin"),
    ("analise-cientifica/FECHAMENTO-DO-CORTE-18-09-2026.md", "a conferência, em duas fontes, de que nenhuma norma publicada entre 31/08 e 18/09/2026 alterou o Código Penal", "normas-leg"),
    ("analise-cientifica/teste-ciclo-eleitoral-universo-115.json", "o teste do ciclo eleitoral sobre o universo único de 115 normas", "tse-cronologia"),
    ("analise-cientifica/posicao-do-individuo.json",
     "a posição do indivíduo diante da lei penal, nas duas pontas", "planalto"),
    ("analise-cientifica/ideologia-partidos-especialistas.json", "a média de cada partido na escala de especialistas, ondas de 2018 e 2022, da seção 4.28", "escala-bolognesi"),
    ("analise-cientifica/ideologia-x-penal.json", "os testes da posição ideológica contra voto, autoria e violência sob o governador, Tabela 27", "escala-bolognesi"),
    ("analise-cientifica/voto-eleitor.json", "o sim de cada partido no texto principal e a variação de cadeiras na eleição seguinte, seção 4.28", "tse-candidatos"),
    ("analise-cientifica/doutrina-partidaria.json", "a contagem de expressões de ordem e de direitos nos 305 documentos doutrinários dos partidos, seção 4.28", "tse-partidos"),
    ("analise-cientifica/rankings-e-mapa.json", "os partidos por sim no texto principal, a autoria por partido e por UF e os eventos por ano de mandato presidencial, Tabela 28", "camara-dados-abertos"),
    ("analise-cientifica/presidentes-partido.json", "o partido de cada presidente eleito, pelo registro da candidatura", "tse-candidatos"),
    ("analise-cientifica/anuario-crimes-por-uf.json", "desde quando o Anuário publica cada tipo penal por Unidade da Federação", "fbsp"),
    ("analise-cientifica/serie-longa-violencia.json", "as três séries de violência contra a de agravamento, cada uma na sua janela, com as quatro especificações e a zona cinzenta do registro, Tabelas 29 e 30", "ipea-atlas"),
    ("analise-cientifica/sonda-sinesp-jc.json", "o que cada um dos doze endereços oficiais respondeu quando se procurou a série do Sinesp JC, seção 4.29", "mjsp-sinesp"),
    ("analise-cientifica/sonda-bancovde-anos-anteriores.json", "o teste do padrão de endereço do banco do Sinesp VDE para os onze anos de 2004 a 2014, com os anos de controle, seção 4.29", "mjsp-sinesp"),
    ("analise-cientifica/ranking-e-mapa-por-uf.json", "a taxa de mortes por agressão e intervenção legal por cem mil habitantes, nas 27 Unidades da Federação, ano a ano de 1996 a 2024, com o ranking e o mapa, Tabela 31", "datasus-sim"),
    ("analise-cientifica/notas-sinesp-jc.json", "o que cada nota de gestor estadual do Sinesp JC declara sobre a contagem, com o trecho literal ao lado, Tabela 32", "mjsp-sinesp"),
]

# O QUE FICA DE FORA DO PACOTE, e o motivo de cada um. Declarar e' obrigacao: pacote
# que omite sem dizer parece completo, e quem examina nao sabe o que nao recebeu.
FORA_DO_PACOTE = [
    ("analise-cientifica/obter_texto_integral_corpus.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/segunda_via_texto_integral.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/terceira_via_texto_integral.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/quarta_via_citadas.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/extrair_texto_corpus.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/mapear_citacoes_corpus.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/preparar_lotes_leitura.py",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/apurar_modo_de_leitura.py",
     "apura, a partir dos registros de leitura, em que modo cada uma das 346 obras do núcleo foi lida. O resultado que ele produz está declarado no texto, na seção 2.1, e o registro obra a obra é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/citacoes-texto-integral.json",
     "ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/extrair_estatutos.py",
     "ferramenta de extração dos estatutos do TSE; o resultado que sustenta a seção 4.28 está em doutrina-partidaria.json, que acompanha o pacote"),
    ("analise-cientifica/conferir_anuario_crimes_por_uf.py",
     "ferramenta que lê as tabelas do Anuário; o resultado está em anuario-crimes-por-uf.json, que acompanha o pacote"),
    ("analise-cientifica/SEVERIDADE-ETAPA-1-30-08-2026.md",
     "etapa intermediária, superada pela versão final da mesma apuração"),
    ("analise-cientifica/base-para-conselho.txt",
     "arquivo de trabalho do exame interno. Processo de trabalho não entra na "
     "entrega, pela regra desta casa de 19/08/2026"),
    ("analise-cientifica/periodicos-juridicos-cp-classificado.jsonl",
     "corpus bruto de 50 MB e 30.140 registros. O corpus PRECISO, de 3.138 "
     "registros, é o que sustenta a revisão e acompanha o pacote"),
    ("analise-cientifica/periodicos-termos-concluidos.json",
     "controle interno de coleta, que registra qual termo já foi varrido"),
    ("analise-cientifica/planalto-lei-9504-1997.html",
     "página bruta da fonte. O texto da Lei n. 9.504/1997 é público e está no "
     "Planalto, e redistribuir a página não acrescenta prova"),
    ("analise-cientifica/senado-discursos-meses-lidos.json",
     "controle interno de coleta, mês a mês"),
    ("analise-cientifica/PRE-ESPECIFICACAO-VALIDADE-30-08-2026.md",
     "arquivo interno de trabalho com as previsões do teste de validade da régua, gravado "
     "antes da execução. A data de gravação de um arquivo local não é registro externo e "
     "não prova a anterioridade, e o texto do trabalho declara isso"),
    ("analise-cientifica/senado-leg-47-lista-do-portal-21-09.txt",
     "lista do portal do Senado da 47ª legislatura, colada pelo autor como segunda fonte; "
     "o mesmo conteúdo, com o código de cada senador, está no arquivo da composição do "
     "Senado por legislatura, que acompanha o pacote"),
    ("analise-cientifica/tse-bdje-acervo.jsonl",
     "catálogo de 13.448 itens da Biblioteca Digital da Justiça Eleitoral, dos "
     "quais 7.278 declaram licença Creative Commons NãoComercial ou SemDerivações. "
     "Ele é citado no trabalho e NÃO é redistribuído, pela mesma razão que as "
     "normas da ABNT: acervo de terceiro se cita, não se copia"),
]

SCRIPTS = [
    ("apurar_severidade_parte_geral.py", "constrói a régua da Parte Geral"),
    ("apurar_causas_de_aumento.py", "mede as causas de aumento e o multiplicador"),
    ("apurar_autoria_e_bancada.py", "cruza autoria, partido e direção"),
    ("apurar_materia_das_normas.py", "classifica por Título e testa o confundidor"),
    ("apurar_rol_hediondos.py", "mede o agravamento feito fora do texto"),
    ("apurar_emendas_e_lsn.py", "colhe as leis de segurança nacional e as emendas"),
    ("apurar_pendencias_restantes.py", "mede poder, sensibilidade, teto efetivo e voto"),
    ("apurar_percepcao_e_serie.py", "mede a percepção e a série de mortes violentas"),
    ("extrair_tabelas_anuarios.py", "extrai as tabelas dos Anuários em PDF"),
    ("sondar_fontes_pendentes.py", "sonda as fontes externas com endereço, hora e código"),
    ("conferir_numeros_do_trabalho.py", "confere cada número do trabalho contra a fonte"),
    ("montar_pacote_publico.py", "monta este pacote e calcula os resumos criptográficos"),
    ("apurar_posicao_do_individuo.py", "mede a posição do indivíduo, com bancada de 18 provas"),
    ("testes_pacote_publico.py", "a bancada do montador, 14 provas nas duas direções"),
    ("apurar_universo_e_regimes.py", "data de publicação e regime de cada uma das 115 normas"),
    ("testar_ciclo_eleitoral_universo_115.py", "refaz o teste do ciclo eleitoral sobre as 115 normas"),
    ("montar_base_analitica_na_planilha.py", "monta na planilha os 130 eventos e os 432 dispositivos"),
    ("apurar_incerteza_da_associacao.py", "calcula o intervalo de confiança e o p por permutação da Tabela 11"),
    ("apurar_serie_longa_violencia.py", "roda as três séries de violência contra a de agravamento, cada uma na sua janela"),
    ("sondar_sinesp_jc.py", "sonda os doze endereços oficiais em busca da série do Sinesp JC"),
    ("sondar_bancovde_anos_anteriores.py", "testa se a fonte oficial oferece banco do Sinesp VDE antes de 2015"),
    ("apurar_ranking_e_mapa_por_uf.py", "monta o ranking e o mapa por Unidade da Federação, depois de provar a identidade com a série nacional"),
    ("apurar_notas_sinesp_jc.py", "mede o que cada nota de gestor estadual declara, com o trecho literal"),
    ("analise_ciclo_eleitoral_cp.py", "o motor de permutação por blocos e de simulação de poder que o teste do ciclo importa",
     os.path.join(os.path.expanduser("~"), ".claude", "scripts", "analise_ciclo_eleitoral_cp.py")),
]


def resumo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def json_para_csv(origem, destino):
    """Achata um JSON de apuração em CSV, para quem abre planilha e não programa.

    O CRITERIO NAO E' OBVIO, e a primeira versao errou: achatar cada no' produzia UM
    arquivo por valor escalar. Medido em 30/08/2026: 253 dos 284 CSV gerados tinham uma
    linha so'. Planilha de uma linha nao e' planilha, e' fragmento, e 253 fragmentos
    escondem as 31 tabelas de verdade.

    A regra que ficou, e ela separa duas coisas que sao mesmo diferentes:

    - LISTA DE DICIONARIOS e' tabela, e sai em CSV proprio, com uma linha por item.
    - TODO VALOR ESCALAR, em qualquer profundidade, entra num unico arquivo
      `<base>__valores.csv`, com as colunas `chave` e `valor`, e a chave carrega o
      caminho inteiro ate' ele, para nao se perder de onde veio.

    Devolve a lista de CSV gravados.
    """
    try:
        d = json.load(io.open(origem, encoding="utf-8"))
    except Exception:
        return [], ["nao e' JSON valido"]
    gravados = []
    base = os.path.splitext(os.path.basename(origem))[0]
    escalares = []

    def grava(nome, campos, linhas):
        # O Windows recusa <>:"/\|?* em nome de arquivo. Medido em 18/09/2026: uma chave
        # do teste sobre as 115 normas traz dois-pontos e derrubava o montador no meio.
        nome = re.sub(r'[<>:"/\\|?*]', "_", nome)
        p = os.path.join(destino, "%s__%s.csv" % (base, nome))
        # E o caminho inteiro nao passa de 260 caracteres. Nome longo demais vira os
        # primeiros 60 caracteres mais um resumo de 10, que continua unico e rastreavel:
        # a chave completa fica na primeira coluna do proprio arquivo.
        if len(p) >= 250:
            nome = nome[:60] + "_" + hashlib.sha1(nome.encode("utf-8")).hexdigest()[:10]
            p = os.path.join(destino, "%s__%s.csv" % (base, nome))
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
            w.writeheader()
            for l in linhas:
                w.writerow({k: ("" if l.get(k) is None else
                                (json.dumps(l[k], ensure_ascii=False)
                                 if isinstance(l[k], (dict, list)) else l[k]))
                            for k in campos})
        gravados.append(os.path.basename(p))

    def percorre(no, caminho):
        if isinstance(no, list):
            if no and all(isinstance(x, dict) for x in no):
                campos = []
                for l in no:
                    for k in l:
                        if k not in campos:
                            campos.append(k)
                grava(caminho or "lista", campos, no)
            elif len(no) >= LISTA_LONGA and all(not isinstance(x, (dict, list)) for x in no):
                # Lista LONGA de valores simples vira tabela de duas colunas, porque
                # senao ela infla o arquivo de metadado: medido em 30/08/2026, o texto
                # original de 1940 sozinho punha 2.541 linhas la' dentro.
                # Lista CURTA nao vira planilha propria, e a razao e' simetrica: separar
                # `pleitos: [1945]` produz planilha de uma linha, que e' fragmento e nao
                # dado. Medido no mesmo dia: separar toda lista levou o pacote de 53 para
                # 129 CSV, quase todos de uma linha.
                grava(caminho or "itens", ["indice", "valor"],
                      [{"indice": i, "valor": v} for i, v in enumerate(no)])
            elif no and all(not isinstance(x, (dict, list)) for x in no):
                escalares.append({"chave": caminho,
                                  "valor": json.dumps(no, ensure_ascii=False)})
            else:
                for i, v in enumerate(no):
                    percorre(v, "%s[%d]" % (caminho, i))
        elif isinstance(no, dict):
            for k, v in no.items():
                percorre(v, (caminho + "." + k) if caminho else k)
        else:
            escalares.append({"chave": caminho, "valor": no})

    percorre(d, "")
    if escalares:
        grava("valores", ["chave", "valor"], escalares)
    return gravados, []


def montar():
    if not os.path.exists(BASE):
        print("FALHA REAL: base ausente")
        return 1
    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)
    for sub in ("dados", "planilhas", "scripts"):
        os.makedirs(os.path.join(DESTINO, sub))

    fonte_por_sigla = {f["sigla"]: f for f in FONTES}
    itens, ausentes, sem_fonte = [], [], []
    csvs = []
    for rel, sustenta, sigla in PACOTE:
        origem = os.path.join(R, rel.replace("/", os.sep))
        if not os.path.exists(origem):
            ausentes.append(rel)
            continue
        if sigla not in fonte_por_sigla:
            sem_fonte.append(rel)
            continue
        nome = os.path.basename(rel)
        alvo = os.path.join(DESTINO, "dados", nome)
        shutil.copy2(origem, alvo)
        itens.append({"arquivo": "dados/" + nome, "sustenta": sustenta,
                      "fonte": sigla, "bytes": os.path.getsize(alvo),
                      "sha256": resumo(alvo)})
        if nome.endswith(".json"):
            g, _r = json_para_csv(origem, os.path.join(DESTINO, "planilhas"))
            csvs.extend(g)
        elif nome.endswith(".csv"):
            shutil.copy2(origem, os.path.join(DESTINO, "planilhas", nome))
            csvs.append(nome)

    for item in SCRIPTS:
        rel, sustenta = item[0], item[1]
        # terceiro elemento, quando existe, e' a origem fora do projeto (o motor do teste)
        origem = item[2] if len(item) > 2 else os.path.join(R, rel)
        if not os.path.exists(origem):
            ausentes.append(rel)
            continue
        alvo = os.path.join(DESTINO, "scripts", rel)
        shutil.copy2(origem, alvo)
        itens.append({"arquivo": "scripts/" + rel, "sustenta": sustenta,
                      "fonte": "proprio", "bytes": os.path.getsize(alvo),
                      "sha256": resumo(alvo)})

    for nome in sorted(os.listdir(os.path.join(DESTINO, "planilhas"))):
        p = os.path.join(DESTINO, "planilhas", nome)
        itens.append({"arquivo": "planilhas/" + nome,
                      "sustenta": "a mesma medida, em formato de planilha",
                      "fonte": "proprio", "bytes": os.path.getsize(p),
                      "sha256": resumo(p)})

    c = sqlite3.connect(BASE)
    c.row_factory = sqlite3.Row
    fontes_base = [dict(r) for r in c.execute(
        "SELECT tabela, arquivo, linhas, colunas, bytes, sha256, situacao FROM fonte ORDER BY tabela")]
    tabelas = [x[0] for x in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name NOT LIKE 'busca%' ORDER BY name")]
    linhas = {t: c.execute("SELECT COUNT(*) FROM [%s]" % t).fetchone()[0] for t in tabelas}
    c.close()

    manifesto = {
        "o_que_e": "pacote publico de dados do projeto de extensao sobre o Codigo Penal",
        "montado_em": time.strftime("%Y-%m-%d"),
        "base_completa": {"arquivo": "BASE-CODIGO-PENAL.sqlite",
                          "bytes": os.path.getsize(BASE), "sha256": resumo(BASE),
                          "tabelas_de_dado": len(tabelas),
                          "linhas_por_tabela": linhas,
                          "linhas_somadas": sum(linhas.values()),
                          "fontes_declaradas": len(fontes_base)},
        "fontes_e_direitos": FONTES,
        "fontes_da_base": fontes_base,
        "arquivos_do_pacote": itens,
        "planilhas_geradas": sorted(set(csvs)),
        "apuracao_deliberadamente_fora_do_pacote":
            [{"arquivo": a, "por_que": b} for a, b in FORA_DO_PACOTE],
        "arquivos_declarados_e_ausentes": ausentes,
        "arquivos_sem_fonte_declarada": sem_fonte,
    }
    io.open(os.path.join(DESTINO, "MANIFESTO.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(manifesto, ensure_ascii=False, indent=1))

    # ------------------------------------------------------ catalogo de fontes
    C = ["# Catálogo de fontes", "",
         "Toda medida deste projeto sai de fonte identificada. Este catálogo traz a",
         "referência de cada uma na ABNT NBR 6023 e o regime de direito que ela declara.", "",
         "Citar a fonte não é formalidade: publicar dado derivado de terceiro sem apontar",
         "a origem é apropriação, ainda que involuntária.", "",
         "## As fontes, uma a uma", ""]
    for f in FONTES:
        C.append("### `%s`" % f["sigla"])
        C.append("")
        C.append(f["referencia"])
        C.append("")
        C.append("**Regime de direito**: %s" % f["regime"])
        C.append("")
    C += ["## Qual arquivo veio de qual fonte", "",
          "| Arquivo | Fonte | O que sustenta |", "|---|---|---|"]
    for x in itens:
        if x["fonte"] != "proprio":
            C.append("| `%s` | `%s` | %s |" % (x["arquivo"], x["fonte"], x["sustenta"]))
    io.open(os.path.join(DESTINO, "CATALOGO-DE-FONTES.md"), "w", encoding="utf-8",
            newline="").write(chr(10).join(C))

    # ----------------------------------------------------------- direitos e uso
    D = ["# Direitos e uso", "",
         "## O que este pacote contém, e o que ele não contém", "",
         "Ele contém a **apuração própria**: as tabelas, as séries e os testes construídos",
         "neste projeto, mais os programas que os produzem.", "",
         "## Sob que licença ele é oferecido", "",
         "| O que | Licença | Arquivo |",
         "|---|---|---|",
         "| as tabelas, as séries, os testes e o texto | **Creative Commons Atribuição 4.0 "
         "Internacional** | `LICENSE` |",
         "| os programas da pasta `scripts` | **MIT** | `LICENSE-CODIGO` |", "",
         "Você pode copiar, adaptar e usar para qualquer fim, inclusive comercial, **desde",
         "que cite a autoria** e indique se houve alteração. Ao usar um dado específico,",
         "cite também a fonte de origem dele.", "",
         "**Isto foi decidido em 23/09/2026, e antes disso não havia licença nenhuma.** Obra",
         "publicada sem licença é obra de todos os direitos reservados: a utilização depende",
         "de autorização prévia e expressa do autor, pelo art. 29 da Lei n. 9.610, de 1998.",
         "O pacote estava, portanto, aberto para ler e fechado para reutilizar, ao contrário",
         "do que ele próprio anuncia.", "",
         "**O que a licença não alcança**: a proteção de base de dados do art. 7º, inciso",
         "XIII, da mesma lei recai sobre a seleção, a organização e a disposição do",
         "conteúdo, e o § 2º do mesmo artigo declara que ela **não abarca os dados ou",
         "materiais em si mesmos**. O que se licencia aqui é a estrutura construída neste",
         "projeto, e não os números brutos, que nunca foram fechados.", "",
         "Ele **não redistribui obra de terceiro**. Nenhum relatório, livro ou norma técnica",
         "de outra autoria acompanha o pacote. O que há é a referência de cada um e a medida",
         "extraída, com a origem declarada em cada valor.", "",
         "## Por que essa separação, e ela foi medida", "",
         "Dos 13.448 itens da Biblioteca Digital da Justiça Eleitoral catalogados neste",
         "projeto, **7.278 declaram licença Creative Commons**, e a maioria é NãoComercial",
         "ou SemDerivações, o que restringe redistribuição.", "",
         "As normas da ABNT e os livros de metodologia estão sob direito autoral e são",
         "citados, nunca reproduzidos.", "",
         "## O que é de domínio público", "",
         "Texto de lei, decisão judicial e ato oficial não são objeto de proteção autoral,",
         "pelo art. 8º, inciso IV, da Lei n. 9.610, de 1998. O texto do Código Penal, o das",
         "115 normas alteradoras e as decisões dos tribunais entram nessa categoria.", "",
         "## Como citar este pacote", "",
         "PEREIRA, Edvandro Adolfo. **O Código Penal atende a quem tem medo, a quem vota, ou",
         "a quem manda?**: oitenta e seis anos de criminalização no Brasil. Uberaba: Centro",
         "Universitário UniFACTHUS, 2026. Pacote de dados.", "",
         "## Como citar uma fonte usada aqui", "",
         "Use a referência do `CATALOGO-DE-FONTES.md`, e não este pacote. O dado é da fonte;",
         "a apuração é deste projeto.", "",
         "## Integridade", "",
         "Cada arquivo traz o seu resumo criptográfico no `MANIFESTO.json`. Conferi-lo antes",
         "de usar é o que garante que o arquivo é o mesmo que foi publicado."]
    io.open(os.path.join(DESTINO, "DIREITOS-E-USO.md"), "w", encoding="utf-8",
            newline="").write(chr(10).join(D))

    # As duas licencas viajam DENTRO do pacote, e nao so' no repositorio do site: o pacote e'
    # baixado como unidade propria, e quem o recebe por outro caminho nao ve' o `LICENSE` que
    # fica na raiz do repositorio. Os arquivos sao COPIADOS da origem unica em `site/licencas`,
    # nunca escritos aqui, para que as duas copias nao possam divergir em silencio.
    _lic = os.path.join(R, "site", "licencas")
    for _o, _d in (("CC-BY-4.0.txt", "LICENSE"), ("MIT.txt", "LICENSE-CODIGO")):
        _c = os.path.join(_lic, _o)
        if not os.path.exists(_c):
            print("ERRO: falta a licenca %s. Sem ela o pacote sai sem autorizacao de uso, e a "
                  "montagem nao segue." % _c)
            return 1
        shutil.copyfile(_c, os.path.join(DESTINO, _d))

    # ------------------------------------------------------------------ leia-me
    L = ["# Pacote de dados", "",
         "Este pacote existe para que o exame deste trabalho não dependa de acreditar no",
         "autor. Cada número afirmado no texto sai de um destes arquivos.", "",
         "## Como está organizado", "",
         "| Pasta | O que traz |", "|---|---|",
         "| `dados` | os arquivos de apuração, no formato em que foram produzidos |",
         "| `planilhas` | as mesmas medidas em CSV, para abrir em planilha |",
         "| `scripts` | os programas que produzem cada medida, cada um com bancada própria |",
         "", "| Arquivo | O que traz |", "|---|---|",
         "| `MANIFESTO.json` | o resumo criptográfico de cada arquivo e o inventário das fontes |",
         "| `CATALOGO-DE-FONTES.md` | a referência ABNT de cada fonte e o regime de direito |",
         "| `DIREITOS-E-USO.md` | o que pode ser redistribuído, o que não pode, e como citar |",
         "| `LEIA-ME.md` | este arquivo |", "",
         "## A base completa", "",
         "| Item | Valor |", "|---|---|",
         "| arquivo | `BASE-CODIGO-PENAL.sqlite` |",
         "| bytes | %d |" % manifesto["base_completa"]["bytes"],
         "| tabelas de dado | %d |" % manifesto["base_completa"]["tabelas_de_dado"],
         "| linhas somadas | %d |" % manifesto["base_completa"]["linhas_somadas"],
         "| fontes declaradas | %d |" % manifesto["base_completa"]["fontes_declaradas"],
         "| sha256 | `%s` |" % manifesto["base_completa"]["sha256"], "",
         "Ela não acompanha o protocolo por causa do tamanho. Os arquivos deste pacote",
         "bastam para refazer toda tabela do trabalho sem precisar dela.", "",
         "## Como conferir", "",
         "1. Confira o resumo criptográfico de cada arquivo contra o `MANIFESTO.json`.",
         "2. Abra e conte. Toda tabela do trabalho sai de contagem sobre estes dados.",
         "3. Rode cada programa da pasta `scripts` com o argumento `--bancada`, que",
         "   executa as provas do instrumento antes de qualquer medida, e depois sem ele.", "",
         "Divergência entre o que você contar e o que o trabalho afirma é achado, e o",
         "achado é de quem contou.", "",
         "## O que NÃO acompanha o pacote, e por quê", "",
         "Pacote que omite sem dizer parece completo, e quem examina não sabe o que",
         "não recebeu. Estes ficaram de fora por decisão declarada:", "",
         "| Arquivo | Por que ficou fora |", "|---|---|"]
    for a, b in FORA_DO_PACOTE:
        L.append("| `%s` | %s |" % (a, b))
    L += ["",
         "## Inventário", "",
         "| Arquivo | Bytes | Fonte do dado |", "|---|---|---|"]
    for x in itens:
        L.append("| `%s` | %d | %s |" % (x["arquivo"], x["bytes"], x["fonte"]))
    io.open(os.path.join(DESTINO, "LEIA-ME.md"), "w", encoding="utf-8", newline="").write(
        chr(10).join(L))

    tam = sum(os.path.getsize(os.path.join(d, a))
              for d, _, arq in os.walk(DESTINO) for a in arq)
    n = sum(len(a) for _, _, a in os.walk(DESTINO))
    print("=== PACOTE PUBLICO MONTADO ===")
    print("   destino       : %s" % DESTINO)
    print("   arquivos      : %d, somando %.1f MB" % (n, tam / 1024 / 1024))
    print("   dados         : %d" % len([x for x in itens if x["arquivo"].startswith("dados/")]))
    print("   planilhas CSV : %d" % len([x for x in itens if x["arquivo"].startswith("planilhas/")]))
    print("   scripts       : %d" % len([x for x in itens if x["arquivo"].startswith("scripts/")]))
    print("   fontes citadas na NBR 6023: %d" % len(FONTES))
    print("   base          : %d bytes, %d tabelas, %d linhas"
          % (manifesto["base_completa"]["bytes"], manifesto["base_completa"]["tabelas_de_dado"],
             manifesto["base_completa"]["linhas_somadas"]))
    print()
    erro = 0
    if ausentes:
        print("ARQUIVOS DECLARADOS E AUSENTES: %d" % len(ausentes))
        for a in ausentes:
            print("   " + a)
        erro = 1
    if sem_fonte:
        print("ARQUIVOS SEM FONTE DECLARADA: %d" % len(sem_fonte))
        for a in sem_fonte:
            print("   " + a)
        print("Publicar dado sem apontar a origem e' apropriacao, ainda que involuntaria.")
        erro = 1
    if not erro:
        print("   zero arquivo ausente e zero arquivo sem fonte declarada")
    return erro


if __name__ == "__main__":
    sys.exit(montar())
