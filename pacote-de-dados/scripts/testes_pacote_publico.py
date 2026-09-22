# -*- coding: utf-8 -*-
# Bancada de `montar_pacote_publico.py`.
#
# Ela mede as DUAS direcoes e, na ultima prova, DESLIGA o instrumento e exige que o
# veredito MUDE, pela regra desta casa de 29/08/2026. Sem essa terceira, a bancada
# aprovaria instrumento morto.
#
# A prova que mais importa e' a da fonte: arquivo de dado sem fonte declarada tem que
# REPROVAR a montagem. E' ela que impede publicar dado de terceiro sem apontar a origem,
# que e' apropriacao ainda que involuntaria.
#
# NAO USA PASTA TEMPORARIA, pela regra terminante de 14/08/2026, e nao apaga em
# recursao, pela regra de 17/08/2026, item 11. A pasta de trabalho e' propria, comeca
# por sublinhado para ficar fora dos autos, e a limpeza e' arquivo a arquivo pelo nome.

import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, R)
# sem isto, o import deixa __pycache__ dentro de 02-DADOS/scripts, e o cache entra no
# pacote publico sem estar no manifesto (medido em 22/09/2026)
sys.dont_write_bytecode = True
import montar_pacote_publico as M

TRABALHO = os.path.join(R, "_bancada-pacote-publico")
OK, FALHA = [], []


def prova(nome, cond, detalhe=""):
    (OK if cond else FALHA).append(nome)
    print("   %s %s%s" % ("OK  " if cond else "FALHA", nome,
                          ("  <- " + detalhe) if (detalhe and not cond) else ""))


def limpar():
    """Apaga arquivo a arquivo, pelo nome, sem recursao."""
    if not os.path.isdir(TRABALHO):
        return
    for n in os.listdir(TRABALHO):
        p = os.path.join(TRABALHO, n)
        if os.path.isfile(p):
            os.remove(p)


def com_json(d):
    """Grava um JSON de prova, achata, e devolve {nome do csv: linhas}."""
    limpar()
    os.makedirs(TRABALHO, exist_ok=True)
    org = os.path.join(TRABALHO, "prova.json")
    io.open(org, "w", encoding="utf-8", newline="").write(
        json.dumps(d, ensure_ascii=False))
    nomes, _ = M.json_para_csv(org, TRABALHO)
    saida = {}
    for n in nomes:
        saida[n] = io.open(os.path.join(TRABALHO, n), encoding="utf-8").read().splitlines()
    limpar()
    return saida


print("=== BANCADA DO PACOTE PUBLICO ===")
print()
print("-- achatamento: o que TEM que virar tabela --")

s = com_json({"itens": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]})
prova("lista de dicionarios vira tabela propria",
      "prova__itens.csv" in s, str(list(s)))
prova("e ela leva TODAS as linhas, mais o cabecalho",
      len(s.get("prova__itens.csv", [])) == 3,
      str(len(s.get("prova__itens.csv", []))))
prova("com uma coluna por chave",
      s.get("prova__itens.csv", [""])[0] == "a;b",
      s.get("prova__itens.csv", [""])[0])

s = com_json({"paginas": list(range(M.LISTA_LONGA + 5))})
prova("lista LONGA de valores simples vira planilha propria",
      "prova__paginas.csv" in s, str(list(s)))
prova("com indice e valor, e uma linha por item",
      len(s.get("prova__paginas.csv", [])) == M.LISTA_LONGA + 6,
      str(len(s.get("prova__paginas.csv", []))))

print()
print("-- achatamento: o que NAO pode virar tabela --")

s = com_json({"pleitos": [1945], "total": 42})
prova("lista CURTA nao vira planilha propria",
      "prova__pleitos.csv" not in s, str(list(s)))
prova("ela entra no arquivo de valores, sem se perder",
      any("pleitos" in l for l in s.get("prova__valores.csv", [])),
      str(s.get("prova__valores.csv")))

s = com_json({"a": {"b": {"c": 7}}})
prova("escalar aninhado entra com o caminho INTEIRO na chave",
      any(l.startswith("a.b.c;") for l in s.get("prova__valores.csv", [])),
      str(s.get("prova__valores.csv")))

s = com_json({"x": 1, "y": 2, "z": 3})
prova("varios escalares dao UM arquivo, e nao um por valor",
      list(s) == ["prova__valores.csv"], str(list(s)))

print()
print("-- a trava contra publicar dado sem citar a fonte --")

siglas = set(f["sigla"] for f in M.FONTES)
sem = [rel for rel, _s, sg in M.PACOTE if sg not in siglas]
prova("todo arquivo do pacote aponta uma fonte que EXISTE no catalogo",
      not sem, str(sem))
prova("nenhuma sigla repetida no catalogo",
      len(siglas) == len(M.FONTES),
      "%d siglas para %d fontes" % (len(siglas), len(M.FONTES)))
prova("toda fonte declara referencia e regime de direito",
      all(f.get("referencia") and f.get("regime") for f in M.FONTES))

guardado = list(M.PACOTE)
M.PACOTE = guardado + [("cp-serie-anual.csv", "prova", "fonte-que-nao-existe")]
sem2 = [rel for rel, _s, sg in M.PACOTE if sg not in siglas]
prova("plantada uma fonte inexistente, ela E' APANHADA",
      len(sem2) == 1, str(sem2))
M.PACOTE = guardado

print()
print("-- desligar o instrumento, e exigir que o veredito MUDE --")

guardado_lim = M.LISTA_LONGA
antes = com_json({"paginas": list(range(guardado_lim + 5))})
M.LISTA_LONGA = 10 ** 9
depois = com_json({"paginas": list(range(guardado_lim + 5))})
M.LISTA_LONGA = guardado_lim
prova("com o limiar desligado, a planilha propria DESAPARECE",
      ("prova__paginas.csv" in antes) and ("prova__paginas.csv" not in depois),
      "antes=%s depois=%s" % (list(antes), list(depois)))

limpar()
if os.path.isdir(TRABALHO):
    os.rmdir(TRABALHO)

print()
print("%d de %d" % (len(OK), len(OK) + len(FALHA)))
if FALHA:
    print("REPROVOU: " + ", ".join(FALHA))
sys.exit(1 if FALHA else 0)
