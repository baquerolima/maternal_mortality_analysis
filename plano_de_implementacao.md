# Plan: Modelo Dimensional Snowflake para Mortalidade Materna

**TL;DR** — Completar o modelo dimensional snowflake definido em `modelo.md`, integrando dados SIM (óbitos) + CNES (estabelecimentos) + geografia, com pipeline ETL em Python/SQLAlchemy para PostgreSQL.

---

## Decisões de Design (validadas em `modelo.md`)

| Decisão | Escolha |
|---|---|
| Granularidade da fato | Contagem agregada (`quantidade_obitos`) por combinação única de dimensões |
| Schema | Snowflake (hierarquias geográfica e de estabelecimentos de saúde) |
| Filtro de mortes maternas | `(SEXO_NORMALIZADO = 'F' AND IDADE BETWEEN '410' AND '449') OR (TPMORTEOCO_NORMALIZADO IN ('1','2','3','4','5') AND IDADE BETWEEN '408' AND '465')` — mulheres 10–49 anos OU circunstância gestacional 1–5 com 8–65 anos |
| Sexo | **Não persiste na fato.** Usado apenas como filtro (normalizado: '2'/'F'→F, '1'/'M'→M, '0'/'9'/outros→I); captura registros de pessoas trans com óbitos maternos |
| Município | Chave natural `codigo_ibge` (PK, 6 dígitos). Role-playing na fato: `codigo_ibge_ocorrencia` (NOT NULL) e `codigo_ibge_residencia` (nullable). O `codigo_ibge` do estabelecimento **não** entra na fato (fica em `Dim_EstabelecimentoSaude` via `CO_IBGE`) |
| Estabelecimento (CNES) | Chave natural `codigo_cnes` (PK, `CO_CNES`). `Dim_EstabelecimentoSaude` + sub-dimensões (`Dim_EsferaAdministrativa`, `Dim_TipoUnidade`, `Dim_NaturezaJuridica`, `Dim_TipoGestao`). `CO_AMBULATORIAL_SUS` entra **direto na fato** (booleano) |
| CID | Role-playing dimension: `id_causa_basica` (NOT NULL, de `CAUSABAS`) e `id_causa_original` (nullable, de `CAUSABAS_O`) |
| CID obstétrico secundário | `LINHAA`–`LINHAII` não geram dimensão; derivam `possui_cid_obstetrico_secundario` (True se algum contém CID O00–O99) |
| Momento da gravidez | Role-playing dimension: `id_momento_gravidez` (de `TPMORTEOCO`) e `id_momento_gravidez_pos_investigacao` (nullable, de `TPOBITOCOR`) |
| Assistência médica | `ASSISTMED` normalizado: `1`→True; `2`/`9`/vazio→False (`recebeu_assistencia_medica`) |
| Investigação dos óbitos | Dimensões **independentes** (sem `Dim_Investigacao`): `Dim_NivelInvestigador`, `Dim_ResgateInfo`, `Dim_FaixaDiasInvestigacao` |
| Tempo | `Dim_Tempo` simplificada: apenas `ano` (sem dia, mês, trimestre, semestre) |
| Colunas descartadas (EDA) | `MORTEPARTO`, `DTINVESTIG`, `DTCONINV`, `FONTEINV`, `OBITOGRAV`, `OBITOPUERP`, `CAUSAMAT` — validadas em `exploracoes/analisa_variaveis_dim.ipynb` |

---

## Critérios de Filtro (Registros que entram na Fato)

Os registros do SIM são filtrados para incluir apenas mortes potencialmente maternas. O SEXO é normalizado no ETL ('2'/'F'→F, '1'/'M'→M, demais→I) e usado apenas como critério de filtro — não é armazenado na fato.

#### Filtro único (sem exceção separada)
```
(SEXO_NORMALIZADO = 'F' AND IDADE BETWEEN '410' AND '449')
OR (TPMORTEOCO_NORMALIZADO IN ('1', '2', '3', '4', '5') AND IDADE BETWEEN '408' AND '465')
```

