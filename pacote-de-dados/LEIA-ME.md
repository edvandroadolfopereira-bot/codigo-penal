# Pacote de dados

Este pacote existe para que o exame deste trabalho não dependa de acreditar no
autor. Cada número afirmado no texto sai de um destes arquivos.

## Como está organizado

| Pasta | O que traz |
|---|---|
| `dados` | os arquivos de apuração, no formato em que foram produzidos |
| `planilhas` | as mesmas medidas em CSV, para abrir em planilha |
| `scripts` | os programas que produzem cada medida, cada um com bancada própria |

| Arquivo | O que traz |
|---|---|
| `MANIFESTO.json` | o resumo criptográfico de cada arquivo e o inventário das fontes |
| `CATALOGO-DE-FONTES.md` | a referência ABNT de cada fonte e o regime de direito |
| `DIREITOS-E-USO.md` | o que pode ser redistribuído, o que não pode, e como citar |
| `LEIA-ME.md` | este arquivo |

## A base completa

| Item | Valor |
|---|---|
| arquivo | `BASE-CODIGO-PENAL.sqlite` |
| bytes | 210190336 |
| tabelas de dado | 42 |
| linhas somadas | 157799 |
| fontes declaradas | 41 |
| sha256 | `2a7e54a9bbb7025b0bd69dfe7fd51f7ddb9d3ac1b8e92a89593995581f51773d` |

Ela não acompanha o protocolo por causa do tamanho. Os arquivos deste pacote
bastam para refazer toda tabela do trabalho sem precisar dela.

## Como conferir

1. Confira o resumo criptográfico de cada arquivo contra o `MANIFESTO.json`.
2. Abra e conte. Toda tabela do trabalho sai de contagem sobre estes dados.
3. Rode cada programa da pasta `scripts` com o argumento `--bancada`, que
   executa as provas do instrumento antes de qualquer medida, e depois sem ele.

Divergência entre o que você contar e o que o trabalho afirma é achado, e o
achado é de quem contou.

## O que NÃO acompanha o pacote, e por quê

Pacote que omite sem dizer parece completo, e quem examina não sabe o que
não recebeu. Estes ficaram de fora por decisão declarada:

| Arquivo | Por que ficou fora |
|---|---|
| `analise-cientifica/obter_texto_integral_corpus.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/segunda_via_texto_integral.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/terceira_via_texto_integral.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/quarta_via_citadas.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/extrair_texto_corpus.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/mapear_citacoes_corpus.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/preparar_lotes_leitura.py` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/citacoes-texto-integral.json` | ferramenta de coleta do texto integral da literatura; o registro da leitura é arquivo de trabalho e não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/extrair_estatutos.py` | ferramenta de extração dos estatutos do TSE; o resultado que sustenta a seção 4.28 está em doutrina-partidaria.json, que acompanha o pacote |
| `analise-cientifica/conferir_anuario_crimes_por_uf.py` | ferramenta que lê as tabelas do Anuário; o resultado está em anuario-crimes-por-uf.json, que acompanha o pacote |
| `analise-cientifica/SEVERIDADE-ETAPA-1-30-08-2026.md` | etapa intermediária, superada pela versão final da mesma apuração |
| `analise-cientifica/base-para-conselho.txt` | arquivo de trabalho do exame interno. Processo de trabalho não entra na entrega, pela regra desta casa de 19/08/2026 |
| `analise-cientifica/periodicos-juridicos-cp-classificado.jsonl` | corpus bruto de 50 MB e 30.140 registros. O corpus PRECISO, de 3.138 registros, é o que sustenta a revisão e acompanha o pacote |
| `analise-cientifica/periodicos-termos-concluidos.json` | controle interno de coleta, que registra qual termo já foi varrido |
| `analise-cientifica/planalto-lei-9504-1997.html` | página bruta da fonte. O texto da Lei n. 9.504/1997 é público e está no Planalto, e redistribuir a página não acrescenta prova |
| `analise-cientifica/senado-discursos-meses-lidos.json` | controle interno de coleta, mês a mês |
| `analise-cientifica/PRE-ESPECIFICACAO-VALIDADE-30-08-2026.md` | arquivo interno de trabalho com as previsões do teste de validade da régua, gravado antes da execução. A data de gravação de um arquivo local não é registro externo e não prova a anterioridade, e o texto do trabalho declara isso |
| `analise-cientifica/senado-leg-47-lista-do-portal-21-09.txt` | lista do portal do Senado da 47ª legislatura, colada pelo autor como segunda fonte; o mesmo conteúdo, com o código de cada senador, está no arquivo da composição do Senado por legislatura, que acompanha o pacote |
| `analise-cientifica/tse-bdje-acervo.jsonl` | catálogo de 13.448 itens da Biblioteca Digital da Justiça Eleitoral, dos quais 7.278 declaram licença Creative Commons NãoComercial ou SemDerivações. Ele é citado no trabalho e NÃO é redistribuído, pela mesma razão que as normas da ABNT: acervo de terceiro se cita, não se copia |

