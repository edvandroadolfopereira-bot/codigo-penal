# Propostas de governo e falas de quem legisla: o que existe, medido em 29/08/2026

Documento de trabalho. Cada linha traz o código HTTP medido na data, e não
impressão sobre disponibilidade.

---

## 1. O marco legal, conferido na fonte, e ele desloca o recorte

A obrigação de apresentar proposta de governo no pedido de registro está no
**art. 11, § 1º, inciso IX, da Lei nº 9.504, de 30 de setembro de 1997**:

> IX - propostas defendidas pelo candidato a Prefeito, a Governador de Estado e a
> Presidente da República.

**O inciso IX foi INCLUÍDO PELA LEI Nº 12.034, DE 2009.** Não consta da redação
original de 1997. Conferido no texto compilado do Planalto em 29/08/2026,
`planalto.gov.br/ccivil_03/leis/l9504.htm`, HTTP 200, 609.835 bytes, arquivo
gravado em `planalto-lei-9504-1997.html`.

**Consequência para a pesquisa, e ela é dura:**

| Período | Existe proposta de governo oficialmente registrada? |
|---|---|
| 1947 a 2009 | **Não.** Não havia obrigação legal de apresentá-la à Justiça Eleitoral |
| 2010 em diante, Presidente e Governador | Sim, por força do inciso IX |
| 2012 em diante, Prefeito | Sim, por força do inciso IX |

Isto não significa que não houvesse programa de governo antes de 2010. Significa
que **não há registro oficial centralizado dele**, e que qualquer levantamento
anterior a 2010 se apoia em fonte partidária, em imprensa ou em acervo, nunca em
registro da Justiça Eleitoral.

---

## 2. O que respondeu, com o número

| Fonte | Endereço | HTTP | Cobertura medida |
|---|---|---|---|
| TSE, DivulgaCandContas, candidaturas | `divulgacandcontas.tse.jus.br/divulga/rest/v1/` | **200** | anos eleitorais **2004 a 2026**, doze pleitos |
| Senado, discursos de plenário | `legis.senado.leg.br/dadosabertos/plenario/lista/discursos/` | **200** | **vazio até 1999**, com dados de **2000 em diante** |
| Câmara, Dados Abertos, proposições | `dadosabertos.camara.leg.br/api/v2/proposicoes` | **200** | busca por palavra-chave funciona |
| Planalto, texto compilado | `planalto.gov.br/ccivil_03/` | **200** | 609.835 bytes na Lei 9.504 |
| Hemeroteca Digital, Biblioteca Nacional | `memoria.bn.gov.br` | **200** | a medir |
| Senado, Diário do Congresso | `www25.senado.leg.br/web/atividade/diarios` | **200** | a medir |

### Detalhe do que a base de discursos do Senado entrega

O XML traz `TextoIntegral` e `TextoIntegralTxt`, isto é o **texto completo do
pronunciamento**, mais `NomeAutor`, `Partido`, `DataSessao`, `Indexacao`,
`Resumo`, `PaginaInicial` e `FontePublicacao`. Uma janela de um mês em 2025
devolveu 529.089 bytes com 246 textos integrais.

Medição do alcance, uma janela de junho por década:

| Janela | HTTP | Bytes | Sessões |
|---|---|---|---|
| junho de 1950 | 200 | 543 | **zero**, `<Sessoes/>` vazio |
| junho de 1960 | 200 | 543 | zero |
| junho de 1970 | 200 | 543 | zero |
| junho de 1980 | 200 | 543 | zero |
| junho de 1990 | 200 | 543 | zero |
| junho de 2000 | 200 | 446.947 | com dados |
| junho de 2010 | 200 | 672.900 | com dados |
| junho de 2020 | 200 | 275.037 | com dados |
| junho de 2025 | 200 | 529.089 | com dados, 1 citação a Código Penal |

**A base começa em 2000.** Resposta 200 com corpo vazio não é ausência de sessão
em 1950: é ausência de dado na base, e assim se escreve.

---

## 3. O que está bloqueado, com o erro medido

| Fonte | O que traria | Erro em 29/08/2026 |
|---|---|---|
| **Biblioteca da Presidência da República** | **Mensagens ao Congresso Nacional**, anuais, e discursos presidenciais desde a República | `ConnectionResetError`, em `http` e em `https` |
| `gov.br/planalto` | portal da Presidência | **HTTP 401** |
| TSE, arquivo da proposta de governo | o PDF da proposta de cada candidato | endpoint de detalhe devolve **200 com corpo vazio** sem cabeçalho de origem, e **403** com ele |
| ABNT Catálogo | vigência das NBR | tela de validação que não avança |

A Biblioteca da Presidência é a perda mais séria. As **Mensagens ao Congresso**
são o documento em que o Presidente expõe ao Legislativo, todo ano, o que pretende
em matéria legislativa. É a fonte oficial mais próxima de programa de governo para
o período de 1947 a 2009, justamente o trecho em que a proposta de campanha não
tem registro.

---

## 4. Fontes de imprensa, e o critério para usá-las

O orientando autorizou jornal confiável. O critério que se adota, e que precisa
estar escrito no trabalho:

1. **Jornal serve para datar declaração e atribuir autoria de fala**, nunca para
   estabelecer o conteúdo de norma. Conteúdo de norma se lê no Diário Oficial.
2. **Prefere-se o acervo digitalizado com imagem da página**, porque permite citar
   jornal, data, página e coluna. A Hemeroteca Digital da Biblioteca Nacional faz
   isso e respondeu HTTP 200.
3. **Declaração de político é fato sobre a declaração**, e não sobre a intenção.
   Registra-se que ele disse, quando e onde, e não o que ele queria.

---

## 5. O que proponho fazer, sem custo de coleta nova desnecessário

| # | Ação | Fonte já testada | Rende o quê |
|---|---|---|---|
| 1 | Varrer os discursos do Senado de 2000 a 2026 procurando menção ao Código Penal | API que já responde 200 | fala datada, com autor, partido e texto integral, cruzável com o calendário eleitoral |
| 2 | Varrer as proposições da Câmara por palavra-chave penal, ano a ano | API que já responde 200 | o denominador que falta, isto é projeto apresentado e não aprovado |
| 3 | Baixar as candidaturas do DivulgaCand de 2004 a 2026 | API que já responde 200 | quem concorreu, por partido e cargo, para ligar autoria de projeto a disputa eleitoral |

Nenhuma das três exige fonte nova. As três usam endpoint já medido nesta data.

---

## 6. O que preciso que seja buscado, porque aqui está bloqueado

| # | O que | Onde | Por quê |
|---|---|---|---|
| A | **Mensagens ao Congresso Nacional**, de 1947 em diante | Biblioteca da Presidência da República | única fonte oficial de programa de governo antes de 2010 |
| B | **Propostas de governo** dos candidatos a Presidente de 2010, 2014, 2018, 2022 e 2026 | TSE, DivulgaCandContas, aba do candidato | o registro oficial existe desde a Lei 12.034/2009 |
| C | **Programas partidários** registrados no TSE | TSE, órgãos partidários | ideologia declarada, que é diferente de ideologia atribuída |
| D | Resultados eleitorais por ano | TSE | composição partidária de cada legislatura |
