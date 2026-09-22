# -*- coding: utf-8 -*-
# Extrai, das DEZESSETE edicoes do Anuario Brasileiro de Seguranca Publica em PDF, toda
# tabela que traga uma linha do Brasil com numero grande.
#
# POR QUE POSICIONAL, e nao por texto corrido: a extracao de texto de PDF perde a
# estrutura da tabela, e as linhas do Brasil que aparecem no texto plano sao TITULO de
# tabela, do tipo 'Brasil - 2005-2008', e nao linha de dado. Medido em 30/08/2026 nas
# seis primeiras edicoes.
#
# A leitura e' pagina a pagina, da primeira a ultima de cada edicao, sem amostragem.
# O progresso vai para o log, porque a passagem leva minutos e barra que nao mede nao
# serve, pela regra desta casa de 03/08/2026.

import io
import os
import re
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
ACERVO = os.path.join(os.environ.get("USERPROFILE", ""), "OneDrive",
                      "Biblioteca-Academica-Direito", "forum-seguranca-publica")
SAIDA = os.path.join(R, "analise-cientifica", "_anuarios-tabelas-brasil.txt")
LOG = os.path.join(R, "analise-cientifica", "extrair_tabelas_log.txt")

NUM = re.compile(r"^\s*\d{1,3}(\.\d{3})+\s*$|^\s*\d{4,6}\s*$")


def edicoes():
    a = {}
    for d, _, arq in os.walk(ACERVO):
        for x in arq:
            m = re.match(r"^(\d{4})_anuario_brasileiro_seguranca_publica\.pdf$", x)
            if m:
                a[int(m.group(1))] = os.path.join(d, x)
    return a


def main():
    import pymupdf
    anu = edicoes()
    if not anu:
        print("FALHA REAL: nenhuma edicao em PDF achada em " + ACERVO)
        return 1
    t0 = time.time()
    L, achadas, paginas = [], 0, 0
    log = io.open(LOG, "w", encoding="utf-8", newline="")
    log.write("extracao das tabelas do Brasil, %d edicoes\n" % len(anu))
    for ed in sorted(anu):
        doc = pymupdf.open(anu[ed])
        n_tab = 0
        for i in range(doc.page_count):
            paginas += 1
            try:
                tabs = doc[i].find_tables()
            except Exception:
                continue
            for tb in tabs.tables:
                try:
                    dados = tb.extract()
                except Exception:
                    continue
                if not dados:
                    continue
                util = False
                for linha in dados:
                    vals = [("" if x is None else str(x).replace(chr(10), " ").strip())
                            for x in linha]
                    if vals and vals[0].lower().startswith("brasil") and \
                            any(NUM.match(v) for v in vals[1:]):
                        util = True
                if not util:
                    continue
                n_tab += 1
                achadas += 1
                L.append("=" * 78)
                L.append("EDICAO %d | pagina %d | %d linhas x %d colunas"
                         % (ed, i + 1, len(dados), len(dados[0])))
                for linha in dados:
                    vals = [("" if x is None else str(x).replace(chr(10), " ").strip())
                            for x in linha]
                    if any(v for v in vals):
                        L.append("   " + " | ".join(vals))
        doc.close()
        msg = ("edicao %d: %d tabela(s) com o Brasil e numero | %d paginas lidas ate' "
               "aqui | %.0f s" % (ed, n_tab, paginas, time.time() - t0))
        print(msg)
        log.write(msg + "\n")
        log.flush()
    log.close()
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(chr(10).join(L))
    print()
    print("edicoes lidas : %d, de %d a %d" % (len(anu), min(anu), max(anu)))
    print("paginas lidas : %d" % paginas)
    print("tabelas uteis : %d" % achadas)
    print("segundos      : %.0f" % (time.time() - t0))
    print("gravado       : " + SAIDA)
    if achadas == 0:
        print("FALHA REAL: zero tabela achada. Isso e' criterio errado, e nao ausencia.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
