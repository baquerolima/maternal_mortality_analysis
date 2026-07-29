# Plan: Modelo Dimensional Snowflake para Mortalidade Materna

**TL;DR** — Completar o modelo dimensional snowflake iniciado em `modelo.md`, integrando dados SIM (óbitos) + CNES (estabelecimentos) + geografia, com pipeline ETL em Python/SQLAlchemy para PostgreSQL.

---

## Decisões de Design (validadas)

| Decisão | Escolha |
|---|---|
| Filtro de mortes maternas | (SEXO = 'F' AND IDADE BETWEEN '410' AND '449') OR (SEXO IN ('M','I') AND TPMORTEOCO ∈ {1,2,3,4,5}). SEXO normalizado no ETL: 'F' (F/2), 'M' (M/1), 'I' (I/0/9/outros) |
| Escolaridade | **Descartado** -- não haverá Dim_Escolaridade |
| Estado civil | **Descartado** -- não haverá atributo direto `estcivil` |
| Sexo | Atributo **direto** na fato (`sexo CHAR(1)`). Normalizado no ETL com CHECK constraint: sexo IN ('F','M','I'). Valores originais do SIM (1/2/F/M/I/0/9) são mapeados para 'F','M','I' |
| Filhos | **Descartado** — não haverá Dim_FaixaFilhos |
| CNES | **Sub-dimensões snowflake** para natureza org, gestão, hierarquia, esfera, tipo unidade, natureza jurídica |
| Bairro | **Independente** — `Dim_Bairro` com FK direta da fato |
| Granularidade da fato | Contagem agregada por combinação única de dimensões |
| CID | Role-playing dimension (causa_basica, causa_materna, causa_basica_original) |
| Município | Role-playing dimension (ocorrência, residência, estabelecimento) |

---

## Dimensões Completas

### 1. Hierarquia Geográfica (Snowflake)

**Dim_Regiao**
| Coluna | Tipo | Descrição |
|---|---|---|
| id_regiao | SERIAL PK | |
| nome_regiao | VARCHAR(20) | Norte, Nordeste, Sudeste, Sul, Centro-Oeste |

**Dim_UF**
| Coluna | Tipo | Descrição |
|---|---|---|
| id_uf | SERIAL PK | |
| nome_uf | VARCHAR(50) | |
| sigla_uf | CHAR(2) | |
| id_regiao | INT FK → Dim_Regiao | |

**Dim_Municipio**
| Coluna | Tipo | Descrição |
|---|---|---|
| id_municipio | SERIAL PK | |
| codigo_ibge | VARCHAR(7) | Código IBGE de 7 dígitos |
| nome_municipio | VARCHAR(100) | |
| id_uf | INT FK → Dim_UF | |

### 2. Hierarquia Estabelecimentos de Saúde (Snowflake)

**Dim_NaturezaOrganizacao**
| Coluna | Tipo |
|---|---|
| id_natureza_organizacao | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_TipoGestao**
| Coluna | Tipo |
|---|---|
| id_tipo_gestao | SERIAL PK |
| codigo | VARCHAR(1) | (E=Estadual, M=Municipal, D=Dupla, etc.) |
| descricao | VARCHAR |

**Dim_NivelHierarquia**
| Coluna | Tipo |
|---|---|
| id_nivel_hierarquia | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_EsferaAdministrativa**
| Coluna | Tipo |
|---|---|
| id_esfera_administrativa | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_TipoUnidade**
| Coluna | Tipo |
|---|---|
| id_tipo_unidade | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_NaturezaJuridica**
| Coluna | Tipo |
|---|---|
| id_natureza_juridica | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_EstabelecimentoSaude**
| Coluna | Tipo | Origem |
|---|---|---|
| id_estabelecimento | SERIAL PK | |
| codigo_cnes | VARCHAR(7) | CODESTAB (SIM) / CO_CNES (CNES) |
| nome_estabelecimento | VARCHAR | ESTABDESCR / NO_FANTASIA |
| id_municipio | INT FK → Dim_Municipio | CO_IBGE (CNES) |
| id_natureza_organizacao | INT FK → Dim_NaturezaOrganizacao | |
| id_tipo_gestao | INT FK → Dim_TipoGestao | |
| id_nivel_hierarquia | INT FK → Dim_NivelHierarquia | |
| id_esfera_administrativa | INT FK → Dim_EsferaAdministrativa | |
| id_tipo_unidade | INT FK → Dim_TipoUnidade | |
| id_natureza_juridica | INT FK → Dim_NaturezaJuridica | |
| st_centro_obstetrico | BOOLEAN | |
| st_centro_neonatal | BOOLEAN | |
| st_atend_hospitalar | BOOLEAN | |
| st_servico_apoio | BOOLEAN | |
| st_atend_ambulatorial | BOOLEAN | |
| co_motivo_desab | VARCHAR | |
| co_ambulatorial_sus | VARCHAR | |