> **Decodificação do IDADE:** campo de 3 dígitos: o 1º dígito é a unidade (`4` = ano) e os 2 dígitos seguintes são a quantidade. Logo, `"410"` = 10 anos, `"449"` = 49 anos, `"408"` = 8 anos e `"465"` = 65 anos.

### Nota sobre inclusão de outliers
Registros com TPMORTEOCO indicando circunstância gestacional (1 a 5) são incluídos independentemente do SEXO — capturando os casos de sexo M ou I — **desde que a idade esteja entre 8 e 65 anos** (`IDADE BETWEEN '408' AND '465'`). O SEXO não persiste na tabela fato.

### Filtro final (SQL-like)
```sql
WHERE (SEXO_NORMALIZADO = 'F' AND IDADE BETWEEN '410' AND '449')
   OR (TPMORTEOCO_NORMALIZADO IN ('1', '2', '3', '4', '5') AND IDADE BETWEEN '408' AND '465')
```

---

## Dimensões

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
| codigo_ibge | VARCHAR(6) PK | Código IBGE de 6 dígitos (raiz) — chave natural |
| nome_municipio | VARCHAR(100) | |
| id_uf | INT FK → Dim_UF | |

### 2. Dim_EstabelecimentoSaude + sub-dimensões (CNES)

> `CO_AMBULATORIAL_SUS` **não** fica aqui — vai direto para a fato como booleano. `CO_ESFERA_ADMINISTRATIVA`, `TP_UNIDADE`, `CO_NATUREZA_JUR` e `TP_GESTAO` viram sub-dimensões (para mapear os códigos e, futuramente, criar agrupamentos de códigos).

**Dim_EstabelecimentoSaude**
| Coluna | Tipo | Origem |
|---|---|---|
| codigo_cnes | VARCHAR(7) PK | `CO_CNES` (equivale a `CODESTAB` do SIM) — chave natural |
| nome_fantasia | VARCHAR | `NO_FANTASIA` |
| codigo_ibge | VARCHAR(6) FK → Dim_Municipio | `CO_IBGE` (raiz do código IBGE) |
| bairro | VARCHAR(100) | `NO_BAIRRO` |
| id_esfera_administrativa | INT FK → Dim_EsferaAdministrativa | `CO_ESFERA_ADMINISTRATIVA` |
| id_tipo_unidade | INT FK → Dim_TipoUnidade | `TP_UNIDADE` |
| id_natureza_juridica | INT FK → Dim_NaturezaJuridica | `CO_NATUREZA_JUR` |
| id_tipo_gestao | INT FK → Dim_TipoGestao | `TP_GESTAO` |

**Dim_EsferaAdministrativa** (`CO_ESFERA_ADMINISTRATIVA`)
| Coluna | Tipo |
|---|---|
| id_esfera_administrativa | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_TipoUnidade** (`TP_UNIDADE`)
| Coluna | Tipo |
|---|---|
| id_tipo_unidade | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_NaturezaJuridica** (`CO_NATUREZA_JUR`)
| Coluna | Tipo |
|---|---|
| id_natureza_juridica | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

**Dim_TipoGestao** (`TP_GESTAO`)
| Coluna | Tipo |
|---|---|
| id_tipo_gestao | SERIAL PK |
| codigo | VARCHAR |
| descricao | VARCHAR |

### 3. Dim_Tempo (simplificada)

| Coluna | Tipo | Descrição |
|---|---|---|
| id_tempo | SERIAL PK | |
| ano | INT | Ano do óbito (derivado de `DTOBITO`). Sem dia, mês, trimestre ou semestre |

### 4. Dim_FaixaEtaria

| Coluna | Tipo |
|---|---|
| id_faixa_etaria | SERIAL PK |
| faixa | VARCHAR(20) |
| idade_min | INT |
| idade_max | INT |

Faixas: Até 14 anos, 15-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49, Acima de 49 anos

### 5. Dim_RacaCor

| Coluna | Tipo |
|---|---|
| id_raca_cor | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(20) |

1-Branca, 2-Preta, 3-Amarela, 4-Parda, 5-Indígena, 9-Ignorado

### 6. Dim_LocalOcorrencia (LOCOCOR)

