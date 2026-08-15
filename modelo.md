# Colunas de interesse no SIM

## Tempo
`DTOBITO`
    Data do óbito no formato DDMMAAAA. Desse atributo deriva apenas o **ano** do óbito — a análise será feita somente por ano, sem granularidade de dia/mês. A dimensão tempo é simplificada para conter apenas o ano.

## Identificação da mulher
`IDADE`
    Idade possui dois subcampos: o primeiro dígito indica a unidade de medida da idade (1 = minuto, 2 = hora, 3 = mês, 4 = ano, 5 = idade maior que 100 anos); o segundo subcampo indica a quantidade de unidades do primeiro.
    Esse atributo compõe a identificação da mulher e dele deriva a dimensão faixa_etaria.

`SEXO`
    Masculino = M,1 ; Feminino = F,2 ; Ignorado = I, 0, 9
    Esse campo serve para verificar se há registros de pessoas trans com óbitos maternos. 
    **Sem dimensão própria**: `SEXO` é usado apenas como critério de filtro (mulheres = `F`) e não entra na tabela-fato.

`RACACOR`
    1 – Branca; 2 – Preta; 3 – Amarela; 4 – Parda; 5 – Indígena; 9 – Ignorado
    Esse atributo compõe a identificação da mulher e dele deriva a dimensão raça.

## Municipio
`CODMUNRES`
    Codigo do municipio com até 7 dígitos, porém maioria dos registros possui 6 dígitos. 
    Desse atributo deriva a dimensão municipio_residencia.

`CODMUNOCOR`
    Codigo do municipio, porém maioria dos registros possui 6 dígitos. 
    Desse atributo deriva a dimensão municipio_ocorrencia.

## Circunstâncias do óbito
`TPMORTEOCO`
    Situacao gestacional em que ocorreu o obito.
    Códigos >> 1: na gravidez; 2: no parto; 3: no abortamento; 4: até 42 dias após o término do parto; 5: de 43 dias a 1 ano após o término da gestação; 8: não ocorreu nestes períodos; 9: ignorado.
    Esse atributo compõe as circunstancias do óbito da mulher e dele deriva a `Dim_MomentoGravidez` (papel `id_momento_gravidez` na tabela-fato).

`ASSISTMED`
    Identificador se a mulher recebeu assistencia medica. Códigos >> 1 – sim; 2 – não; 9 – ignorado
    Normalizado para o booleano `recebeu_assistencia_medica` na tabela-fato: `1` → `True` (recebeu); `2`/`9`/vazio → `False` (não recebeu). Não gera dimensão.

`CAUSABAS`
    CIDs informados como causa básica do óbito. Representa a causa inicial geralmente.
    Esse atributo compõe as circunstancias do óbito da mulher e dele deriva a `Dim_CID` (papel `id_causa_basica` na tabela-fato, NOT NULL).

`CAUSABAS_O`
    Causa básica original do óbito, informado antes da resseleção.
    Esse atributo compõe as circunstancias do óbito da mulher e dele deriva a `Dim_CID` (papel `id_causa_original` na tabela-fato, nullable).

`LINHAA`, `LINHAB`, `LINHAC`, `LINHAD`, `LINHAII`
    CIDs das demais linhas do atestado de óbito (causas antecedentes, consequenciais e Parte II). No arquivo do SIM os valores vêm prefixados com `*` (ex: `*R570`, `*I319`, `*X999`) e vazios quando não preenchidos.
    Não geram dimensões. Derivam o booleano `possui_cid_obstetrico_secundario` na tabela-fato: `True` se **qualquer um** dos cinco contiver um CID obstétrico (Capítulo XV da CID-10, códigos `O00`–`O99` — código iniciado por `O` após o prefixo `*`).

## Investigação dos óbitos
`NUDIASOBCO`
    Diferença entre a data óbito e a data conclusão da investigação, em dias.

`TPNIVELINV`
    Tipo de nível investigador. Códigos >> E: Estadual; R: Regional; M: Municipal

`TPOBITOCOR`
    Códigos >> 1: Durante a gestação; 2: Durante o abortamento; 3: Após o abortamento; 4: No parto ou até 1 hora após o parto; 5: No puerpério até 42 dias após o parto; 6: Entre 43 dias e até 1 ano após o parto; 7: A investigação não identificou o momento do óbito; 8: Mais de um ano após o parto; 9: O óbito não ocorreu nas circunstancias anteriores; Nulo/Em Branco: Não investigado
    Deriva a `Dim_MomentoGravidez` (papel `id_momento_gravidez_pos_investigacao` na tabela-fato).