## Inventário

| Arquivo | Bytes | Fonte do dado |
|---|---|---|
| `dados/cp-severidade-por-artigo.csv` | 49663 | planalto |
| `dados/cp-eventos-de-severidade.csv` | 11221 | planalto |
| `dados/cp-dispositivos-com-artigo.csv` | 117893 | planalto |
| `dados/cp-normas-alteradoras.csv` | 4417 | planalto |
| `dados/cp-sancao-veto-publicacao.csv` | 112706 | camara-legin |
| `dados/cp-serie-anual.csv` | 1320 | planalto |
| `dados/cp-compilado-texto.txt` | 303873 | planalto |
| `dados/codigo-penal-1940-texto-original.json` | 193024 | camara-legin |
| `dados/codigo-penal-1940-retificacao.json` | 5462 | camara-legin |
| `dados/texto-integral-planalto.jsonl` | 2358433 | planalto |
| `dados/texto-integral-normas-cp.jsonl` | 1774853 | camara-legin |
| `dados/AUDITORIA-DO-TEXTO-DAS-NORMAS.json` | 37353 | planalto |
| `dados/calendario-eleitoral-1940-2026.csv` | 4415 | tse-cronologia |
| `dados/teste-ciclo-eleitoral.json` | 23572 | tse-cronologia |
| `dados/teste-severidade-ciclo-eleitoral.json` | 14355 | tse-cronologia |
| `dados/poder-do-teste.json` | 393 | tse-cronologia |
| `dados/incerteza-da-associacao.json` | 1127 | fbsp |
| `dados/validade-criterio-regua.json` | 7311 | planalto |
| `dados/rol-hediondos.json` | 4074 | planalto |
| `dados/rol-como-segunda-unidade.json` | 4898 | planalto |
| `dados/severidade-parte-geral.json` | 10121 | planalto |
| `dados/causas-de-aumento.json` | 6151 | planalto |
| `dados/autoria-e-bancada.json` | 8849 | camara-dados-abertos |
| `dados/teste-origem-x-direcao.json` | 514 | camara-dados-abertos |
| `dados/materia-das-normas.json` | 9449 | planalto |
| `dados/emendas-e-lsn.json` | 3099 | normas-leg |
| `dados/emendas-e-lsn.txt` | 56659 | normas-leg |
| `dados/cruzamento-violencia-e-severidade.json` | 2051 | fbsp |
| `dados/percepcao-e-serie.json` | 7484 | fbsp-percepcao |
| `dados/mvi-serie-historica.json` | 7829 | fbsp |
| `dados/regimes-e-pleitos.json` | 2354 | tse-cronologia |
| `dados/defasagem-projeto-lei.json` | 24405 | camara-dados-abertos |
| `dados/pendencias-restantes.json` | 14666 | camara-dados-abertos |
| `dados/sonda-das-fontes-pendentes.json` | 3636 | planalto |
| `dados/REVISAO-DE-LITERATURA.md` | 26961 | planalto |
| `dados/territorio-e-eleitorado.json` | 6582 | tse-eleitorado |
| `dados/agentes-politicos.json` | 213538 | camara-dados-abertos |
| `dados/presidentes-mandatos.json` | 12691 | biblioteca-pr |
| `dados/bancadas-e-autoria.json` | 47304 | camara-dados-abertos |
| `dados/governadores-e-homicidios.json` | 139073 | tse-candidatos |
| `dados/governadores-indiretos-dhbb.json` | 26673 | cpdoc-dhbb |
| `dados/populacao-uf.json` | 28048 | pop-uf |
| `dados/partido-na-epoca.json` | 34797 | camara-dados-abertos |
| `dados/conferencia-governadores-1947-1966.json` | 61151 | tse-votacao-uf |
| `dados/CRUZAMENTO-VIOLENCIA-E-SEVERIDADE.md` | 5662 | fbsp |
| `dados/FONTE-IMPEACHMENT-E-IMPEDIMENTO.md` | 4965 | senado-dados-abertos |
| `dados/FONTE-TSE-cronologia-das-eleicoes.md` | 13192 | tse-cronologia |
| `dados/FONTES-PROPOSTAS-E-FALAS-medicao.md` | 6481 | camara-dados-abertos |
| `dados/camara-legislaturas.json` | 9162 | camara-dados-abertos |
| `dados/camara-partidos-historicos.json` | 16713 | camara-dados-abertos |
| `dados/camara-partidos.json` | 3297 | camara-dados-abertos |
| `dados/comparacao-municipal-x-nacional.json` | 5255 | tse-cronologia |
| `dados/conferencia-lei-14197.txt` | 3275 | normas-leg |
| `dados/divergencia-calendario-eleitoral.json` | 2488 | tse-cronologia |
| `dados/emendas-constitucionais-penais.txt` | 143 | normas-leg |
| `dados/lei-seguranca-nacional.txt` | 26340 | normas-leg |
| `dados/periodicos-classificacao-relatorio.json` | 2456 | planalto |
| `dados/periodicos-juridicos-cp-preciso.jsonl` | 5410058 | planalto |
| `dados/senado-discursos-codigo-penal.jsonl` | 1129656 | senado-dados-abertos |
| `dados/senado-partidos.xml` | 11728 | senado-dados-abertos |
| `dados/detalhe-votacoes-sem-objeto.json` | 96710 | camara-dados-abertos |
| `dados/senado-composicao-por-legislatura.json` | 312760 | senado-dados-abertos |
| `dados/partido-senador-na-epoca.json` | 13849 | senado-dados-abertos |
| `dados/engolidas-pela-elipse.json` | 7832 | planalto |
| `dados/faltam-na-fonte-do-congresso.json` | 16832 | camara-legin |
| `dados/nao-achadas-no-planalto.json` | 108 | planalto |
| `dados/universo-e-regimes.json` | 2450 | camara-legin |
| `dados/universo-e-regimes.csv` | 12893 | camara-legin |
| `dados/FECHAMENTO-DO-CORTE-18-09-2026.md` | 1152 | normas-leg |
| `dados/teste-ciclo-eleitoral-universo-115.json` | 23081 | tse-cronologia |
| `dados/posicao-do-individuo.json` | 2736 | planalto |
| `dados/ideologia-partidos-especialistas.json` | 12243 | escala-bolognesi |
| `dados/ideologia-x-penal.json` | 72964 | escala-bolognesi |
| `dados/voto-eleitor.json` | 13772 | tse-candidatos |
| `dados/doutrina-partidaria.json` | 46884 | tse-partidos |
| `dados/rankings-e-mapa.json` | 11042 | camara-dados-abertos |
| `dados/presidentes-partido.json` | 4177 | tse-candidatos |
| `dados/anuario-crimes-por-uf.json` | 171993 | fbsp |
| `dados/serie-longa-violencia.json` | 10058 | ipea-atlas |
| `dados/sonda-sinesp-jc.json` | 4805 | mjsp-sinesp |
| `dados/sonda-bancovde-anos-anteriores.json` | 3232 | mjsp-sinesp |
| `dados/ranking-e-mapa-por-uf.json` | 101044 | datasus-sim |
| `dados/notas-sinesp-jc.json` | 11451 | mjsp-sinesp |
| `scripts/apurar_severidade_parte_geral.py` | 19403 | proprio |
| `scripts/apurar_causas_de_aumento.py` | 14154 | proprio |
| `scripts/apurar_autoria_e_bancada.py` | 14592 | proprio |
| `scripts/apurar_materia_das_normas.py` | 27197 | proprio |
| `scripts/apurar_rol_hediondos.py` | 12326 | proprio |
| `scripts/apurar_emendas_e_lsn.py` | 11227 | proprio |
| `scripts/apurar_pendencias_restantes.py` | 23321 | proprio |
| `scripts/apurar_percepcao_e_serie.py` | 12557 | proprio |
| `scripts/extrair_tabelas_anuarios.py` | 4048 | proprio |
| `scripts/sondar_fontes_pendentes.py` | 9139 | proprio |
| `scripts/conferir_numeros_do_trabalho.py` | 20162 | proprio |
| `scripts/montar_pacote_publico.py` | 48697 | proprio |
| `scripts/apurar_posicao_do_individuo.py` | 14944 | proprio |
| `scripts/testes_pacote_publico.py` | 5294 | proprio |
| `scripts/apurar_universo_e_regimes.py` | 16257 | proprio |
| `scripts/testar_ciclo_eleitoral_universo_115.py` | 6300 | proprio |
| `scripts/montar_base_analitica_na_planilha.py` | 16115 | proprio |
| `scripts/apurar_incerteza_da_associacao.py` | 6081 | proprio |
| `scripts/apurar_serie_longa_violencia.py` | 12077 | proprio |
| `scripts/sondar_sinesp_jc.py` | 6540 | proprio |
| `scripts/sondar_bancovde_anos_anteriores.py` | 4708 | proprio |
| `scripts/apurar_ranking_e_mapa_por_uf.py` | 9604 | proprio |
| `scripts/apurar_notas_sinesp_jc.py` | 5870 | proprio |
| `scripts/analise_ciclo_eleitoral_cp.py` | 15447 | proprio |
| `planilhas/AUDITORIA-DO-TEXTO-DAS-NORMAS__normas.csv` | 12581 | proprio |
| `planilhas/AUDITORIA-DO-TEXTO-DAS-NORMAS__valores.csv` | 1456 | proprio |
| `planilhas/agentes-politicos__normas.csv` | 106811 | proprio |
| `planilhas/agentes-politicos__valores.csv` | 4529 | proprio |
| `planilhas/anuario-crimes-por-uf__2007.lidos.csv` | 114 | proprio |
| `planilhas/anuario-crimes-por-uf__2008.lidos.csv` | 137 | proprio |
| `planilhas/anuario-crimes-por-uf__2009.lidos.csv` | 130 | proprio |
| `planilhas/anuario-crimes-por-uf__2010.lidos.csv` | 152 | proprio |
| `planilhas/anuario-crimes-por-uf__2011.lidos.csv` | 150 | proprio |
| `planilhas/anuario-crimes-por-uf__2012.lidos.csv` | 152 | proprio |
| `planilhas/anuario-crimes-por-uf__2013.lidos.csv` | 163 | proprio |
| `planilhas/anuario-crimes-por-uf__2014.lidos.csv` | 166 | proprio |
| `planilhas/anuario-crimes-por-uf__2015.lidos.csv` | 166 | proprio |
| `planilhas/anuario-crimes-por-uf__2016.lidos.csv` | 157 | proprio |
| `planilhas/anuario-crimes-por-uf__2017.lidos.csv` | 160 | proprio |
| `planilhas/anuario-crimes-por-uf__2018.lidos.csv` | 228 | proprio |
| `planilhas/anuario-crimes-por-uf__2019.lidos.csv` | 268 | proprio |
| `planilhas/anuario-crimes-por-uf__2020.lidos.csv` | 348 | proprio |
| `planilhas/anuario-crimes-por-uf__2021.lidos.csv` | 216 | proprio |
| `planilhas/anuario-crimes-por-uf__2022.lidos.csv` | 296 | proprio |
| `planilhas/anuario-crimes-por-uf__2023.lidos.csv` | 336 | proprio |
| `planilhas/anuario-crimes-por-uf__2024.lidos.csv` | 194 | proprio |
| `planilhas/anuario-crimes-por-uf__2025.lidos.csv` | 194 | proprio |
| `planilhas/anuario-crimes-por-uf__2026.lidos.csv` | 206 | proprio |
| `planilhas/anuario-crimes-por-uf___excluidos_por_serem_copia_de_outra_edicao.csv` | 261 | proprio |
| `planilhas/anuario-crimes-por-uf__valores.csv` | 169485 | proprio |
| `planilhas/autoria-e-bancada__valores.csv` | 16034 | proprio |
| `planilhas/bancadas-e-autoria__divergencias_ficha_x_epoca.csv` | 3669 | proprio |
| `planilhas/bancadas-e-autoria__legislaturas.csv` | 7677 | proprio |
| `planilhas/bancadas-e-autoria__taxa_autoria_por_100.csv` | 569 | proprio |
| `planilhas/bancadas-e-autoria__valores.csv` | 38926 | proprio |
| `planilhas/calendario-eleitoral-1940-2026.csv` | 4415 | proprio |
| `planilhas/camara-legislaturas__lista.csv` | 4797 | proprio |
| `planilhas/camara-partidos-historicos__partidos.csv` | 7506 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.49.csv` | 190 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.52.csv` | 222 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.53.csv` | 198 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.54.csv` | 247 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.55.csv` | 335 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.56.csv` | 336 | proprio |
| `planilhas/camara-partidos-historicos__por_legislatura.57.csv` | 267 | proprio |
| `planilhas/camara-partidos-historicos__valores.csv` | 1405 | proprio |
| `planilhas/camara-partidos__lista.csv` | 2015 | proprio |
| `planilhas/causas-de-aumento__epocas.1940.subestimacao_por_artigo.csv` | 378 | proprio |
| `planilhas/causas-de-aumento__epocas.hoje.subestimacao_por_artigo.csv` | 513 | proprio |
| `planilhas/causas-de-aumento__valores.csv` | 1480 | proprio |
| `planilhas/codigo-penal-1940-retificacao__documentos.csv` | 4296 | proprio |
| `planilhas/codigo-penal-1940-retificacao__valores.csv` | 309 | proprio |
| `planilhas/codigo-penal-1940-texto-original__valores.csv` | 188483 | proprio |
| `planilhas/comparacao-municipal-x-nacional__lista.csv` | 1783 | proprio |
| `planilhas/conferencia-governadores-1947-1966__linhas.csv` | 21369 | proprio |
| `planilhas/cp-dispositivos-com-artigo.csv` | 117893 | proprio |
| `planilhas/cp-eventos-de-severidade.csv` | 11221 | proprio |
| `planilhas/cp-normas-alteradoras.csv` | 4417 | proprio |
| `planilhas/cp-sancao-veto-publicacao.csv` | 112706 | proprio |
| `planilhas/cp-serie-anual.csv` | 1320 | proprio |
| `planilhas/cp-severidade-por-artigo.csv` | 49663 | proprio |
| `planilhas/cruzamento-violencia-e-severidade__valores.csv` | 2558 | proprio |
| `planilhas/defasagem-projeto-lei__defasagem.csv` | 10070 | proprio |
| `planilhas/detalhe-votacoes-sem-objeto__votacoes.csv` | 74089 | proprio |
| `planilhas/divergencia-calendario-eleitoral__DIVERGENCIA_ENTRE_AS_DUAS_FONTES_OFICIAIS.UNIAO.csv` | 373 | proprio |
| `planilhas/divergencia-calendario-eleitoral__fonte_1_cronologia_TSE.csv` | 373 | proprio |
| `planilhas/divergencia-calendario-eleitoral__fonte_2_resultados_TSE.csv` | 292 | proprio |
| `planilhas/divergencia-calendario-eleitoral__fonte_3_lista_que_eu_usei_de_memoria.csv` | 220 | proprio |
| `planilhas/divergencia-calendario-eleitoral__valores.csv` | 504 | proprio |
| `planilhas/doutrina-partidaria__por_partido.csv` | 25202 | proprio |
| `planilhas/doutrina-partidaria__testes.direitos_escala_2018.partidos_usados.csv` | 229 | proprio |
| `planilhas/doutrina-partidaria__testes.direitos_escala_2022.partidos_usados.csv` | 240 | proprio |
| `planilhas/doutrina-partidaria__testes.indice_ordem_menos_direitos_escala_2018.partidos_usados.csv` | 229 | proprio |
| `planilhas/doutrina-partidaria__testes.indice_ordem_menos_direitos_escala_2022.partidos_usados.csv` | 240 | proprio |
| `planilhas/doutrina-partidaria__testes.ordem_escala_2018.partidos_usados.csv` | 229 | proprio |
| `planilhas/doutrina-partidaria__testes.ordem_escala_2022.partidos_usados.csv` | 240 | proprio |
| `planilhas/doutrina-partidaria__valores.csv` | 3000 | proprio |
| `planilhas/emendas-e-lsn__lei_de_seguranca_nacional.achadas_SO_por_numero_e_nao_por_ementa.csv` | 281 | proprio |
| `planilhas/emendas-e-lsn__lei_de_seguranca_nacional.normas_que_DEFINEM_crime_contra_a_seguranca_nacional.csv` | 1378 | proprio |
| `planilhas/emendas-e-lsn__valores.csv` | 825 | proprio |
| `planilhas/engolidas-pela-elipse__normas.csv` | 2748 | proprio |
| `planilhas/engolidas-pela-elipse__valores.csv` | 130 | proprio |
| `planilhas/faltam-na-fonte-do-congresso__normas.csv` | 9561 | proprio |
| `planilhas/faltam-na-fonte-do-congresso__valores.csv` | 130 | proprio |
| `planilhas/governadores-e-homicidios__governadores.csv` | 54592 | proprio |
| `planilhas/governadores-e-homicidios__valores.csv` | 952 | proprio |
| `planilhas/governadores-indiretos-dhbb__fora_da_lista.csv` | 558 | proprio |
| `planilhas/governadores-indiretos-dhbb__governadores.csv` | 7152 | proprio |
| `planilhas/governadores-indiretos-dhbb__nomeados.csv` | 3998 | proprio |
| `planilhas/governadores-indiretos-dhbb__valores.csv` | 1344 | proprio |
| `planilhas/ideologia-partidos-especialistas__cortes.csv` | 140 | proprio |
| `planilhas/ideologia-partidos-especialistas__divergencias_entre_as_fontes.csv` | 89 | proprio |
| `planilhas/ideologia-partidos-especialistas__valores.csv` | 16706 | proprio |
| `planilhas/ideologia-x-penal__A_voto_nominal.por_partido.csv` | 1996 | proprio |
| `planilhas/ideologia-x-penal__B_autoria.normas.csv` | 499 | proprio |
| `planilhas/ideologia-x-penal__C_governadores.mandatos.csv` | 11977 | proprio |
| `planilhas/ideologia-x-penal__valores.csv` | 6587 | proprio |
| `planilhas/incerteza-da-associacao__especificacoes.csv` | 323 | proprio |
| `planilhas/incerteza-da-associacao__valores.csv` | 318 | proprio |
| `planilhas/materia-das-normas__anos_eleitorais_usados.csv` | 382 | proprio |
| `planilhas/materia-das-normas__titulos_lidos.csv` | 1177 | proprio |
| `planilhas/materia-das-normas__valores.csv` | 9891 | proprio |
| `planilhas/mvi-serie-historica__valores.csv` | 8165 | proprio |
| `planilhas/nao-achadas-no-planalto__valores.csv` | 80 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.CEARÁ.declaracoes.csv` | 1359 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.GOIÁS.declaracoes.csv` | 1728 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.MATO GROSSO.declaracoes.csv` | 1068 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.MINAS GERAIS.declaracoes.csv` | 894 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.PARANÁ.declaracoes.csv` | 729 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.PERNAMBUCO.declaracoes.csv` | 142 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.PIAUÍ.declaracoes.csv` | 330 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.RIO DE JANEIRO.declaracoes.csv` | 124 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.RONDÔNIA.declaracoes.csv` | 84 | proprio |
| `planilhas/notas-sinesp-jc__por_unidade_da_federacao.SÃO PAULO.declaracoes.csv` | 487 | proprio |
| `planilhas/notas-sinesp-jc__valores.csv` | 2356 | proprio |
| `planilhas/partido-na-epoca__valores.csv` | 54085 | proprio |
| `planilhas/partido-senador-na-epoca__valores.csv` | 23748 | proprio |
| `planilhas/pendencias-restantes__A_poder_do_teste_da_agenda.resultados.csv` | 143 | proprio |
| `planilhas/pendencias-restantes__C_teto_efetivo.detalhe.csv` | 1958 | proprio |
| `planilhas/pendencias-restantes__D_objeto_das_votacoes.por_objeto.csv` | 378 | proprio |
| `planilhas/pendencias-restantes__valores.csv` | 3428 | proprio |
| `planilhas/percepcao-e-serie__B_percepcao_de_inseguranca.comparacao_2017_contra_2022.csv` | 385 | proprio |
| `planilhas/percepcao-e-serie__B_percepcao_de_inseguranca.estudos_lidos.csv` | 1817 | proprio |
| `planilhas/percepcao-e-serie__B_percepcao_de_inseguranca.medidas_de_2022_sem_par_em_2017.csv` | 388 | proprio |
| `planilhas/percepcao-e-serie__valores.csv` | 4071 | proprio |
| `planilhas/periodicos-classificacao-relatorio__valores.csv` | 2593 | proprio |
| `planilhas/poder-do-teste__valores.csv` | 390 | proprio |
| `planilhas/populacao-uf__valores.csv` | 35230 | proprio |
| `planilhas/posicao-do-individuo__B_recorte_estreito.por_titulo.csv` | 192 | proprio |
| `planilhas/posicao-do-individuo__valores.csv` | 2945 | proprio |
| `planilhas/presidentes-mandatos__periodos.csv` | 8153 | proprio |
| `planilhas/presidentes-mandatos__valores.csv` | 707 | proprio |
| `planilhas/presidentes-partido__valores.csv` | 4832 | proprio |
| `planilhas/ranking-e-mapa-por-uf__ranking_pela_taxa_no_ultimo_ano.csv` | 865 | proprio |
| `planilhas/ranking-e-mapa-por-uf__valores.csv` | 137110 | proprio |
| `planilhas/rankings-e-mapa__R1_partidos_por_sim_no_texto_base_que_agrava.csv` | 278 | proprio |
| `planilhas/rankings-e-mapa__R2_partidos_por_autoria.csv` | 249 | proprio |
| `planilhas/rankings-e-mapa__R3_presidentes_por_normas_por_ano.csv` | 1237 | proprio |
| `planilhas/rankings-e-mapa__valores.csv` | 5241 | proprio |
| `planilhas/regimes-e-pleitos__regimes.csv` | 884 | proprio |
| `planilhas/regimes-e-pleitos__valores.csv` | 48 | proprio |
| `planilhas/rol-como-segunda-unidade__artigos_do_rol_invisiveis_para_a_regua.csv` | 86 | proprio |
| `planilhas/rol-como-segunda-unidade__normas_que_tocaram_o_rol.csv` | 414 | proprio |
| `planilhas/rol-como-segunda-unidade__parametros_medidos.csv` | 473 | proprio |
| `planilhas/rol-como-segunda-unidade__sobreposicao_com_a_regua_do_texto.csv` | 692 | proprio |
| `planilhas/rol-como-segunda-unidade__valores.csv` | 530 | proprio |
| `planilhas/rol-como-segunda-unidade__vedacoes.csv` | 209 | proprio |
| `planilhas/rol-hediondos__deixado_de_fora.csv` | 530 | proprio |
| `planilhas/rol-hediondos__detalhe.csv` | 974 | proprio |
| `planilhas/rol-hediondos__valores.csv` | 828 | proprio |
| `planilhas/senado-composicao-por-legislatura__valores.csv` | 410114 | proprio |
| `planilhas/serie-longa-violencia__testes.csv` | 1600 | proprio |
| `planilhas/serie-longa-violencia__valores.csv` | 20212 | proprio |
| `planilhas/severidade-parte-geral__institutos.csv` | 5297 | proprio |
| `planilhas/severidade-parte-geral__valores.csv` | 869 | proprio |
| `planilhas/sonda-bancovde-anos-anteriores__anos_de_controle.csv` | 280 | proprio |
| `planilhas/sonda-bancovde-anos-anteriores__anos_testados.csv` | 728 | proprio |
| `planilhas/sonda-bancovde-anos-anteriores__valores.csv` | 598 | proprio |
| `planilhas/sonda-das-fontes-pendentes__sondas.csv` | 2534 | proprio |
| `planilhas/sonda-das-fontes-pendentes__valores.csv` | 336 | proprio |
| `planilhas/sonda-sinesp-jc__resultados.csv` | 2689 | proprio |
| `planilhas/sonda-sinesp-jc__valores.csv` | 303 | proprio |
| `planilhas/territorio-e-eleitorado__correlacoes.csv` | 1966 | proprio |
| `planilhas/territorio-e-eleitorado__valores.csv` | 2948 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.PRINCIPAL_ anos completos, 1945 a 2025.GOVERNADOR direto.anos_do_grupo.csv` | 184 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.PRINCIPAL_ anos completos, 1945 a 2025.LEGISLATIVA FEDERAL direta.anos_do_grupo.csv` | 202 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.PRINCIPAL_ anos completos, 1945 a 2025.MUNICIPAL ISOLADA, sem presidencial.anos_do_grupo.csv` | 193 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.PRINCIPAL_ anos completos, 1945 a 2025.MUNICIPAL, qualquer.anos_do_grupo.csv` | 256 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.SENSIBILIDADE_ com 2026 incompleto, contagem crua.GOVERNADOR direto.anos_do_grupo.csv` | 193 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.SENSIBILIDADE_ com 2026 incompleto, contagem crua.LEG_065659ae0e.csv` | 211 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.SENSIBILIDADE_ com 2026 incompleto, contagem crua.MUNICIPAL, qualquer.anos_do_grupo.csv` | 256 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__testes.SENSIBILIDADE_ com 2026 incompleto, contagem crua.MUN_7506fa796d.csv` | 193 | proprio |
| `planilhas/teste-ciclo-eleitoral-universo-115__valores.csv` | 47231 | proprio |
| `planilhas/teste-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.GOVERNADOR direto.anos_do_grupo.csv` | 184 | proprio |
| `planilhas/teste-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.LEGISLATIVA FEDERAL direta.anos_do_grupo.csv` | 202 | proprio |
| `planilhas/teste-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.MUNICIPAL ISOLADA, sem presidencial.anos_do_grupo.csv` | 193 | proprio |
| `planilhas/teste-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.MUNICIPAL, qualquer.anos_do_grupo.csv` | 256 | proprio |
| `planilhas/teste-ciclo-eleitoral__valores.csv` | 34890 | proprio |
| `planilhas/teste-origem-x-direcao__valores.csv` | 660 | proprio |
| `planilhas/teste-severidade-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.GOVERNADOR direto.anos_do_grupo.csv` | 184 | proprio |
| `planilhas/teste-severidade-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.LEGISLATIVA FEDERAL direta.anos_do_grupo.csv` | 202 | proprio |
| `planilhas/teste-severidade-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.MUNICIPAL ISOLADA, sem presidencial.anos_do_grupo.csv` | 193 | proprio |
| `planilhas/teste-severidade-ciclo-eleitoral__testes.serie inteira, sem o ano em curso.MUNICIPAL, qualquer.anos_do_grupo.csv` | 256 | proprio |
| `planilhas/teste-severidade-ciclo-eleitoral__valores.csv` | 26470 | proprio |
| `planilhas/universo-e-regimes.csv` | 12893 | proprio |
| `planilhas/universo-e-regimes__por_regime.csv` | 348 | proprio |
| `planilhas/universo-e-regimes__valores.csv` | 1241 | proprio |
| `planilhas/validade-criterio-regua__P5_conferencia_item_a_item.detalhe.csv` | 1989 | proprio |
| `planilhas/validade-criterio-regua__valores.csv` | 1811 | proprio |
| `planilhas/voto-eleitor__etapa_3_teste.54.partidos.csv` | 415 | proprio |
| `planilhas/voto-eleitor__etapa_3_teste.56.partidos.csv` | 561 | proprio |
| `planilhas/voto-eleitor__valores.csv` | 17187 | proprio |