| Coluna | Tipo |
|---|---|
| id_local_ocorrencia | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(50) |

1-Hospital, 2-Outros est. saúde, 3-Domicílio, 4-Via pública, 5-Outros, 6-Aldeia indígena, 9-Ignorado

### 7. Dim_MomentoGravidez (Role-Playing)

| Coluna | Tipo |
|---|---|
| id_momento_gravidez | SERIAL PK |
| codigo | INT |
| descricao | VARCHAR(60) |

> Alimentada por `TPMORTEOCO` (papel `id_momento_gravidez`) e por `TPOBITOCOR` (papel `id_momento_gravidez_pos_investigacao`).
>
> Descrições: Durante gravidez (1), No parto/aborto (2–3), Até 42 dias pós-parto (4), 43d a 1 ano pós-parto (5), Não se aplica (8), Ignorado (9).
>
> Nota: valores 6 e 7 do SIM são normalizados para 9 (Ignorado) no ETL.

### 8. Dim_CID (Role-Playing)

| Coluna | Tipo |
|---|---|
| id_cid | SERIAL PK |
| codigo_cid | VARCHAR(4) | Código CID-10 (ex: "O95") |
| descricao | VARCHAR(255) | Descrição da causa (fonte CID10.DBF) |
| capitulo | VARCHAR | Capítulo CID-10 (ex: "Capítulo XV – Gravidez, parto e puerpério") |
| categoria | VARCHAR(3) | 3 caracteres iniciais (ex: "O95") |

### 9. Dim_NivelInvestigador (TPNIVELINV)

| Coluna | Tipo |
|---|---|
| id_nivel_investigador | SERIAL PK |
| codigo | CHAR(1) |
| descricao | VARCHAR(20) |

E-Estadual, R-Regional, M-Municipal

### 10. Dim_ResgateInfo (TPRESGINFO)

| Coluna | Tipo |
|---|---|
| id_resgate_info | SERIAL PK |
| codigo | VARCHAR(2) |
| descricao | VARCHAR(80) |

01-Não acrescentou nem corrigiu, 02-Resgate de novas informações, 03-Correção de causas informadas

### 11. Dim_FaixaDiasInvestigacao (NUDIASOBCO)

| Coluna | Tipo |
|---|---|
| id_faixa_dias | SERIAL PK |
| faixa | VARCHAR(10) |
| dias_min | INT |
| dias_max | INT |

Faixas: 0-120, 121-240, 241-365, 366-730, 730+
> Nota: outliers de `NUDIASOBCO` > 1460 dias são descartados no ETL.

---

## Tabela Fato

### Fact_MorteMaterna

Grão: combinação única de dimensões (1 registro por combinação)

| Coluna | Tipo | Origem |
|---|---|---|
| id_tempo | INT FK → Dim_Tempo | DTOBITO (ano) |
| codigo_ibge_ocorrencia | VARCHAR(6) FK → Dim_Municipio **NOT NULL** | CODMUNOCOR |
| codigo_ibge_residencia | VARCHAR(6) FK → Dim_Municipio nullable | CODMUNRES |
| id_faixa_etaria | INT FK → Dim_FaixaEtaria | IDADE |
| id_raca_cor | INT FK → Dim_RacaCor | RACACOR |
| id_local_ocorrencia | INT FK → Dim_LocalOcorrencia | LOCOCOR |
| codigo_cnes | VARCHAR(7) FK → Dim_EstabelecimentoSaude nullable | CODESTAB |
| id_momento_gravidez | INT FK → Dim_MomentoGravidez | TPMORTEOCO |
| id_momento_gravidez_pos_investigacao | INT FK → Dim_MomentoGravidez nullable | TPOBITOCOR |
| id_causa_basica | INT FK → Dim_CID **NOT NULL** | CAUSABAS |
| id_causa_original | INT FK → Dim_CID nullable | CAUSABAS_O |
| recebeu_assistencia_medica | BOOLEAN | ASSISTMED (1→True; 2/9/vazio→False) |
| atendimento_ambulatorial_sus | BOOLEAN | CO_AMBULATORIAL_SUS ("SIM"→True; demais→False) |
| possui_cid_obstetrico_secundario | BOOLEAN | LINHAA–LINHAII (True se algum contém CID O00–O99) |
| id_nivel_investigador | INT FK → Dim_NivelInvestigador nullable | TPNIVELINV |
| id_resgate_info | INT FK → Dim_ResgateInfo nullable | TPRESGINFO |
| id_faixa_dias_investigacao | INT FK → Dim_FaixaDiasInvestigacao nullable | NUDIASOBCO |
| quantidade_obitos | INT **measure** | COUNT(*) |