`TPRESGINFO`
    Informa se a investigação permitiu o resgate de alguma causa de óbito não informado, ou a correção de alguma antes informada. Códigos >> 01: Não acrescentou nem corrigiu informação; 02: Sim, permitiu o resgate de novas informações; 03: Sim, permitiu a correção de alguma das causas informadas originalmente.

## Estabelecimento de Saúde
`LOCOCOR`
    Local em que ocorreu o óbito. 1 – hospital; 2 – outros estabelecimentos de saúde; 3 – domicílio; 4 – via pública; 5 – outros; 6 - aldeia indígena; 9 – ignorado. 
    Esse atributo compõe a dimensão `Dim_LocalOcorrencia`.

`CODESTAB`
    Codigo CNES do Estabelecimento de Saúde em que ocorreu o óbito. 
    Esse atributo compõem a dimensão estabelecimento_de_saúde.

Essa dimensão estabelecimento_de_saúde terá uma hierarquia "snowflake" com os dados dos estabelecimentos de saúde que vamos pegar na base do CNES - Cadastro Nacional dos Estabelecimentos de Saúde. A granularidade mais baixa refere-se aos codigos dos estabelecimentos; o local do óbito (`LOCOCOR`) fica na dimensão `Dim_LocalOcorrencia` e os demais dados oriundos do CNES - ver lista de campos abaixo.

```
Campos do CNES: 
CO_CNES - equivalente a CODESTAB no SIM - essa é a chave de ligação entre os dados
NO_FANTASIA
CO_IBGE
TP_GESTAO
CO_ESFERA_ADMINISTRATIVA
TP_UNIDADE
NO_BAIRRO
CO_NATUREZA_JUR
CO_AMBULATORIAL_SUS
```

## Decisões de EDA — Colunas de Investigação (validado em `exploracoes/analisa_variaveis_dim.ipynb`)

- **`MORTEPARTO`**: **descartada**. Preenchida quase exclusivamente fora do universo de mulheres em idade fértil (idade em dias/meses/horas ou mediana de 2 anos quando em anos) — pertence à ficha de investigação de óbito infantil/fetal, não materno.
- **`DTINVESTIG`, `DTCONINV`**: **descartadas**. Datas multiplicarão o número de valores únicos de dimensões na tabela-fato. `NUDIASOBCO` é suficiente para realizarmos análise sobre a celeridade das investigações.
- **`FONTEINV`**: **descartada**. Representa a investigação de óbito do SIM **em geral** (qualquer óbito investigável, não só materno). 
- **`NUDIASOBCO`, `TPNIVELINV`, `TPOBITOCOR`**: mantidas — ~99.8% dos preenchimentos em todo o SIM já ocorrem dentro do universo `mif`, confirmando que são específicas da investigação de óbito materno.
- **`TPRESGINFO`**: mantida, provável indicativo de que é uma morte materna, quase 100% dentro do `mif` (onde representa cerca de ~4.5%).
- **`OBITOGRAV`, `OBITOPUERP`**: **descartadas**. O SIM aplica essas perguntas como triagem rotineira em qualquer óbito feminino (inclusive fora da idade fértil, com idade média ≈58 anos).
- **`CAUSAMAT`**: **descartada**. Pouco preenchimento em geral, mesmo dentro do `mif`.
- **`NUDIASOBCO`**: outliers definidos como `> 1460` dias (4 anos) — apenas 1 registro removido. Normalizada em faixas para a dimensão `Dim_FaixaDiasInvestigacao`: `0-120`, `121-240`, `241-365`, `366-730`, `730+` dias.


# Modelo Dimensional para Análise de Mortalidade Materna

**TL;DR** — Modelo dimensional snowflake com fato sendo a quantidade de óbitos de cada dimensão.

## Decisões de Design
- **Granularidade**: Fato agregado (contagem por combinação única de dimensões)
- **Schema**: Snowflake (hierarquias normalizadas)

### Decisão: Município como Role-Playing Dimension
- `Dim_Municipio` é reutilizada com papel duplo na fato: `id_municipio_ocorrencia` (NOT NULL) e `id_municipio_residencia` (nullable).
- `id_municipio_estabelecimento` **não** entra como FK na tabela-fato; é carregado na `Dim_EstabelecimentoSaude` (via `CO_IBGE` do CNES) e **pode** referenciar `Dim_Municipio`.

