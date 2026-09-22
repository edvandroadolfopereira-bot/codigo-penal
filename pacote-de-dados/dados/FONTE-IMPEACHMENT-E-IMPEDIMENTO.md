# Impeachment e impedimento presidencial: o ato, e não a notícia

Apurado em 30/08/2026. Arquivo de trabalho.

**Por que ele existe.** O usuário trouxe o tema com links de jornalismo, Wikipédia,
Facebook, Instagram e YouTube. Nenhum desses cita em trabalho acadêmico. Este
arquivo registra o **ato**, com número, data, ementa e publicação oficial, e separa
com precisão o que a fonte primária afirma do que ela não afirma.

---

## 1. Onde não estava, e isso foi medido

A base local `normas-leg`, do portal do Congresso, tem **111.447 registros e dez
espécies**: lei, decreto-lei, medida provisória, lei complementar, emenda
constitucional, lei delegada, constituição, emenda de revisão e ADCT.

**Nenhuma delas é resolução.** Logo os atos de impeachment não podiam estar ali, e
isso agora é medido, não suposto.

## 2. Onde estava

Base de legislação do próprio Senado Federal, pelo portal de dados abertos
`legis.senado.leg.br/dadosabertos`. Foram percorridas **6.574 Resoluções do Senado
Federal**, e nos três anos de interesse há 166, das quais **quatro** tratam da
matéria.

---

## 3. Os quatro atos

| Ato | Data | Publicação original | Página |
|---|---|---|---|
| **RSF nº 20/1955** | 11/11/1955 | Diário do Congresso Nacional, Seção 2, de 17/11/1955 | 2813, col. 1 |
| **RSF nº 21/1955** | 22/11/1955 | Diário do Congresso Nacional, Seção 2, de 22/11/1955 | 1, col. 1 |
| **RSF nº 101/1992** | 30/12/1992 | Diário Oficial da União de 31/12/1992 | 18975, col. 1 |
| **RSF nº 35/2016** | 31/08/2016 | Diário Oficial da União, Edição Extra, de 31/08/2016 | 1, col. 1 |

### O que cada ementa diz, na letra da fonte

**RSF 20/1955**: o Senado, tomando conhecimento da deliberação adotada na mesma
data pela Câmara dos Deputados, *reconhece a existência do impedimento previsto no
artigo 79, parágrafo 1, da Constituição Federal, para cuja solução o mesmo
dispositivo prevê o chamamento do Vice-Presidente do Senado Federal ao exercício da
Presidência da República*.

**RSF 21/1955**: *resolve declarar que permanece o impedimento anteriormente
reconhecido até deliberação em contrário do Congresso Nacional*.

**RSF 101/1992**: *dispõe sobre sanções no processo de impeachment contra o
Presidente da República, Fernando Affonso Collor de Mello*. Origem declarada:
Mesa da Câmara dos Deputados, DIV 12 de 1992.

**RSF 35/2016**: *dispõe sobre sanções no processo de impeachment contra a
Presidente da República, Dilma Vana Rousseff*. Origem declarada: DEN 1/2016,
autor Hélio Pereira Bicudo. Indexação do próprio Senado: *imposição, sanção,
perda, cargo, Presidente da República*.

---

## 4. A distinção que a fonte faz, e que o trabalho tem que respeitar

**São dois institutos diferentes, e o vocabulário do Senado os separa:**

| Ano | Como o ato se descreve | Natureza |
|---|---|---|
| 1955 | **impedimento** do art. 79, §1º, da Constituição de 1946 | declaração de impedimento, com chamamento do substituto |
| 1992 e 2016 | **sanções no processo de impeachment** | julgamento por crime de responsabilidade, com perda do cargo |

Tratar os quatro como "impeachment" apaga essa diferença. O trabalho escreve
**impeachment** para 1992 e 2016 e **impedimento** para 1955, e diz por quê.

**E 1955 é uma crise só, com dois atos separados por onze dias**, e não dois
episódios independentes. Codificar 1955 como dois eventos contaria duas vezes a
mesma ruptura.

---

## 5. O que a fonte primária NÃO afirma, e por isso eu também não

**As duas resoluções de 1955 não nomeiam ninguém.** A ementa da RSF 20 fala em
impedimento sem dizer de quem, e a da RSF 21 fala em *impedimento anteriormente
reconhecido*, também sem nome.

A atribuição corrente, que dá a RSF 20 a Carlos Luz e a RSF 21 a Café Filho, **não
se lê nas ementas**. Ela está no Diário do Congresso Nacional, Seção 2, de
17/11/1955 e de 22/11/1955, cujas páginas estão identificadas acima e **não foram
lidas**.

**Portanto**: o trabalho afirma os atos, as datas e a natureza, e **não atribui
nome de presidente a cada resolução de 1955** enquanto o Diário não for lido.

O inteiro teor tampouco foi obtido: os endereços de texto do Senado responderam
404 para os quatro atos, e a página da norma é montada por código no navegador.
O campo `temTexto` da própria base declara **S** para os quatro, então o texto
existe no sistema do Senado e o que falta é o caminho para ele.

---

## 6. O que isto muda no teste

O grupo de impeachment deixa de estar marcado como `fonte_nao_conferida`. Os anos
passam a ser **1955, 1992 e 2016**, cada um com o ato que o estabelece.

**O limite de poder continua inteiro e vai escrito ao lado do resultado**: são três
anos contra oitenta e um, e no recorte de 1990 em diante são dois contra trinta e
quatro, caso em que a própria função **recusa testar**, porque abaixo de três de
cada lado não há o que permutar.
