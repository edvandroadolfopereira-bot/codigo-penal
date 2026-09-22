# -*- coding: utf-8 -*-
"""O UNIVERSO de normas e a classificacao por REGIME pela data de publicacao.

Nasceu da auditoria de 16/09/2026, achados 3.2 e 3.4, e das decisoes do autor em
18/09/2026:

  - data de corte: 30/09/2026;
  - cada norma se classifica no regime vigente na DATA DE PUBLICACAO no Diario Oficial
    da Uniao, e nao pelo ano. Com o ano, 1964 e 1985 entravam nos dois regimes
    vizinhos, e as taxas usavam denominadores incompativeis.

O QUE FAZ:
  1. le a data de publicacao de cada uma das 115 normas em DUAS fontes independentes:
     a ficha do Legin da Camara ("Publicacao Original" no DOU) e o portal Normas.leg.br
     (campo datePublished). Divergencia entre as duas sai listada, nunca resolvida em
     silencio. Vale a do Legin; a do Normas.leg.br cobre a norma sem ficha;
  2. classifica cada norma no regime da data de publicacao;
  3. calcula a exposicao de cada regime em anos exatos (dias / 365,2425), e a taxa de
     normas alteradoras por ano de regime;
  4. procura no Normas.leg.br norma que ALTERA o Codigo Penal publicada DEPOIS da
     janela observada, para a recoleta de outubro. Nao a inclui: so' lista.

A JANELA OBSERVADA termina na data em que o universo foi coletado, e nao na data de
corte. Contar exposicao ate' 30/09/2026 com normas coletadas so' ate' 30/08/2026
poria no denominador um mes em que o numerador nao olhou. Depois da recoleta,
JANELA_FIM passa a ser 30/09/2026.

OS MARCOS DOS REGIMES sao premissa do trabalho e precisam de fonte historiografica
citada antes de entrar no texto. Estao isolados na tabela REGIMES para serem trocados
num lugar so'.
"""

import collections
import csv
import datetime as dt
import io
import json
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")
NORMAS_LEG = os.path.expanduser(os.path.join("~", ".claude", "normas-leg"))
SAIDA_JSON = os.path.join(R, "analise-cientifica", "universo-e-regimes.json")
SAIDA_CSV = os.path.join(R, "analise-cientifica", "universo-e-regimes.csv")

URN_CP = "decreto.lei:1940-12-07;2848"
CORTE = dt.date(2026, 9, 18)   # decisao do autor em 18/09/2026: coletas ate' hoje, para fechar o trabalho
JANELA_FIM = CORTE   # 18/09/2026: Normas.leg.br recolhido hoje e texto compilado do Planalto conferido; nenhuma norma nova entre 31/08 e 18/09

# (nome, inicio, fim), fim inclusive. Marcos conferidos em 18/09/2026, com trecho lido:
#   29/10/1945: FGV CPDOC, pagina "A sanha dos meus inimigos...": o periodo Vargas "se
#               encerrou em 29 de outubro de 1945, quando Vargas deposto se autoexila".
#               https://cpdoc.fgv.br/pesquisa-conhecimento/getulio-vargas-1954
#   31/03/1964: FGV CPDOC, "O golpe de 1964 e a instauracao do regime militar": movimento
#               "deflagrado em 31 de marco de 1964". https://cpdoc.fgv.br/artigos/golpe-1964
#               A vacancia so' foi declarada pelo Congresso em 02/04/1964; por isso o teste
#               de sensibilidade abaixo lista toda norma publicada entre 31/03 e 02/04/1964.
#   15/03/1985: FGV, Atlas Historico do Brasil, verbete 4909: "cerimonia de transmissao do
#               cargo em 15 de marco de 1985". https://atlas.fgv.br/verbete/4909
REGIMES = [
    ("Estado Novo", None, dt.date(1945, 10, 29)),
    ("República de 1946", dt.date(1945, 10, 30), dt.date(1964, 3, 31)),
    ("Ditadura militar", dt.date(1964, 4, 1), dt.date(1985, 3, 14)),
    ("Nova República", dt.date(1985, 3, 15), CORTE),
]

MESES = {m: i for i, m in enumerate(
    "janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro".split(), 1)}


def sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chave_do_rotulo(rot):
    """(numero, ano) de 'Lei Ordinaria n. 9.268, de 1o de abril de 1996'. Aceita 1o."""
    m = re.search(r"n[ºo°]\s*([\d.]+),\s*de\s*\d{1,2}[ºo°]?\s*de\s*\w+\s*de\s*(\d{4})", rot or "")
    return (int(m.group(1).replace(".", "")), int(m.group(2))) if m else None