### Decisão: Estabelecimento de Saúde (atributos do CNES)
- `CO_AMBULATORIAL_SUS` entra **direto na tabela-fato**, normalizado para booleano (`"SIM"` → `True`; demais → `False`). É uma flag de baixo custo e congela o valor no momento do óbito.
- `Dim_EstabelecimentoSaude` contém: `CO_CNES`, `NO_FANTASIA`, `CO_IBGE`, `CO_ESFERA_ADMINISTRATIVA`, `TP_UNIDADE`, `NO_BAIRRO` e `CO_NATUREZA_JUR`.
  - Obs.: "CO_NATUREZA_JURIDICA" (terminologia usada nas decisões) corresponde ao campo `CO_NATUREZA_JUR` na base CNES.
- Os demais campos do CNES **não** entram no modelo por ora.

### Decisão: CID como Role-Playing Dimension
- `Dim_CID` é reutilizada com papel duplo na fato: `id_causa_basica` (NOT NULL, derivada de `CAUSABAS`) e `id_causa_original` (nullable, derivada de `CAUSABAS_O`).
- As 2 FKs apontam para a mesma `Dim_CID` — *role-playing dimension*

### Decisão: CID obstétrico secundário (LINHAA–LINHAII)
- `LINHAA`, `LINHAB`, `LINHAC`, `LINHAD` e `LINHAII` não geram dimensão; derivam apenas o booleano `possui_cid_obstetrico_secundario` ("PossuiCidObstetricoSecundario") na fato.
- Regra: `True` se **qualquer um** dos cinco campos contiver CID do Capítulo XV da CID-10 (`O00`–`O99`, i.e., código iniciado por `O` após o prefixo `*` presente no arquivo do SIM); `False` caso contrário.

### Decisão: Momento da Gravidez como Role-Playing Dimension
- `Dim_MomentoGravidez` é reutilizada com papel duplo na fato: `id_momento_gravidez` (derivada de `TPMORTEOCO`) e `id_momento_gravidez_pos_investigacao` (nullable, derivada de `TPOBITOCOR`).
- As 2 FKs apontam para a mesma `Dim_MomentoGravidez` — *role-playing dimension*

## Modelo Dimensional (Snowflake)

**Hierarquia Geográfica (snowflake):**
- `Dim_Regiao`: id_regiao (PK), nome_regiao (Norte, Nordeste, Sudeste, Sul, Centro-Oeste)
- `Dim_UF`: id_uf (PK), nome_uf, sigla_uf, id_regiao (FK → Dim_Regiao)
- `Dim_Municipio`: id_municipio (PK), codigo_ibge (7 dígitos), nome_municipio, id_uf (FK → Dim_UF)

**Hierarquia Estabelecimentos de Saúde (snowflake):**
- `Dim_EstabelecimentoSaude`: id_estabelecimento (PK), codigo_cnes (`CO_CNES`), nome_fantasia (`NO_FANTASIA`), codigo_ibge (`CO_IBGE`), id_municipio (FK → Dim_Municipio, via `CO_IBGE` do CNES), esfera_administrativa (`CO_ESFERA_ADMINISTRATIVA`), tipo_unidade (`TP_UNIDADE`), bairro (`NO_BAIRRO`), natureza_juridica (`CO_NATUREZA_JUR`)

- `Dim_Tempo`: id_tempo (PK), ano (derivado de `DTOBITO`) — simplificada: sem dia, mês, trimestre ou semestre
- `Dim_FaixaEtaria`: id_faixa_etaria (PK), faixa ("10-14","15-19",...,"45-49"), idade_min, idade_max
- `Dim_RacaCor`: id_raca_cor (PK), codigo (1,2,3,4,5,9), descricao (Branca,Preta,Amarela,Parda,Indígena,Ignorado)
- `Dim_LocalOcorrencia`: id_local_ocorrencia (PK), codigo (1,2,3,4,5,6,9), descricao (Hospital,Outros est. saúde,Domicílio,Via pública,Outros,Aldeia indígena,Ignorado) — derivada de `LOCOCOR`
- `Dim_MomentoGravidez` (role-playing): id_momento_gravidez (PK), codigo, descricao (Durante gravidez,No parto/aborto,Até 42 dias pós-parto,43d a 1 ano pós-parto,Não se aplica) — alimentada por `TPMORTEOCO` (papel `id_momento_gravidez`) e por `TPOBITOCOR` (papel `id_momento_gravidez_pos_investigacao`)
- `Dim_CID` (role-playing): id_cid (PK), codigo_cid (VARCHAR(4), ex: "O95"), descricao (descrição da causa — fonte CID10.DBF), capitulo (capítulo CID-10, ex: "Capítulo XV – Gravidez, parto e puerpério"), categoria (3 caracteres iniciais, ex: "O95") — alimentada por `CAUSABAS` (papel `id_causa_basica`) e por `CAUSABAS_O` (papel `id_causa_original`)

