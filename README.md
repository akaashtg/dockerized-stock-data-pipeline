# dockerized-stock-market-pipeline with Airflow & CrateDB

## Overview
This project implements a **Dockerized data pipeline** using **Apache Airflow** to fetch, process, and store stock market data.  
It was bootstrapped with the Astronomer CLI (`astro dev init`) and extended to meet the requirements of the assignment.

The pipeline:
- Fetches daily stock market data from the **Alpha Vantage API**.
- Extracts the **adjusted closing price** for each ticker.
- Stores the data in a **CrateDB table** (`sp500`) via Airflow’s `PostgresHook`.
- Is fully containerized with **Airflow**, **CrateDB**, and **Postgres** (for Airflow metadata).

---



---

## Project Contents

```
.
├── dags/
│   └── financial_data_pipeline.py   # Main Airflow DAG (code1)
├── plugins/                         # Custom plugins (empty)
├── logs/                            # Airflow logs (auto-generated)
├── docker-compose.yml               # Runs Airflow + CrateDB + Postgres
├── .env                             # API keys and DB connection URIs
├── .astro/config.yaml               # Astronomer local config
├── Dockerfile                       # Astronomer Runtime image
├── packages.txt                     # OS packages (empty by default)
├── requirements.txt                 # Python packages (empty by default)
├── airflow_settings.yaml             # Local-only Airflow settings
└── README.md                        # This file
```

---

## How the DAG Works
The DAG (`financial_data_pipeline.py`) contains:
1. **get_tickers_from_db** — Reads tickers from the `tickers_list` table in CrateDB.
2. **fetch_stock_data** — Calls the Alpha Vantage API for each ticker and retrieves the latest adjusted close price.
3. **upsert_postgres** — Inserts or updates rows in the `sp500` table using `ON CONFLICT`.

The DAG is scheduled **daily** but can be adjusted via the DAG definition.

---

## Running the Project Locally

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed and running.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.
- Astronomer CLI (`brew install astro` on macOS, or see [docs](https://www.astronomer.io/docs/astro/cli/install-cli)).

---

### 2. Set up `.env`
Create a `.env` file in the project root:
```env
# Alpha Vantage API key
ALPHA_VANTAGE_KEY=YOUR_API_KEY_HERE

# CrateDB connection for Airflow
AIRFLOW_CONN_CRATEDB_CONNECTION=postgresql://crate:@cratedb:5432/doc?sslmode=disable
```

---

### 3. Start Services

#### Option A — Run via Astronomer (development mode)
```bash
astro dev start
```
- Airflow Web UI → [http://localhost:8081](http://localhost:8081) (port set in `.astro/config.yaml`)
- CrateDB Admin UI → [http://localhost:4200](http://localhost:4200)

#### Option B — Run via Docker Compose (assignment-ready)
```bash
docker-compose up
```
- Airflow Web UI → [http://localhost:8080](http://localhost:8080)
- CrateDB Admin UI → [http://localhost:4200](http://localhost:4200)

---

### 4. Create the Target Table in CrateDB
Run this SQL in CrateDB Admin UI or via `psql`:
```sql
CREATE TABLE IF NOT EXISTS sp500 (
   closing_date TIMESTAMP,
   ticker TEXT,
   adjusted_close DOUBLE,
   PRIMARY KEY (closing_date, ticker)
);
```

---

### 5. Trigger the DAG
1. Open Airflow Web UI.
2. Unpause the `financial_data_pipeline` DAG.
3. Trigger manually or wait for the scheduled run.

---

## Deployment
You can deploy this project to any Astronomer Deployment or Airflow environment by copying:
- `dags/financial_data_pipeline.py`
- `.env`
- `docker-compose.yml`

---

## Contact
For Alpha Vantage API documentation: [https://www.alphavantage.co/documentation/](https://www.alphavantage.co/documentation/)  
For Astronomer CLI docs: [https://www.astronomer.io/docs/astro/cli](https://www.astronomer.io/docs/astro/cli)
