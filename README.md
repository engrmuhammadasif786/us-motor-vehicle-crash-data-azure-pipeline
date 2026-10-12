# 🚗 U.S. Motor Vehicle Crash Data Pipeline

An end-to-end batch data pipeline for analyzing fatal crash data from the **NHTSA Fatality Analysis Reporting System (FARS)**.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   NHTSA     │────▶│  Azure Blob  │────▶│  Snowflake  │────▶│  Streamlit   │
│  FARS CSV   │     │  (Data Lake) │     │   (DWH)     │     │  Dashboard   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │                    ▲
                            │                    │
                       ┌────┴────┐        ┌─────┴──────┐
                       │ Prefect │        │    dbt     │
                       │(Extract │        │(Transform) │
                       │ & Load) │        └────────────┘
                       └─────────┘
```

**Tech Stack:**
- **Cloud:** Azure (Blob Storage)
- **IaC:** Pulumi
- **Orchestration:** Prefect
- **Data Warehouse:** Snowflake (prod) / DuckDB (local dev)
- **Transformations:** dbt
- **Dashboards:** Streamlit (primary), Power BI (bonus)

## Project Structure

```
.
├── dashboards/
│   ├── streamlit/          # Streamlit dashboard app
│   └── powerbi/            # Power BI files (bonus)
├── data/                   # Local data storage (gitignored)
├── dbt/
│   ├── models/
│   │   ├── staging/        # Staging models (cleaned FARS data)
│   │   └── marts/          # Fact & dimension tables
│   ├── dbt_project.yml
│   └── profiles.yml        # Dual targets: dev (DuckDB) / prod (Snowflake)
├── infrastructure/
│   └── pulumi/             # Azure infrastructure as code
├── pipelines/
│   └── prefect/            # Prefect flows & tasks
│       ├── flows.py        # Main pipeline orchestration
│       └── tasks/          # Extract, upload, load tasks
├── tests/                  # Unit tests
├── docker-compose.yml      # Local services (Azurite, Prefect)
├── Makefile                # Common commands
├── pyproject.toml          # Python dependencies
└── README.md               # This file
```

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Azure CLI (for production)
- Pulumi CLI (for infrastructure)
- Snowflake account (for production)

## Setup

### 1. Clone and Install

```bash
git clone <repo-url>
cd us-motor-vehicle-crash-data-azure-pipeline
pip install -e ".[all]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Local Development

Local development uses **Azurite** (Azure Storage emulator) and **DuckDB** to avoid cloud costs.

### Start Local Services

```bash
make up
```

This starts:
- Azurite (Blob Storage emulator) on port 10000
- Prefect Orion UI on port 4200

### Run the Pipeline

```bash
make pipeline
```

This executes the full flow: extract → upload → load → dbt build.

### Run dbt Manually

```bash
make dbt-build
# or for production
DBT_TARGET=prod make dbt-build
```

### Launch Dashboard

```bash
make dashboard
```

Open http://localhost:8501 to view the Streamlit dashboard.

## Production Deployment

### 1. Provision Infrastructure

```bash
cd infrastructure/pulumi
pulumi stack init prod
pulumi config set azure-native:location EastUS
pulumi config set env prod
pulumi up
```

### 2. Set Production Environment Variables

Update `.env` with production values:
- Azure Storage account credentials
- Snowflake connection details
- `ENV=prod`

### 3. Run Production Pipeline

```bash
ENV=prod DBT_TARGET=prod make pipeline
```

## Dashboard

The Streamlit dashboard includes:

1. **Crash Distribution by Light Condition** (categorical bar chart)
2. **Crash Trend Over Time** (temporal line chart)

Plus bonus visualizations: Top States, Weather Conditions.

### Power BI (Bonus)

A Power BI report is included under `dashboards/powerbi/` for enterprise BI use cases.

## Evaluation Criteria Mapping

| Criteria | Implementation |
|----------|---------------|
| **Problem Description** | This README + inline documentation |
| **Cloud + IaC** | Azure Blob Storage provisioned via Pulumi |
| **Data Ingestion (Batch)** | Prefect orchestrated DAG: extract → upload → load |
| **Data Warehouse** | Snowflake (prod) with partitioned/clustered tables; DuckDB (dev) |
| **Transformations** | dbt models: staging → marts (fact + dimensions) |
| **Dashboard** | Streamlit (2 required tiles + extras), Power BI bonus |
| **Reproducibility** | Docker Compose, Makefile, `.env.example`, comprehensive README |

## Extra Mile

- ✅ **Tests:** pytest unit tests in `tests/`
- ✅ **Makefile:** Standardized commands for local/prod parity
- 🔄 **CI/CD:** GitHub Actions workflow skeleton (see `.github/workflows/`)

## Data Source

[NHTSA FARS - Fatality Analysis Reporting System](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars)

Annual CSV files are downloaded from NHTSA's public FTP/HTTP endpoints.

## License

MIT