### 3. Dim_Bairro (independente)

| Coluna | Tipo |
|---|---|
| id_bairro | SERIAL PK |
| nome_bairro | VARCHAR(100) |

> Nota: Os bairros vêm do CNES (NO_BAIRRO). Como um bairro pode existir em múltiplos municípios, e a granularidade é apenas o nome, usamos tabela independente. O vínculo município-bairro pode ser feito via `Dim_EstabelecimentoSaude.id_municipio` em join.

### 4. Dim_Tempo

| Coluna | Tipo |
|---|---|
| id_tempo | SERIAL PK |
| data_completa | DATE |
| dia | INT |
| mes | INT |
| ano | INT |
| trimestre | INT |
| semestre | INT |

### 5. Dim_FaixaEtaria

| Coluna | Tipo |
|---|---|
| id_faixa_etaria | SERIAL PK |
| faixa | VARCHAR(10) |
| idade_min | INT |
| idade_max | INT |

Faixas: 10-14, 15-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49

> Nota: A faixa "50+" existe na dimensão para completude, mas não receberá registros devido ao filtro de idade (10-49 anos).

### 6. Dim_RacaCor

| Coluna | Tipo |
|---|---|
| id_raca_cor | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(20) |

1-Branca, 2-Preta, 3-Amarela, 4-Parda, 5-Indígena

### 7. Dim_LocalOcorrencia (LOCOCOR)

| Coluna | Tipo |
|---|---|
| id_local_ocorrencia | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(50) |

1-Hospital, 2-Outros est. saúde, 3-Domicílio, 4-Via pública, 5-Outros, 6-Aldeia indígena, 9-Ignorado

### 8. Dim_SituacaoGestacionalObito (TPMORTEOCO)

| Coluna | Tipo |
|---|---|
| id_situacao_gestacional | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(60) |

1-Na gravidez, 2-No parto, 3-No abortamento, 4-Até 42 dias pós-parto, 5-43d a 1 ano pós-parto, 8-Não ocorreu nestes períodos, 9-Ignorado

### 9. Dim_TipoParto (PARTO)

| Coluna | Tipo |
|---|---|
| id_tipo_parto | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(20) |

1-Vaginal, 2-Cesáreo, 9-Ignorado

### 10. Dim_MomentoObitoParto (OBITOPARTO)

| Coluna | Tipo |
|---|---|
| id_momento_obito_parto | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(20) |

1-Antes, 2-Durante, 3-Depois, 9-Ignorado

### 11. Dim_TipoGravidez (GRAVIDEZ)

| Coluna | Tipo |
|---|---|
| id_tipo_gravidez | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(20) |

1-Única, 2-Dupla, 3-Tripla e mais, 9-Ignorada

### 12. Dim_SemanaGestacao (SEMAGESTAC)

| Coluna | Tipo |
|---|---|
| id_semana_gestacao | SERIAL PK |
| faixa | VARCHAR(20) |
| semanas_min | INT |
| semanas_max | INT |

Faixas: 0-21, 22-27, 28-31, 32-36, 37-41, 42+

### 13. Dim_CID (Role-Playing)

| Coluna | Tipo |
|---|---|
| id_cid | SERIAL PK |
| codigo | VARCHAR(6) | Código CID-10 (ex: O150, X999) |
| descricao | VARCHAR(255) | |
| capitulo | VARCHAR(10) | Capítulo CID (ex: XV, XX) |

---

## Critérios de Filtro (Registros que entram na Fato)

Os registros do SIM são filtrados para incluir apenas mortes potencialmente maternas, seguindo a regra:

#### Filtro de mortes maternas
```
(SEXO = 'F' AND IDADE BETWEEN '410' AND '449')
OR (SEXO IN ('M', 'I') AND TPMORTEOCO IN ('1','2','3','4','5'))
```
Onde SEXO foi normalizado no ETL: 'F' (F ou 2 no SIM), 'M' (M ou 1), 'I' (I, 0, 9 ou demais).

### Regra principal: Mulheres em idade fértil
```
SEXO = 'F'
AND IDADE BETWEEN '410' AND '449'
```

> **Decodificação do IDADE:** campo de 3 dígitos: o 1º dígito é a unidade (`4` = ano) e os 2 dígitos seguintes são a quantidade. Logo, `"410"` = 10 anos e `"449"` = 49 anos.

### Exceção (outlier): Sexo M ou I com marcador de mortalidade materna
```
SEXO IN ('M', 'I')
AND TPMORTEOCO IN ('1', '2', '3', '4', '5')
```

