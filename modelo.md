# Colunas de interesse no SIM

## Tempo
`DTOBITO`
    Data do óbito no formato DDMMAAAA. Desse atributo deriva toda a dimensão tempo.

## Identificação da mulher
`IDADE`
    Idade possui dois subcampos. Primeiro digito indica a unidade da idade (se 1 = minuto, se 2 = hora, se 3 = mês, se 4 = ano, se = 5 idade maior que 100 anos).
    Segundo subcampo indica a quantidade de unidades do campo 1. 
    Esse atributo compõem a identificação da pessoa falecida e dele deriva a dimensão faixa_etaria.

`SEXO`
    Masculino = M,1 ; Feminino = F,2 ; Ignorado = I, 0, 9
    Esse campo serve para verificar se há registros de pessoas trans com óbitos maternos. 
    Esse atributo compõem a identificação da pessoa falecida e dele deriva a dimensão sexo.

`RACACOR`
    1 – Branca; 2 – Preta; 3 – Amarela; 4 – Parda; 5 – Indígena
    Esse atributo compõem a identificação da pessoa falecida e dele deriva a dimensão raça.

## Estabelecimento de Saúde
`LOCOCOR`
    Local em que ocorreu o óbito. 1 – hospital; 2 – outros estabelecimentos de saúde; 3 – domicílio; 4 – via pública; 5 – outros; 6 - aldeia indígena; 9 – ignorado. 
    Esse atributo compõem a dimensão estabelecimento_de_saúde.

`CODESTAB`
    Codigo CNES do Estabelecimento de Saúde em que ocorreu o óbito. 
    Esse atributo compõem a dimensão estabelecimento_de_saúde.

Essa dimensão estabelecimento_de_saúde terá uma hierarquia "snowflake" com os dados dos estabelecimentos de saúde que vamos pegar na base do CNES - Cadastro Nacional dos Estabelecimentos de Saúde. A granularidade mais baixa refere-se aos codigos dos estabelecimentos, sendo que queremos agrupar os estabelecimentos por local_do_obito (LOCOCOR) e demais dados oriundos do CNES - ver lista de campos abaixo.

Campos do CNES: 
CO_CNES - equivalente a CODESTAB no SIM - essa é a chave de ligação entre os dados
CO_IBGE
CO_NATUREZA_ORGANIZACAO
TP_GESTAO
CO_NIVEL_HIERARQUIA
CO_ESFERA_ADMINISTRATIVA
CO_ATIVIDADE
TP_UNIDADE
NO_BAIRRO
CO_NATUREZA_JUR
ST_CENTRO_OBSTETRICO
ST_CENTRO_NEONATAL
ST_ATEND_HOSPITALAR
ST_SERVICO_APOIO
ST_ATEND_AMBULATORIAL
CO_MOTIVO_DESAB
CO_AMBULATORIAL_SUS

## Municipio
`CODMUNRES`
    Codigo do municipio com até 7 dígitos, porém maioria dos registros possui 6 dígitos. 
    Desse atributo deriva a dimensão municipio_residencia.

`CODMUNOCOR`
    Codigo do municipio com até 8 dígitos, porém maioria dos registros possui 6 dígitos. 
    Desse atributo deriva a dimensão municipio_ocorrencia.

## Circunstâncias do óbito
`TPMORTEOCO`
    Situacao gestacional em que ocorreu o obito.
    1: na gravidez; 2: no parto; 3: no abortamento; 4: até 42 dias após o término do parto; 5: de 43 dias a 1 ano após o término da gestação; 8: não ocorreu nestes períodos; 9: ignorado.
    Esse atributo compõem as circunstancias do óbito da pessoa falecida e dele deriva a dimensão situacao_gestacional_obito.

`ASSISTMED`
    Identificador se a pessoa falecida recebeu assistencia medica. 1 – sim; 2 – não; 9 – ignorado
    Esse atributo compõem as circunstancias do óbito da pessoa falecida e dele deriva a dimensão recebeu_assist_medica.

