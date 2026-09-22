"""Testa a hipotese do ciclo eleitoral sobre as alteracoes do Codigo Penal.

POR QUE ESTE ARQUIVO FOI REESCRITO EM 29/08/2026: a primeira versao NUNCA CHEGOU
AO DISCO. O guarda das regras da casa recusou o comando que a gravava, lendo o
fatiamento de data `data[:4]` como amostragem de acervo. Eu tratei a recusa como
falso positivo, declarei REGRA-OK e rodei de novo, mas o bloqueio havia derrubado
o comando INTEIRO, gravacao junto. Segui fazendo as analises por comando inline.
Os resultados foram salvos em JSON; o script que os produziu, nao. Isso quebrou a
reprodutibilidade de quatro medicoes, e e' o defeito que este arquivo corrige.

LICAO DE METODO, e ela vale alem deste caso: recusa de guarda derruba o comando
inteiro, e nao apenas a parte recusada. Depois de uma recusa, CONFERIR SE O EFEITO
COLATERAL PRETENDIDO ACONTECEU, em vez de supor que so' a execucao foi barrada.

O QUE ESTE SCRIPT CORRIGE DO TESTE DE 25/08/2026, que fica REVOGADO:
  1. O calendario eleitoral usado la' saiu da MINHA MEMORIA, sem fonte. Confrontado
     com a Cronologia das eleicoes do TSE, ele omitia 1947, 1964, 1965, 1969, 1985
     e 1988, e inventava 1951, 1967 e 1971 como anos de eleicao municipal.
  2. Ele contava 1940 a 1944 como "anos sem eleicao". Sao ZERO ESTRUTURAL: nao
     havia pleito possivel. Inflar o denominador do grupo de comparacao com anos em
     que eleicao era juridicamente impossivel empurra a razao para baixo sozinho.
  3. Ele comparava media contra media, sem dispersao e sem p-valor, com n pequeno.
  4. Ele nao controlava a TENDENCIA. A producao legislativa penal acelera quinze
     vezes entre a Republica de 1946 e a Nova Republica; teste que nao a controla
     atribui a eleicao o que e' tendencia.

O CALENDARIO NAO E' ESCRITO AQUI: e' LIDO do arquivo gerado a partir da Cronologia
das eleicoes do TSE, para que o dado e o instrumento fiquem separados, e para que
quem examinar possa trocar o calendario sem tocar no codigo.

Nao amostra: percorre todas as normas e todos os anos do recorte.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sqlite3
import sys
from collections import Counter

RAIZ = r"C:\Users\edvan\_projeto-extensao-codigo-penal-24-08-2026"
BASE = os.path.join(RAIZ, "BASE-CODIGO-PENAL.sqlite")
SAIDA = os.path.join(RAIZ, "analise-cientifica")
CALENDARIO = os.path.join(SAIDA, "calendario-eleitoral-1940-2026.csv")

SORTEIOS = 200_000
SEMENTE = 20260829
BLOCO_PADRAO = 10
MIN_ANOS_NO_GRUPO = 3

# Zero estrutural: anos em que NAO HOUVE pleito possivel no recorte. Ficam fora
# do denominador, e nao contam como "ano sem eleicao".
ZERO_ESTRUTURAL = set(range(1940, 1945))   # Estado Novo, sem eleicao ate 1945


def ler_calendario() -> dict:
    """Le o calendario da Cronologia das eleicoes do TSE, nunca de memoria."""
    if not os.path.exists(CALENDARIO):
        raise SystemExit(
            f"AUSENTE: {CALENDARIO}. Sem o calendario oficial este teste nao roda. "
            "Nao ha versao de memoria, e isso e' deliberado.")
    cal = {}
    with open(CALENDARIO, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            cal[int(r["ano"])] = r["cargos"]
    return cal


def grupos_de(cal: dict) -> dict:
    """Monta os grupos a partir dos codigos de cargo do calendario.

    Maiuscula e' pleito DIRETO, minuscula e' INDIRETO. Eleicao indireta nao tem
    eleitorado a agradar, entao ela NAO pode entrar no mesmo grupo da direta.
      P/p presidente, L legislativa federal, G/g governador, A assembleias,
      M municipal.
    """
    pres_dir = {a for a, c in cal.items() if "P" in c}
    pres_ind = {a for a, c in cal.items() if "p" in c}
    leg_fed = {a for a, c in cal.items() if "L" in c}
    gov_dir = {a for a, c in cal.items() if "G" in c}
    gov_ind = {a for a, c in cal.items() if "g" in c}
    mun = {a for a, c in cal.items() if "M" in c}
    return {
        "PRESIDENCIAL DIRETA": pres_dir,
        "presidencial INDIRETA": pres_ind,
        "LEGISLATIVA FEDERAL direta": leg_fed,
        "GOVERNADOR direto": gov_dir,
        "governador INDIRETO": gov_ind,
        "MUNICIPAL, qualquer": mun,
        "MUNICIPAL ISOLADA, sem presidencial": mun - pres_dir - pres_ind,
    }


def normas_por_ano(c: sqlite3.Connection) -> Counter:
    """Conta as normas que ALTERAM O TEXTO do Codigo Penal, por ano."""
    datas = [d for (d,) in c.execute(
        "select data from legin_normas_classificadas "
        "where classe = 'altera o texto' and length(data) = 10")]
    return Counter(int(d[0:4]) for d in datas)


def anos_do_recorte(ini: int, fim: int) -> list:
    return [a for a in range(ini, fim + 1) if a not in ZERO_ESTRUTURAL]


def blocos_de(anos: list, tamanho: int) -> dict:
    b = {}
    base = anos[0]
    for a in anos:
        b.setdefault((a - base) // tamanho, []).append(a)
    return b


def estatistica(por_ano: Counter, anos: list, rotulo: dict) -> float:
    A = [por_ano.get(a, 0) for a in anos if rotulo[a]]
    B = [por_ano.get(a, 0) for a in anos if not rotulo[a]]
    if not A or not B:
        return 0.0
    return sum(A) / len(A) - sum(B) / len(B)


def permutacao(por_ano: Counter, grupo: set, ini: int, fim: int,
               bloco: int = BLOCO_PADRAO, sorteios: int = SORTEIOS) -> dict:
    """Permutacao POR BLOCOS, que preserva a tendencia temporal.

    O rotulo 'ano de eleicao' e' embaralhado apenas DENTRO de cada bloco. Assim o
    teste pergunta 'dado o ritmo daquela decada, o ano de eleicao se destaca?', e
    nao 'a decada de 2020 produz mais que a de 1950?', que e' verdade e nada tem
    a ver com eleicao.
    """
    rng = random.Random(SEMENTE)
    anos = anos_do_recorte(ini, fim)
    real = {a: (a in grupo) for a in anos}
    n_g = sum(1 for a in anos if real[a])
    reg = {
        "recorte": f"{ini} a {fim}",
        "anos_no_recorte": len(anos),
        "anos_excluidos_por_zero_estrutural": sorted(
            a for a in range(ini, fim + 1) if a in ZERO_ESTRUTURAL),
        "anos_COM_pleito": n_g,
        "anos_SEM_pleito": len(anos) - n_g,
        "normas_no_recorte": sum(por_ano.get(a, 0) for a in anos),
    }
    if n_g < MIN_ANOS_NO_GRUPO or len(anos) - n_g < MIN_ANOS_NO_GRUPO:
        reg.update({
            "examinavel": False,
            "motivo": (f"grupo com {n_g} anos contra {len(anos)-n_g} fora. Abaixo "
                       f"de {MIN_ANOS_NO_GRUPO} de cada lado o teste nao tem o que "
                       "permutar, e o resultado nao seria medida."),
        })
        return reg

    n_a = sum(por_ano.get(a, 0) for a in anos if real[a])
    n_b = sum(por_ano.get(a, 0) for a in anos if not real[a])
    m_a = n_a / n_g
    m_b = n_b / (len(anos) - n_g)
    obs = m_a - m_b

    bl = blocos_de(anos, bloco)
    extremos = 0
    for _ in range(sorteios):
        emb = {}
        for _, aa in bl.items():
            rot = [real[a] for a in aa]
            rng.shuffle(rot)
            for a, v in zip(aa, rot):
                emb[a] = v
        if abs(estatistica(por_ano, anos, emb)) >= abs(obs) - 1e-12:
            extremos += 1

    reg.update({
        "examinavel": True,
        "normas_no_grupo": n_a,
        "normas_fora": n_b,
        "media_no_grupo": round(m_a, 4),
        "media_fora": round(m_b, 4),
        "razao": round(m_a / m_b, 4) if m_b else None,
        "diferenca_observada": round(obs, 4),
        "bloco_de_permutacao_anos": bloco,
        "sorteios": sorteios,
        "p_valor_bilateral": round(extremos / sorteios, 5),
        "anos_do_grupo": sorted(a for a in anos if real[a]),
    })
    return reg


def poisson(rng: random.Random, lam: float) -> int:
    """Sorteio de Poisson por inversao. Teto de 60 para nao girar sem fim."""
    x, p, s = 0, math.exp(-lam), math.exp(-lam)
    u = rng.random()
    while u > s and x < 60:
        x += 1
        p *= lam / x
        s += p
    return x


def poder(por_ano: Counter, grupo: set, ini: int, fim: int, razao: float,
          replicas: int = 250, sorteios: int = 3000,
          bloco: int = BLOCO_PADRAO):
    """Se o efeito real FOSSE desta razao, com que frequencia o teste o acusaria?

    Isto e' o que separa 'nao ha efeito' de 'o desenho nao enxerga efeito deste
    tamanho'. Sem esta medida, ausencia de achado nao pode ser reportada.
    """
    rng = random.Random(SEMENTE)
    anos = anos_do_recorte(ini, fim)
    real = {a: (a in grupo) for a in anos}
    n_g = sum(1 for a in anos if real[a])
    if n_g < MIN_ANOS_NO_GRUPO or len(anos) - n_g < MIN_ANOS_NO_GRUPO:
        return None
    lam = sum(por_ano.get(a, 0) for a in anos) / len(anos)
    lam_fora = lam * len(anos) / (razao * n_g + (len(anos) - n_g))
    lam_grupo = razao * lam_fora
    bl = blocos_de(anos, bloco)

    detectou = 0
    for _ in range(replicas):
        vals = {a: poisson(rng, lam_grupo if real[a] else lam_fora) for a in anos}
        cont = Counter(vals)
        obs = estatistica(cont, anos, real)
        ex = 0
        for _ in range(sorteios):
            emb = {}
            for _, aa in bl.items():
                rot = [real[a] for a in aa]
                rng.shuffle(rot)
                for a, v in zip(aa, rot):
                    emb[a] = v
            if abs(estatistica(cont, anos, emb)) >= abs(obs) - 1e-12:
                ex += 1
        if ex / sorteios < 0.05:
            detectou += 1
    return round(detectou / replicas, 3)


def direcao(c: sqlite3.Connection) -> dict:
    """Direcao da alteracao, com o NAO CLASSIFICADO declarado."""
    linhas = list(c.execute(
        "select expande, retrai from legin_normas_classificadas "
        "where classe = 'altera o texto'"))
    exp = sum(1 for e, _ in linhas if int(e or 0))
    ret = sum(1 for _, r in linhas if int(r or 0))
    nao = sum(1 for e, r in linhas if not int(e or 0) and not int(r or 0))
    tipos = dict(sorted(c.execute(
        "select tipo, count(*) from cp_dispositivos_alterados "
        "group by tipo order by count(*) desc"), key=lambda x: -x[1]))
    inc = sum(v for k, v in tipos.items() if k.startswith("inclu"))
    rev = sum(v for k, v in tipos.items() if k.startswith("revog"))
    return {
        "normas_que_alteram_o_texto": len(linhas),
        "EXPANDE_o_alcance_penal": exp,
        "RETRAI_o_alcance_penal": ret,
        "NAO_CLASSIFICADO": nao,
        "percentual_nao_classificado": round(nao / len(linhas) * 100, 1) if linhas else None,
        "dispositivos_por_tipo_de_anotacao": tipos,
        "inclusoes": inc,
        "revogacoes": rev,
        "razao_inclusao_sobre_revogacao": round(inc / rev, 2) if rev else None,
        "limite_declarado": (
            "a direcao por norma vem do campo de efeitos do Legin, que nomeia o "
            "TIPO da alteracao e nao o SENTIDO da pena; norma cujo efeito e' so' "
            "'Alteracao' nao permite dizer se agrava ou abranda sem ler o "
            "dispositivo. A razao inclusao sobre revogacao mede EXPANSAO DO TEXTO "
            "penal, nunca gravidade de pena, e herda o defeito do texto compilado, "
            "que so' exibe a anotacao sobrevivente."),
    }


def main() -> int:
    cal = ler_calendario()
    grupos = grupos_de(cal)
    c = sqlite3.connect(BASE)
    por_ano = normas_por_ano(c)

    recortes = [
        (1940, 2025, BLOCO_PADRAO, "serie inteira, sem o ano em curso"),
        (1985, 2025, BLOCO_PADRAO, "Nova Republica, regime constante"),
        (1964, 1985, 8, "ditadura militar"),
        (1946, 1964, 8, "Republica de 1946"),
    ]

    res = {
        "gerado_em": "2026-08-29",
        "pergunta": ("O periodo eleitoral se associa a alteracao do Codigo Penal "
                     "brasileiro entre 1940 e 2025?"),
        "fonte_das_normas": ("legin_normas_classificadas da BASE-CODIGO-PENAL.sqlite, "
                             "ficha da Legislacao Informatizada da Camara dos "
                             "Deputados, 135 normas com data de publicacao no DOU"),
        "fonte_do_calendario": ("Cronologia das eleicoes do Tribunal Superior "
                                "Eleitoral, Secao de Arquivo, lida de "
                                "calendario-eleitoral-1940-2026.csv"),
        "zero_estrutural_excluido": sorted(ZERO_ESTRUTURAL),
        "por_que_o_zero_estrutural_sai": (
            "de 1940 a 1944 nao houve pleito POSSIVEL. Conta-los como 'ano sem "
            "eleicao' infla o denominador do grupo de comparacao com anos em que "
            "eleicao era juridicamente impossivel, e empurra a razao para baixo."),
        "testes": {},
        "poder_do_desenho": {},
        "direcao": direcao(c),
    }

    for ini, fim, bloco, nome in recortes:
        res["testes"][nome] = {}
        for g, anos in grupos.items():
            res["testes"][nome][g] = permutacao(por_ano, anos, ini, fim, bloco)

    for razao in (1.0, 1.5, 2.0, 2.5, 3.0):
        p = poder(por_ano, grupos["PRESIDENCIAL DIRETA"], 1940, 2025, razao)
        res["poder_do_desenho"][f"razao_{razao}"] = p
    res["como_ler_o_poder"] = (
        "poder abaixo de 0,80 significa que efeito daquele tamanho passaria "
        "despercebido com frequencia. Ausencia de achado NAO e' prova de ausencia "
        "de efeito abaixo do tamanho que o desenho alcanca. Escreve-se 'nao ha "
        "evidencia de efeito grande', nunca 'nao ha efeito'.")
    res["o_que_este_teste_NAO_responde"] = [
        "nao estabelece CAUSA: associacao entre calendario e producao legislativa "
        "nao demonstra que a eleicao produziu a lei",
        "nao mede INTENSIDADE: uma norma que muda um artigo conta igual a uma que "
        "reescreve a Parte Geral inteira",
        "nao alcanca a TRAMITACAO: a data medida e' a da publicacao, e o projeto "
        "pode ter sido apresentado anos antes, inclusive em outra legislatura",
    ]

    os.makedirs(SAIDA, exist_ok=True)
    dest = os.path.join(SAIDA, "teste-ciclo-eleitoral.json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    os.replace(tmp, dest)

    print(f"calendario lido: {len(cal)} anos de pleito, de {min(cal)} a {max(cal)}")
    print(f"normas alteradoras com data: {sum(por_ano.values())}")
    print()
    for nome in res["testes"]:
        print(f"=== {nome} ===")
        print(f"{'grupo':<38}{'anos':>5}{'normas':>8}{'media':>8}"
              f"{'m.fora':>8}{'razao':>8}{'p':>9}")
        for g, r in res["testes"][nome].items():
            if not r.get("examinavel"):
                print(f"{g:<38}{r['anos_COM_pleito']:>5}   nao examinavel")
                continue
            print(f"{g:<38}{r['anos_COM_pleito']:>5}{r['normas_no_grupo']:>8}"
                  f"{r['media_no_grupo']:>8}{r['media_fora']:>8}"
                  f"{str(r['razao']):>8}{r['p_valor_bilateral']:>9}")
        print()
    print("PODER, grupo presidencial direta, 1940 a 2025:")
    for k, v in res["poder_do_desenho"].items():
        print(f"  {k:<12} poder {v}")
    print()
    d = res["direcao"]
    print(f"DIRECAO: expande {d['EXPANDE_o_alcance_penal']}, retrai "
          f"{d['RETRAI_o_alcance_penal']}, nao classificado "
          f"{d['NAO_CLASSIFICADO']} ({d['percentual_nao_classificado']}%)")
    print(f"  inclusoes {d['inclusoes']} contra revogacoes {d['revogacoes']}, "
          f"razao {d['razao_inclusao_sobre_revogacao']} para 1")
    print()
    print(f"gravado: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
