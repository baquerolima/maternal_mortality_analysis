# Maternal Mortality Analysis (Brazil)

Data analysis project on maternal mortality in Brazil, using public data from the Brazilian Unified Health System (SUS).

## Project Overview

Maternal mortality is a critical public health indicator and a key target of the UN Sustainable Development Goals (SDG 3.1 — reduce the global maternal mortality ratio to less than 70 per 100,000 live births). This project aims to collect, organize, and analyze publicly available data from multiple Brazilian health information systems to enable insights into maternal deaths across the country.

### Data Sources

| Source | Description | Period |
|---|---|---|
| **SIM** (Mortality Information System) | Death records with cause of death (ICD-10), demographics, and circumstances | 2014–2024 |
| **CNES** (National Registry of Health Establishments) | Healthcare facility data: type, management, location, infrastructure | Current |
| **SINASC** (Live Birth Information System) | Live birth records for rate calculations | 2014–2023 |

### Subject of Analysis

The core analysis focuses on **potentially maternal deaths** — deaths of women of childbearing age (10–49 years) or any individual with a gestational-related death marker. The filtering criteria are:

1. **Primary rule:** Female sex (`SEXO = 'F'`) AND age between 10 and 49 years (`IDADE` between `410` and `449` — the SIM encoding where the first digit `4` = years, followed by the age value)
2. **Quality check exception:** Male or ignored sex (`SEXO IN ('M','I')`) with a gestational death marker (`TPMORTEOCO` in 1–5), capturing potential trans individuals or data entry errors

Each death record is enriched with:
- **ICD-10 cause of death** (basic cause, maternal cause, original cause) — a role-playing dimension
- **Geographic hierarchy** (municipality → state → region) for both occurrence and residence
- **Healthcare establishment** where the death occurred (with CNES-derived attributes: type, management hierarchy, administrative sphere, and infrastructure flags like obstetric/neonatal center availability)
- **Demographic dimensions** (age group, race/color, sex)
- **Obstetric context** (pregnancy type, delivery type, gestational age, moment of death relative to delivery, location of occurrence)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Future Front-End                          │
│           Angular / TypeScript Dashboards                    │
│                        ⬇ (API)                              │
├─────────────────────────────────────────────────────────────┤
│                   Supabase (PostgreSQL)                      │
│    ┌──────────────────────────────────────────────────┐      │
│    │           Snowflake Dimensional Model             │      │
│    │  ┌──────────┐    ┌────────────────────────────┐   │      │
│    │  │ Dim_*    │◄───│  Fact_MorteMaterna         │   │      │
│    │  │ (14 dims)│    │  (measures + foreign keys) │   │      │
│    │  └──────────┘    └────────────────────────────┘   │      │
│    └──────────────────────────────────────────────────┘      │
│                        ⬆                                    │
├─────────────────────────────────────────────────────────────┤
│                  Python ETL Pipeline                          │
│    ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐   │
│    │ SIM      │  │ CNES     │  │ SINASC                  │   │
│    │ (CSV)    │  │ (CSV)    │  │ (CSV)                   │   │
│    └────┬─────┘  └────┬─────┘  └──────────┬──────────────┘   │
│         └──────────────┴────────────────────┘                 │
│                           ⬇                                   │
│                    SQLAlchemy ORM                              │
│                           ⬇                                   │
│              Dimensional Load (Snowflake)                      │
└─────────────────────────────────────────────────────────────┘
```

### ETL Pipeline (Python)

The ETL pipeline is built in **Python** using **SQLAlchemy** for database interaction and **Pandas** for data processing:

1. **Staging Load** — Raw CSV files from SIM, CNES, and SINASC are loaded into staging tables
2. **Sex Normalization** — Raw sex values (1/2/F/M/I/0/9) are mapped to a controlled vocabulary: `'F'`, `'M'`, `'I'`
3. **Maternal Death Filter** — Applies the combined criteria (age + sex + gestational marker)
4. **Dimension Loading** — Populates 14 dimension tables, including:
   - **Fixed domain dimensions** (race/color, location of occurrence, pregnancy type, etc.) — loaded from predefined dictionaries
   - **Geographic dimensions** (region, state, municipality) — extracted from SIM and CNES data
   - **Healthcare establishment dimension** with snowflake sub-dimensions (management type, hierarchy level, administrative sphere, unit type, legal nature, organization nature)
   - **Time dimension** — generated from death dates (2014–2023+)
   - **ICD-10 dimension** — extracted from cause-of-death fields with descriptions
5. **Fact Table Population** — Aggregated death counts per unique combination of dimensions

### Database (Supabase / PostgreSQL)

The analytical database is hosted on **Supabase**, a managed PostgreSQL service:
- **PostgreSQL** with full SQL analytics capabilities
- **Snowflake dimensional model** (star schema with snowflake sub-dimensions)
- Optimized for analytical queries with proper indexing and foreign key constraints
- Schema includes ~20 tables: 1 fact table, 14 dimensions, plus snowflake sub-dimensions for healthcare establishments

### Future: Front-End (Angular / TypeScript)

A future **Angular / TypeScript** web application will consume the analytical data and present interactive dashboards featuring:
- Maternal mortality trends over time (yearly, quarterly)
- Geographic distribution maps (by region, state, municipality)
- Demographic breakdowns (age group, race/color)
- Healthcare establishment infrastructure analysis
- ICD-10 cause-of-death analysis
- Filterable and cross-linked visualizations

## Project Structure

```
sus_etl/                          # ETL Pipeline
├── main.py                       # Pipeline orchestrator
├── database.py                   # PostgreSQL/SQLAlchemy connection
├── processing.py                 # Staging load logic
├── ckan.py                       # CKAN API data harvesting
├── metadata.py                   # Load metadata tracking
├── schemas/
│   └── star_schema.sql           # DDL for dimensional model
├── dimensoes_fixas.py            # Fixed domain dimensions
├── dimensoes_geograficas.py      # Geographic dimensions
├── dimensoes_cnes.py             # CNES/health establishment dimensions
├── dimensao_tempo.py             # Time dimension
├── dimensao_cid.py               # ICD-10 dimension
├── fact_table.py                 # Fact table population
└── validacao.py                  # Post-load validation
arquivos/                         # Raw data files
├── SIM/                          # Mortality data (2014–2023)
├── CNES/                         # Healthcare establishments
├── SINASC/                       # Live birth records (2014–2023)
└── registros_mm*.csv             # Processed maternal mortality records
exploracoes/                      # Analysis notebooks & scripts
└── analisa_colunas.ipynb
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
