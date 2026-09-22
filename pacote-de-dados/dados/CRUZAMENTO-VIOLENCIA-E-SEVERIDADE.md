# O cruzamento com os anuários do Fórum, feito em 30/08/2026

Arquivo de trabalho. Este é o objetivo específico que o trabalho declarava como
pendente, e que agora tem resposta com limite declarado.

---

## 1. O que havia no disco, medido antes de usar

| | |
|---|---|
| itens do acervo do Fórum | 242 |
| dos quais do tipo Anuário | **23**, e não vinte |
| arquivos | 578, somando 1.908,7 MB |
| por tipo | 437 PDF, 79 JPEG, 26 XLSX, 16 PNG, 7 ZIP |
| **marcadores de nuvem** | **578 de 578** |

Todos os arquivos eram marcador de nuvem, e abrir hidrata. Aqui isso foi
necessário e intencional, porque a planilha é o que traz a série.

## 2. Defeito de catalogação da fonte, medido e declarado

O arquivo de resumo criptográfico `e40c53ff` está catalogado em **três itens** do
acervo, sob quatro nomes de arquivo diferentes.

Um desses itens o atribui ao **10º Anuário, de 2016**, quando o conteúdo é o **16º
Anuário, de 2022**: a série dentro dele vai de 2011 a 2021, o que é impossível para
uma publicação de 2016.

Conferido pelos quatro resumos criptográficos, todos idênticos. **Por isso a série
canônica sai da edição de 2026, e não de pasta rotulada por ano.**

## 3. A série de violência, e o que ela é

**Mortes Violentas Intencionais**, do 20º Anuário, edição de 2026, tabela da série
histórica. A categoria soma homicídio doloso, latrocínio, lesão corporal seguida de
morte e morte decorrente de intervenção policial.

A própria fonte declara que a categoria só passou a ser calculada em 2013, e que
2012 foi computado retroativamente.

### As revisões entre edições, medidas

A série foi extraída de **nove edições** e comparada. O Fórum revisa números:

| Ano | Valor mais antigo | Valor atual | Diferença |
|---|---|---|---|
| 2018 | 57.358 | 57.592 | 234 |
| 2020 | 50.033 | 50.448 | 415 |
| 2019 | 47.796, depois 47.742 | 47.765 | revisado duas vezes |
| 2015 | 58.459 | 58.437 | 22 |

Usar a edição mais recente não é preferência: é a única forma de trabalhar com a
série que o próprio órgão sustenta hoje.

---

## 4. O cruzamento

Janela comum: **2012 a 2025, catorze anos.** Ela é curta, e isso decide a leitura.

| Ano | MVI, Brasil | Agravamentos |
|---|---|---|
| 2012 | 54.694 | 3 |
| 2013 | 55.844 | 0 |
| 2014 | 59.739 | 1 |
| 2015 | 58.437 | 0 |
| 2016 | 61.600 | 1 |
| 2017 | **64.079** | 0 |
| 2018 | 57.592 | 3 |
| 2019 | 47.765 | 0 |
| 2020 | 50.448 | 0 |
| 2021 | 48.286 | **22** |
| 2022 | 47.963 | 1 |
| 2023 | 46.441 | 1 |
| 2024 | 44.220 | 3 |
| 2025 | **40.775** | 8 |

**A violência caiu 25,4% no período**, do pico de 64.079 em 2017 para 40.775 em
2025. **E o Código continuou sendo agravado**, com 43 eventos no mesmo intervalo.

### A associação, e por que a primeira leitura estaria errada

| Especificação | Pearson | Spearman | n |
|---|---|---|---|
| nível, com tendência | **-0,356** | -0,402 | 14 |
| **primeira diferença, sem tendência** | **-0,104** | -0,229 | 13 |
| primeira diferença, com defasagem de um ano | +0,277 | +0,130 | 12 |

**O -0,356 do nível é artefato de tendência.** Duas séries que caminham em sentidos
opostos ao longo de catorze anos se correlacionam por construção, e não por
relação.

Removida a tendência pela primeira diferença, **a associação praticamente
desaparece**. Com defasagem de um ano ela troca de sinal e continua fraca.

---

## 5. O achado que não depende de poder estatístico

Este é o ponto, e ele é composicional, não inferencial.

**Os 22 agravamentos de 2021, que dominam a série inteira, foram medidos um a um:**

| Norma | Eventos | Sobre o quê |
|---|---|---|
| Lei n. 14.133/2021 | **11** | crimes em licitação e contratos, arts. 337-E a 337-O |
| Lei n. 14.197/2021 | **8** | crimes contra o Estado Democrático, arts. 359-I a 359-R |
| Lei n. 14.155/2021 | 2 | invasão de dispositivo e estelionato eletrônico |
| Lei n. 14.188/2021 | 1 | violência psicológica contra a mulher |

**Dezenove dos vinte e dois não versam criminalidade violenta.** São crime de
licitação e crime político.

Ou seja: **o maior episódio de agravamento penal da janela não responde a
criminalidade violenta**, e isso se afirma sem depender de correlação nenhuma,
porque sai da leitura do que cada norma criou.

---

## 6. A resposta à última pergunta do projeto

A pergunta era se faz sentido ampliar a tipificação penal diante da criminalidade
violenta brasileira. O trabalho respondia que **não responde**.

Agora responde, e com este teor:

**A resposta legislativa medida não acompanha a série de violência.** A violência
caiu vinte e cinco por cento entre 2012 e 2025, o Código foi agravado quarenta e
três vezes no mesmo intervalo, e removida a tendência não há associação entre as
duas séries.

**E a composição do agravamento afasta a hipótese de resposta à violência**: o ano
de maior agravamento foi dominado por crime de licitação e crime contra o Estado
Democrático.

### O que esta resposta NÃO afirma

1. **Não afirma que a lei causou a queda da violência**, nem o contrário. Com n de
   catorze e sem desenho de identificação, causa não se afirma.
2. **Não mede dissuasão.** Mede se as duas séries andam juntas.
3. **Não afirma que ampliar tipificação seja inútil.** Afirma que a ampliação
   medida não se explica pela série de violência.
4. **A janela é curta e o poder é baixo.** Ausência de associação detectada, com n
   de treze, não é prova de ausência de associação.
5. A série do Fórum começa em 2012, e a de agravamento é densa desde 1990. A janela
   comum é a mais curta das duas.