Registros de sexo masculino ou ignorado que possuem `TPMORTEOCO` indicando circunstância gestacional são incluídos como possíveis casos de pessoas trans ou erros de preenchimento — uma verificação de qualidade dos dados.

### Filtro final (SQL-like)
```sql
WHERE (SEXO = 'F' AND IDADE BETWEEN '410' AND '449')
   OR (SEXO IN ('M', 'I') AND TPMORTEOCO IN ('1', '2', '3', '4', '5'))
```

---

## Tabela Fato

### Fact_MorteMaterna

Grão: combinação única de dimensões (1 registro por combinação)

| Coluna | Tipo | Origem |
|---|---|---|
| id_tempo | INT FK → Dim_Tempo | DTOBITO |
| id_municipio_ocorrencia | INT FK → Dim_Municipio **NOT NULL** | CODMUNOCOR |
| id_municipio_residencia | INT FK → Dim_Municipio nullable | CODMUNRES |
| id_municipio_estabelecimento | INT FK → Dim_Municipio nullable | CO_IBGE (CNES) |
| id_bairro_ocorrencia | INT FK → Dim_Bairro nullable | NO_BAIRRO (CNES) |
| id_estabelecimento_saude | INT FK → Dim_EstabelecimentoSaude nullable | CODESTAB |
| id_faixa_etaria | INT FK → Dim_FaixaEtaria | IDADE |
| id_raca_cor | INT FK → Dim_RacaCor | RACACOR |
| id_local_ocorrencia | INT FK → Dim_LocalOcorrencia | LOCOCOR |
| id_situacao_gestacional | INT FK → Dim_SituacaoGestacionalObito | TPMORTEOCO |
| id_tipo_parto | INT FK → Dim_TipoParto | PARTO |
| id_momento_obito_parto | INT FK → Dim_MomentoObitoParto | OBITOPARTO |
| id_tipo_gravidez | INT FK → Dim_TipoGravidez | GRAVIDEZ |
| id_semana_gestacao | INT FK → Dim_SemanaGestacao | SEMAGESTAC |
| id_causa_basica | INT FK → Dim_CID **NOT NULL** | CAUSABAS |
| id_causa_materna | INT FK → Dim_CID nullable | CAUSAMAT |
| id_causa_basica_original | INT FK → Dim_CID nullable | CAUSABAS_O |
| sexo | CHAR(1) nullable | SEXO normalizado: 'F' (F/2), 'M' (M/1), 'I' (I/0/9/outros). CHECK constraint: sexo IN ('F','M','I') |
| recebeu_assistencia_medica | BOOLEAN | ASSISTMED (1=sim) |
| quantidade_obitos | INT **measure** | COUNT(*) |

---

## Etapas de Implementação

### Fase 1: Modelagem SQL e criação das tabelas
**Dependências:** Nenhuma (paralelizável com Fase 2)

1. **Criar script SQL de DDL** (`sus_etl/schemas/star_schema.sql`) com todas as 20 tabelas (14 dimensões + sub-dimensões CNES + fato)
2. **Incluir CONSTRAINTS**, FKs, índices, chaves únicas
3. **Adicionar tabela de metadados de dim_carga** (tracking de quando cada dimensão foi populada)

### Fase 2: Dimensões de Domínio Fixo (carga manual)
**Dependências:** Nenhuma (paralelizável com Fase 1)

4. **Criar módulo `sus_etl/dimensoes_fixas.py`** com dicionários de:
   - Dim_Regiao (5 regiões)
   - Dim_RacaCor (5 cores)
   - Dim_LocalOcorrencia (7 valores LOCOCOR)
   - Dim_SituacaoGestacionalObito (7 valores TPMORTEOCO)
   - Dim_TipoParto (4 valores PARTO)
   - Dim_MomentoObitoParto (4 valores OBITOPARTO)
   - Dim_TipoGravidez (4 valores GRAVIDEZ)
   - Dim_SemanaGestacao (6 faixas)
   - Dim_NaturezaJuridica (categorias CNES)

5. **Função `carregar_dimensoes_fixas()`** que insere via SQLAlchemy

### Fase 3: Dimensões Geográficas (CNES + IBGE)
**Dependências:** Fase 1

6. **Extrair UF + região** de tabela auxiliar de municípios brasileiros
7. **Criar `sus_etl/dimensoes_geograficas.py`**:
   - Extrair municípios únicos de SIM (CODMUNOCOR, CODMUNRES) + CNES (CO_IBGE)
   - Carregar Dim_UF e Dim_Municipio

### Fase 4: Dimensão Estabelecimentos de Saúde
**Dependências:** Fase 1, Fase 2 (sub-dimensões CNES)