---

## Etapas de Implementação

### Fase 1: Modelagem SQL e criação das tabelas
**Dependências:** Nenhuma (paralelizável com Fase 2)

1. **Criar script SQL de DDL** (`sus_etl/schemas/star_schema.sql`) com todas as tabelas (todas as dimensões + fato + metadados de carga)
2. **Incluir CONSTRAINTS**, FKs, índices, chaves únicas
3. **Adicionar tabela de metadados de dim_carga** (tracking de quando cada dimensão foi populada)

### Fase 2: Dimensões de Domínio Fixo (carga manual)
**Dependências:** Nenhuma (paralelizável com Fase 1)

4. **Criar módulo `sus_etl/dimensoes_fixas.py`** com dicionários de:
   - Dim_Regiao (5 regiões)
   - Dim_RacaCor (6 cores, incluindo código 9-Ignorado)
   - Dim_LocalOcorrencia (7 valores LOCOCOR)
   - Dim_MomentoGravidez (valores de TPMORTEOCO e TPOBITOCOR)
   - Dim_NivelInvestigador (E/R/M)
   - Dim_ResgateInfo (01/02/03)
   - Dim_FaixaDiasInvestigacao (5 faixas)

5. **Função `carregar_dimensoes_fixas()`** que insere via SQLAlchemy

### Fase 3: Dimensões Geográficas (IBGE)
**Dependências:** Fase 1

6. **Extrair UF + região** de tabela auxiliar de municípios brasileiros
7. **Criar `sus_etl/dimensoes_geograficas.py`**:
   - Carregar Dim_Regiao, Dim_UF e Dim_Municipio (PK natural = código IBGE de 6 dígitos — raiz)
   - Incluir registro sentinela `999999` ("Município não identificado") em Dim_Municipio

### Fase 4: Dim_EstabelecimentoSaude + sub-dimensões (CNES)
**Dependências:** Fase 1, Fase 3

8. **Criar `sus_etl/dimensoes_cnes.py`**:
   - Carregar as sub-dimensões `Dim_EsferaAdministrativa`, `Dim_TipoUnidade`, `Dim_NaturezaJuridica` e `Dim_TipoGestao` (código + descrição)
   - Carregar `Dim_EstabelecimentoSaude` com os atributos do CNES: `CO_CNES` (PK natural), `NO_FANTASIA`, `CO_IBGE` (6 dígitos, FK → Dim_Municipio), `NO_BAIRRO`
   - Resolver as FKs das sub-dimensões
   - Incluir registro sentinela `9999999` ("Estabelecimento não identificado") em Dim_EstabelecimentoSaude

### Fase 5: Dimensão Tempo (simplificada)
**Dependências:** Nenhuma

9. **Criar `sus_etl/dimensao_tempo.py`**:
   - Extrair os anos únicos de DTOBITO (2014–2024)
   - Popular Dim_Tempo apenas com `ano`

### Fase 6: Dimensão CID (role-playing)
**Dependências:** Fase 1

10. **Criar `sus_etl/dimensao_cid.py`**:
    - Extrair CIDs únicos de CAUSABAS e CAUSABAS_O
    - Buscar descrição, capítulo e categoria (fonte CID10.DBF)
    - Carregar Dim_CID (codigo_cid, descricao, capitulo, categoria)

### Fase 7: Tabela Fato
**Dependências:** Fases 2, 3, 4, 5, 6 (todas as dimensões carregadas)