RE_DOU = re.compile(r"Diário Oficial da União[^|]*?(\d{1,2})/(\d{1,2})/(\d{4}), Página \d+ \(Publicação Original\)")


def datas_legin(c):
    """Data de publicacao original no DOU, por (numero, ano), lida da ficha."""
    out = {}
    for rot, dn, pub in c.execute("SELECT norma, data_no_nome, publicacoes FROM cp_sancao_veto_publicacao"):
        k = chave_do_rotulo(rot)
        if not k:
            continue
        ds = {dt.date(int(a), int(m), int(d)) for d, m, a in RE_DOU.findall(pub or "")}
        out.setdefault(k, {"assinatura": dn, "dou": set()})["dou"] |= ds
    return out


def ler_normas_leg(anos):
    """datePublished e alteracao do CP, por (numero, ano), lendo os arquivos dos anos
    pedidos do comeco ao fim. Tambem devolve toda norma que toca o CP."""
    pasta = os.path.join(os.path.realpath(os.path.join(NORMAS_LEG, "data")), "normas")
    por_chave, tocam_cp = {}, []
    ler_normas_leg.nao_lidos = []
    for ano in sorted(anos):
        p = os.path.join(pasta, "textos-%d.jsonl" % ano)
        if not os.path.exists(p):
            continue
        # Arquivo que o OneDrive nao entrega (marcador de nuvem que expira ao baixar)
        # levanta OSError 22. Ele NAO e' lido, e isso se declara: a segunda fonte fica
        # sem conferir aquele ano, o que nunca se le' como "confere".
        try:
            with io.open(p, encoding="utf-8") as f:
                linhas_do_ano = f.readlines()
        except OSError as e:
            ler_normas_leg.nao_lidos.append("%d (%s)" % (ano, e.__class__.__name__))
            continue
        if True:
            for linha in linhas_do_ano:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                urn = d.get("urn", "")
                m = re.search(r":(lei|decreto\.lei|lei\.complementar|medida\.provisoria|decreto):(\d{4})-\d{2}-\d{2};(\d+)", urn)
                if not m:
                    continue
                k = (int(m.group(3)), int(m.group(2)))
                pub = d.get("datePublished")
                pub = pub[0] if isinstance(pub, list) else pub
                efeitos = []
                for campo in ("legislationAmends", "legislationRepeals", "legislationCommences"):
                    v = d.get(campo) or []
                    efeitos += v if isinstance(v, list) else [v]
                toca = any(URN_CP in str(e.get("@id", "")) for e in efeitos if isinstance(e, dict))
                reg = {"urn": urn, "tipo": m.group(1), "publicacao": pub, "toca_cp": toca, "nome": d.get("name")}
                por_chave.setdefault(k, []).append(reg)
                if toca:
                    tocam_cp.append(reg)
    return por_chave, tocam_cp


def regime_de(data):
    for nome, ini, fim in REGIMES:
        if (ini is None or data >= ini) and data <= fim:
            return nome
    return None