**Dimensões de Investigação (separadas, restritas ao universo `mif`):**
> Decisão: os atributos de investigação dos óbitos **não** serão mais modelados como hierarquia snowflake (`Dim_Investigacao`). Cada atributo mantido vira uma **dimensão independente** que entra diretamente na tabela-fato com sua própria FK — isso elimina uma dimensão artificial que agruparia campos semanticamente distintos.

- `Dim_NivelInvestigador`: id_nivel_investigador (PK), codigo (E/R/M), descricao (Estadual, Regional, Municipal) — derivada de `TPNIVELINV`
- `Dim_ResgateInfo`: id_resgate_info (PK), codigo (01/02/03), descricao — derivada de `TPRESGINFO`
- `Dim_FaixaDiasInvestigacao`: id_faixa_dias (PK), faixa ("0-120","121-240","241-365","366-730","730+"), dias_min, dias_max — derivada de `NUDIASOBCO` (outliers `> 1460` dias descartados)

### Tabela Fato

**1. Fact_MorteMaterna** — grão: combinação única de dimensões
Colunas: 
    id_tempo (FK), 
    id_municipio_ocorrencia (FK, NOT NULL), 
    id_municipio_residencia (FK, nullable), 
    id_faixa_etaria (FK), 
    id_raca_cor (FK), 
    id_local_ocorrencia (FK), 
    id_estabelecimento_saude (FK), 
    id_momento_gravidez (FK, de TPMORTEOCO), 
    id_momento_gravidez_pos_investigacao (FK, nullable, de TPOBITOCOR), 
    id_causa_basica (FK, NOT NULL, de CAUSABAS), 
    id_causa_original (FK, nullable, de CAUSABAS_O), 
    recebeu_assistencia_medica (bool, de ASSISTMED normalizado), 
    atendimento_ambulatorial_sus (bool, de CO_AMBULATORIAL_SUS normalizado: "SIM" → True), 
    possui_cid_obstetrico_secundario (bool, de LINHAA/LINHAB/LINHAC/LINHAD/LINHAII: True se algum contém CID obstétrico O00–O99), 
    id_nivel_investigador (FK, nullable → Dim_NivelInvestigador), 
    id_resgate_info (FK, nullable → Dim_ResgateInfo), 
    id_faixa_dias_investigacao (FK, nullable → Dim_FaixaDiasInvestigacao), 
    **quantidade_obitos** (INT, measure)

Conferência FK: todas as dimensões listadas possuem FK na tabela-fato — `Dim_Tempo` (id_tempo), `Dim_Municipio` (id_municipio_ocorrencia, id_municipio_residencia), `Dim_FaixaEtaria` (id_faixa_etaria), `Dim_RacaCor` (id_raca_cor), `Dim_LocalOcorrencia` (id_local_ocorrencia), `Dim_EstabelecimentoSaude` (id_estabelecimento_saude), `Dim_MomentoGravidez` (id_momento_gravidez, id_momento_gravidez_pos_investigacao), `Dim_CID` (id_causa_basica, id_causa_original), `Dim_NivelInvestigador` (id_nivel_investigador), `Dim_ResgateInfo` (id_resgate_info), `Dim_FaixaDiasInvestigacao` (id_faixa_dias_investigacao). `Dim_Regiao` e `Dim_UF` são alcançadas via `Dim_Municipio` (snowflake).

# Pendências
- Dicionarizar os atributos do CNES aqui nesse arquivo modelo.md
- conferir `LOCOCOR` contra a informação de tipo do estabelecimento de saúde registrado no CNES.
- conferir a quantidade real de dígitos nos 3 atributos que referenciam municipios, olhando os registros reais.
- conferir `id_municipio_estabelecimento` do CNES contra `CODMUNOCOR` registrado no SIM.