11. **Criar `sus_etl/fact_table.py`**:
    - **Normalizar SEXO internamente** (não persiste na fato): '2'/'F'→F, '1'/'M'→M, '0'/'9'/outros→I
    - **Normalizar TPMORTEOCO:** valores 6 e 7 → 9 (Ignorado)
    - **Normalizar ASSISTMED:** 1→True; 2/9/vazio→False
    - **Normalizar CO_AMBULATORIAL_SUS:** "SIM"→True; demais→False
    - **Derivar `possui_cid_obstetrico_secundario`** de LINHAA–LINHAII (algum contém CID O00–O99)
    - **Normalizar NUDIASOBCO** em faixas (0-120, 121-240, 241-365, 366-730, 730+); descartar outliers > 1460 dias
    - **Normalizar CODMUNOCOR e CODMUNRES** para 6 dígitos (raiz IBGE, zero-pad à esquerda); `CODMUNOCOR` vazio/inválido → sentinela `999999` (FK `codigo_ibge_ocorrencia` NOT NULL) e `CODMUNRES` vazio/inválido → `NULL` (FK `codigo_ibge_residencia` nullable)
    - **Normalizar CODESTAB** (SIM) para o formato do `CO_CNES` (VARCHAR(7), zero-pad à esquerda); vazio/inválido → sentinela `9999999` — alimenta a FK natural `codigo_cnes`
    - Aplicar filtro: `(SEXO_NORMALIZADO = 'F' AND IDADE BETWEEN '410' AND '449') OR (TPMORTEOCO_NORMALIZADO IN ('1','2','3','4','5') AND IDADE BETWEEN '408' AND '465')`
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
- `sus_etl/dimensoes_fixas.py` — Dimensões de domínio fixo, incluindo as de investigação (NOVO)
- `sus_etl/dimensoes_geograficas.py` — Dim_Regiao, Dim_UF, Dim_Municipio (NOVO)
- `sus_etl/dimensoes_cnes.py` — Dim_EstabelecimentoSaude + sub-dimensões (NOVO)
- `sus_etl/dimensao_tempo.py` — Dim_Tempo (ano) (NOVO)
- `sus_etl/dimensao_cid.py` — Dim_CID role-playing (NOVO)
- `sus_etl/fact_table.py` — Fact_MorteMaterna (NOVO)
- `sus_etl/main.py` — Integrar pipeline (MODIFICAR)
- `sus_etl/validacao.py` — Validações pós-carga (NOVO)

### Como referência:
- `modelo.md` — Modelo dimensional e decisões de EDA (fonte da verdade)
- `arquivos/CNES/cnes_estabelecimentos.csv` — Fonte de dados CNES
- `arquivos/SIM/dados_*.csv` (2014–2024) — Fonte de dados SIM
- `exploracoes/analisa_variaveis_dim.ipynb` — EDA que validou as decisões de colunas
- `sus_etl/database.py` — Conexão PostgreSQL + engine SQLAlchemy
- `sus_etl/processing.py` — Padrão de carga staging (referência)

---

## Verificação

1. Executar pipeline ETL completo do staging até star schema
2. `SELECT COUNT(*) FROM Fact_MorteMaterna` deve bater com total de registros do filtro: `(SEXO_NORMALIZADO = 'F' AND IDADE BETWEEN '410' AND '449') OR (TPMORTEOCO_NORMALIZADO IN ('1','2','3','4','5') AND IDADE BETWEEN '408' AND '465')`
3. Nenhum FK na fato deve apontar para ID inexistente nas dimensões
4. Colunas NOT NULL (id_tempo, codigo_ibge_ocorrencia, id_causa_basica) sem NULLs
5. Ao menos 1 registro por ano de dado disponível
6. Consultas analíticas de exemplo funcionam (ex: óbitos por ano × raça_cor × região)

---

## Pendências (herdadas de `modelo.md`)

- Dicionarizar os atributos do CNES em `modelo.md` (códigos/descrições das sub-dimensões)
- Conferir `LOCOCOR` contra o tipo de estabelecimento registrado no CNES
- Conferir `codigo_ibge` do estabelecimento (CNES, `CO_IBGE`) contra `CODMUNOCOR` do SIM