8. **Criar `sus_etl/dimensoes_cnes.py`**:
   - Carregar sub-dimensões CNES (NaturezaOrganizacao, TipoGestao, NivelHierarquia, EsferaAdministrativa, TipoUnidade) a partir dos dados do CNES
   - Carregar Dim_Bairro
   - Carregar Dim_EstabelecimentoSaude com todos os FKs

### Fase 5: Dimensão Tempo
**Dependências:** Nenhuma

9. **Criar `sus_etl/dimensao_tempo.py`**:
   - Gerar séries de data baseada em DTOBITO (2014-2023+)
   - Popular Dim_Tempo com data, dia, mês, ano, trimestre, semestre

### Fase 6: Dimensão CID
**Dependências:** Fase 1

10. **Criar `sus_etl/dimensao_cid.py`**:
    - Extrair CIDs únicos de CAUSABAS, CAUSAMAT, CAUSABAS_O
    - Buscar descrição e capítulo (pode ser via arquivo auxiliar CID-10)
    - Carregar Dim_CID

### Fase 7: Tabela Fato
**Dependências:** Fases 2, 3, 4, 5, 6 (todas as dimensões carregadas)

11. **Criar `sus_etl/fact_table.py`**:
    - **Normalizar SEXO:** mapear valor original do SIM → 'F'|'M'|'I' (F/2→F, M/1→M, I/0/9/demais→I)
    - Aplicar filtro: `(SEXO = 'F' AND IDADE BETWEEN '410' AND '449') OR (SEXO IN ('M','I') AND TPMORTEOCO IN ('1','2','3','4','5'))`
    - Para registros M ou I incluídos pela exceção, logar contagem como alerta de qualidade (outliers)
    - Resolver cada FK via lookup nas dimensões
    - Agrupar por combinação única de dimensões
    - Inserir em Fact_MorteMaterna com quantidade_obitos = COUNT(*)

### Fase 8: Pipeline ETL Integrado
**Dependências:** Fases 1-7

12. **Modificar `sus_etl/main.py`** para:
    - Após carga staging, executar carga de dimensões + fato
    - Adicionar flag `--full-refresh` para recarregar tudo
    - Adicionar logging de progresso

### Fase 9: Validação e Testes
**Dependências:** Fase 7

13. **Criar `sus_etl/validacao.py`** com:
    - Verificar total de óbitos na fato vs. raw data
    - Checar nulls em colunas NOT NULL
    - Validar FKs (nenhum registro órfão)
    - Relatório de cardinalidade por dimensão

---

## Arquivos relevantes

### A modificar/criar:
- `sus_etl/schemas/star_schema.sql` — DDL completo (NOVO)
- `sus_etl/dimensoes_fixas.py` — Dimensões de domínio fixo (NOVO)
- `sus_etl/dimensoes_geograficas.py` — Dim_Regiao, Dim_UF, Dim_Municipio (NOVO)
- `sus_etl/dimensoes_cnes.py` — Dim_EstabelecimentoSaude + sub-dims (NOVO)
- `sus_etl/dimensao_tempo.py` — Dim_Tempo (NOVO)
- `sus_etl/dimensao_cid.py` — Dim_CID (NOVO)
- `sus_etl/fact_table.py` — Fact_MorteMaterna (NOVO)
- `sus_etl/main.py` — Integrar pipeline (MODIFICAR)
- `sus_etl/validacao.py` — Validações pós-carga (NOVO)
- `modelo.md` — Atualizar com modelo completo (MODIFICAR)

### Como referência:
- `arquivos/CNES/cnes_estabelecimentos.csv` — Fonte de dados CNES
- `arquivos/SIM/dados_*.csv` (2014-2023) — Fonte de dados SIM
- `exploracoes/filtra_mortalidade_materna.py` — Lógica de filtro original (TPMORTEOCO). **Substituído** pelo novo critério: SEXO normalizado + idade 10-49 + exceção M/I com TPMORTEOCO
- `sus_etl/database.py` — Conexão PostgreSQL + engine SQLAlchemy
- `sus_etl/processing.py` — Padrão de carga staging (referência)

---

## Verificação

1. Executar pipeline ETL completo do staging até star schema
2. `SELECT COUNT(*) FROM Fact_MorteMaterna` deve bater com total de registros do filtro: `(SEXO = 'F' AND IDADE BETWEEN '410' AND '449') OR (SEXO IN ('M','I') AND TPMORTEOCO IN ('1','2','3','4','5'))`
3. **Validação de outlier:** Log deve reportar quantos registros M ou I foram incluídos pela exceção (espera-se quantidade residual)
4. Nenhum FK na fato deve apontar para ID inexistente nas dimensões
5. Colunas NOT NULL (id_tempo, id_municipio_ocorrencia, id_causa_basica) sem NULLs
6. Ao menos 1 registro por ano de dado disponível
7. Consultas analíticas de exemplo funcionam (ex: óbitos por ano × raça_cor × região)