def main():
    c = sqlite3.connect(BASE)
    universo = c.execute("SELECT especie, numero, ano, procedencia FROM uniao_normas_alteradoras").fetchall()
    legin = datas_legin(c)
    c.close()

    anos = {int(a) for _, _, a, _ in universo} | {1940, JANELA_FIM.year, CORTE.year}
    nleg, tocam_cp = ler_normas_leg(anos)

    cp = [r for r in nleg.get((2848, 1940), []) if r["tipo"] == "decreto.lei"]
    inicio_cp = dt.date.fromisoformat(cp[0]["publicacao"]) if cp and cp[0]["publicacao"] else None
    if inicio_cp is None:
        print("FALHA REAL: data de publicacao do proprio Codigo Penal nao encontrada no Normas.leg.br")
        return 1

    linhas, diverg, sem_data, fonte_usada = [], [], [], collections.Counter()
    for esp, num, ano, proc in universo:
        k = (int(str(num).replace(".", "")), int(ano))
        dl = sorted(legin.get(k, {}).get("dou", set()))
        cand = [r for r in nleg.get(k, []) if r["publicacao"]]
        dn = sorted({dt.date.fromisoformat(r["publicacao"][:10]) for r in cand})
        if dl and dn and dl[0] != dn[0]:
            diverg.append({"norma": "%s %s/%s" % (esp, num, ano), "legin_dou": str(dl[0]), "normas_leg": str(dn[0])})
        if dl:
            data, fonte = dl[0], "Legin, ficha, Publicação Original no DOU"
        elif dn:
            data, fonte = dn[0], "Normas.leg.br, datePublished"
        else:
            sem_data.append("%s %s/%s" % (esp, num, ano))
            continue
        fonte_usada[fonte] += 1
        linhas.append({"especie": esp, "numero": num, "ano_da_norma": int(ano), "procedencia": proc,
                       "publicacao_dou": data.isoformat(), "fonte_da_data": fonte,
                       "segunda_fonte": (dn[0].isoformat() if (dl and dn) else ""),
                       "regime": regime_de(data),
                       "dentro_da_janela": data <= JANELA_FIM})

    if sem_data:
        print("RECUSADO: normas sem data de publicacao em nenhuma das duas fontes: %s" % sem_data)
        return 1

    # exposicao e taxa por regime
    por_regime = collections.Counter(l["regime"] for l in linhas if l["dentro_da_janela"])
    tabela = []
    for nome, ini, fim in REGIMES:
        a = max(ini or inicio_cp, inicio_cp)
        b = min(fim, JANELA_FIM)
        dias = (b - a).days + 1 if b >= a else 0
        anos_exp = dias / 365.2425
        n = por_regime.get(nome, 0)
        tabela.append({"regime": nome, "inicio_contado": a.isoformat(), "fim_contado": b.isoformat(),
                       "dias": dias, "anos_de_exposicao": round(anos_exp, 3), "normas": n,
                       "normas_por_ano": round(n / anos_exp, 3) if anos_exp else None})

    ja = {(int(str(l["numero"]).replace(".", "")), l["ano_da_norma"]) for l in linhas}

    # NORMAS QUE TOCAM O CP, coluna da Tabela 4 (acrescentado em 18/09/2026, porque a coluna
    # estava no texto sem arquivo de apuracao). O conjunto e' a UNIAO das fichas do Legin que
    # tocam o Codigo (alteram o texto ou incidem sem alterar) com o universo das 115 normas
    # alteradoras, porque a Lei 6.368/1976 esta' no universo e nao tem ficha no Legin. A data
    # e' a mesma das alteradoras: Publicacao Original no DOU, e o Normas.leg.br na falta dela.
    tocam = {k: min(v["dou"]) for k, v in legin.items() if v["dou"]}
    sem_data_tocam = sorted(k for k, v in legin.items() if not v["dou"])
    for l in linhas:
        k = (int(str(l["numero"]).replace(".", "")), l["ano_da_norma"])
        tocam.setdefault(k, dt.date.fromisoformat(l["publicacao_dou"]))
    for k in list(sem_data_tocam):
        cand = sorted(r["publicacao"][:10] for r in nleg.get(k, []) if r["publicacao"])
        if cand:
            tocam[k] = dt.date.fromisoformat(cand[0])
            sem_data_tocam.remove(k)
    tocam_por_regime = collections.Counter(regime_de(d) for d in tocam.values() if d <= JANELA_FIM)
    for t in tabela:
        t["normas_que_tocam_o_cp"] = tocam_por_regime.get(t["regime"], 0)

    novas = []
    for r in tocam_cp:
        m = re.search(r"(\d{4})-\d{2}-\d{2};(\d+)$", r["urn"])
        k = (int(m.group(2)), int(m.group(1))) if m else None
        if r["publicacao"] and r["publicacao"][:10] > JANELA_FIM.isoformat() and k not in ja:
            novas.append({"nome": r["nome"], "urn": r["urn"], "publicacao": r["publicacao"][:10],
                          "ate_o_corte": r["publicacao"][:10] <= CORTE.isoformat()})
    fora_da_janela = [l for l in linhas if not l["dentro_da_janela"]]

    # sensibilidade aos marcos: norma publicada a menos de 30 dias de um marco, e, no
    # golpe, toda norma entre a deflagracao (31/03) e a vacancia (02/04/1964).
    marcos = [dt.date(1945, 10, 29), dt.date(1964, 3, 31), dt.date(1985, 3, 15)]
    sensiveis = []
    for l in linhas:
        d = dt.date.fromisoformat(l["publicacao_dou"])
        for m in marcos:
            if abs((d - m).days) <= 30:
                sensiveis.append({"norma": "%s %s/%s" % (l["especie"], l["numero"], l["ano_da_norma"]),
                                  "publicacao": l["publicacao_dou"], "marco": m.isoformat(),
                                  "dias_do_marco": (d - m).days, "regime": l["regime"]})

    ordem = [n for n, _, _ in REGIMES]
    linhas.sort(key=lambda l: l["publicacao_dou"])
    tmp = SAIDA_CSV + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    os.replace(tmp, SAIDA_CSV)
    resumo = {
        "gerado_em": dt.date.today().isoformat(),
        "corte": CORTE.isoformat(),
        "janela_observada": [inicio_cp.isoformat(), JANELA_FIM.isoformat()],
        "inicio_da_janela": "publicacao do proprio Codigo Penal no DOU, lida no Normas.leg.br",
        "anos_da_segunda_fonte_NAO_lidos": ler_normas_leg.nao_lidos,
        "normas_sem_conferencia_pela_segunda_fonte": [
            "%s %s/%s" % (l["especie"], l["numero"], l["ano_da_norma"]) for l in linhas
            if l["fonte_da_data"].startswith("Legin") and not l["segunda_fonte"]],
        "normas_no_universo": len(linhas),
        "normas_dentro_da_janela": sum(1 for l in linhas if l["dentro_da_janela"]),
        "fonte_da_data": dict(fonte_usada),
        "divergencias_entre_as_duas_fontes": diverg,
        "por_regime": tabela,
        "soma_por_regime": sum(t["normas"] for t in tabela),
        "normas_que_tocam_o_cp": {
            "definicao": "uniao das fichas do Legin que tocam o Codigo (alteram o texto ou incidem sem alterar) com as 115 normas alteradoras",
            "fichas_do_legin": len(legin),
            "total_na_uniao": len(tocam),
            "dentro_da_janela": sum(tocam_por_regime.values()),
            "sem_data_em_nenhuma_fonte": ["%s/%s" % k for k in sem_data_tocam],
            "por_regime": {t["regime"]: t["normas_que_tocam_o_cp"] for t in tabela}},
        "normas_que_tocam_o_cp_publicadas_depois_da_janela": novas,
        "marcos_e_fontes": {
            "1945-10-29": "FGV CPDOC, https://cpdoc.fgv.br/pesquisa-conhecimento/getulio-vargas-1954",
            "1964-03-31": "FGV CPDOC, https://cpdoc.fgv.br/artigos/golpe-1964",
            "1985-03-15": "FGV, Atlas Historico do Brasil, https://atlas.fgv.br/verbete/4909"},
        "normas_a_ate_30_dias_de_um_marco": sensiveis,
        "ordem_dos_regimes": ordem,
    }
    tmp = SAIDA_JSON + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SAIDA_JSON)

    print("inicio da janela (publicacao do CP no DOU): %s | fim da janela: %s | corte: %s"
          % (inicio_cp, JANELA_FIM, CORTE))
    print("normas no universo: %d | dentro da janela: %d | fontes da data: %s"
          % (len(linhas), resumo["normas_dentro_da_janela"], dict(fonte_usada)))
    print("anos do Normas.leg.br NAO lidos (nuvem): %s" % (ler_normas_leg.nao_lidos or "nenhum"))
    print("normas com data conferida nas duas fontes: %d | so' pela ficha do Legin: %d"
          % (sum(1 for l in linhas if l["segunda_fonte"]),
             len(resumo["normas_sem_conferencia_pela_segunda_fonte"])))
    print("divergencias Legin x Normas.leg.br: %d" % len(diverg))
    for d in diverg:
        print("   ", d)
    print("%-20s %-12s %-12s %9s %7s %10s" % ("regime", "inicio", "fim", "anos", "normas", "por ano"))
    for t in tabela:
        print("%-20s %-12s %-12s %9.3f %7d %10s" % (t["regime"], t["inicio_contado"], t["fim_contado"],
                                                   t["anos_de_exposicao"], t["normas"], t["normas_por_ano"]))
    print("soma por regime: %d" % resumo["soma_por_regime"])
    print("normas a ate' 30 dias de um marco de regime: %d" % len(sensiveis))
    for s in sensiveis:
        print("   ", s)
    print("normas do universo publicadas depois da janela: %s" % [l["especie"] + " " + l["numero"] for l in fora_da_janela])
    print("normas que tocam o CP no Normas.leg.br, publicadas depois de %s e fora do universo: %d" % (JANELA_FIM, len(novas)))
    for n in novas:
        print("   ", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