`CAUSABAS`
    CIDs informados como causa básica do óbito. Representa a causa inicial geralmente.
    Esse atributo compõem as circunstancias do óbito da pessoa falecida e dele deriva a dimensão causa_basica.

`CAUSABAS_O`
    Causa básica original do óbito, informado antes da resseleção.
    Esse atributo compõem as circunstancias do óbito da pessoa falecida e dele deriva a dimensao causa_basica_anterior.


# Modelo Dimensional para Análise de Mortalidade Materna

**TL;DR** — Modelo dimensional snowflake com fato sendo a quantidade de óbitos de cada dimensão.

## Decisões de Design
- **Granularidade**: Fato agregado (contagem por combinação única de dimensões)
- **Schema**: Snowflake (hierarquias normalizadas)

### Decisão: Município de Residência como Role-Playing Dimension
- `Dim_Municipio` é reutilizada com papel triplo na fato: `id_municipio_ocorrencia` (NOT NULL), `id_municipio_residencia` (nullable) e `id_municipio_estabelecimento` (nullable) oriundo do atributo "CO_IBGE" do CNES.
- As 3 FKs apontam para a mesma `Dim_Municipio` — *role-playing dimension*

### Decisão: CID como Role-Playing Dimension
- `Dim_CID` é reutilizada com papel duplo na fato: `id_causa_basica` (NOT NULL) e `id_causa_basica_original` (nullable).
- As 2 FKs apontam para a mesma `Dim_CID` — *role-playing dimension*

## Modelo Dimensional (Snowflake)

**Hierarquia Geográfica (snowflake):**
- `Dim_Regiao`: id_regiao (PK), nome_regiao (Norte, Nordeste, Sudeste, Sul, Centro-Oeste)
- `Dim_UF`: id_uf (PK), nome_uf, sigla_uf, id_regiao (FK → Dim_Regiao)
- `Dim_Municipio`: id_municipio (PK), codigo_ibge (7 dígitos), nome_municipio, id_uf (FK → Dim_UF)

**Hierarquia Estabelecimentos de Saúde (snowflake):**
- `Dim_EstabelecimentoSaude`: id_estabelecimento (PK), codigo_cnes, nome_estabelecimento, id_municipio (FK → Dim_Municipio)
Pendente: Escrever as dimensões secundarias com os atributos do CNES que serão ligados à DIM_EstabelecimentoSaude

- `Dim_Tempo`: id_tempo (PK), data_completa, dia, mes, ano, trimestre, semestre
- `Dim_FaixaEtaria`: id_faixa_etaria (PK), faixa ("10-14","15-19",...,"45-49"), idade_min, idade_max
- `Dim_RacaCor`: id_raca_cor (PK), codigo (1-5), descricao (Branca,Preta,Amarela,Parda,Indígena)
- `Dim_MomentoGravidez`: id_momento_gravidez (PK), codigo, descricao (Durante gravidez,No parto/aborto,Até 42 dias pós-parto,43d a 1 ano pós-parto,Não se aplica)
Pendente: Escrever as dimensões de circunstancias do obito que estão descritas acima e não estão elencadas aqui.
Pendente: Escrever as dimensões `id_causa_basica` e `id_causa_basica_original` associadas à `DIM_CID`.

### Tabela Fato

**1. Fact_MorteMaterna** — grão: combinação única de dimensões
Colunas: id_tempo (FK), id_municipio_ocorrencia (FK, NOT NULL), id_municipio_residencia (FK, nullable), id_bairro_ocorrencia (FK, nullable → Dim_Bairro), id_faixa_etaria (FK), id_raca_cor (FK), id_escolaridade (FK), id_estado_civil (FK), id_local_ocorrencia (FK), id_estabelecimento_saude (FK), id_momento_gravidez (FK), id_faixa_filhos (FK), id_cid_basico (FK), durante_parto (bool), durante_puerperio (bool), recebeu_assistencia_medica (bool), **quantidade_obitos** (INT, measure)
Pendente: incluir as novas dimensões.


