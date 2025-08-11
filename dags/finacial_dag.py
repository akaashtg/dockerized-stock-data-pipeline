# dags/financial_data_import.py
import datetime
import logging
import os
import requests
import pendulum
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowSkipException

API_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")  # Store this in env var or Airflow Variable


@task()
def get_tickers_from_db():
    """Fetch list of tickers from the database."""
    hook = PostgresHook(postgres_conn_id="postgres_default")
    sql = "SELECT DISTINCT ticker FROM public.tickers_list;"  # Example table containing tickers
    records = hook.get_records(sql)
    tickers = [row[0] for row in records]

    if not tickers:
        raise AirflowSkipException("No tickers found in database.")
    logging.info("Loaded %d tickers from DB", len(tickers))
    return tickers


@task(retries=2, retry_delay=datetime.timedelta(seconds=30))
def fetch_stock_data(tickers):
    """Fetch latest stock data from Alpha Vantage in JSON format."""
    all_data = []

    if not API_KEY:
        raise ValueError("Missing Alpha Vantage API key in environment variables.")

    for symbol in tickers:
        try:
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "apikey": API_KEY
            }
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()

            json_data = response.json()
            time_series = json_data.get("Time Series (Daily)")

            if not time_series:
                logging.warning("No data returned for %s", symbol)
                continue

            # Get the latest date available
            latest_date = sorted(time_series.keys())[-1]
            latest_info = time_series[latest_date]

            all_data.append({
                "closing_date": latest_date,
                "ticker": symbol,
                "adjusted_close": float(latest_info["5. adjusted close"])
            })

        except Exception as e:
            logging.exception("Error fetching data for %s: %s", symbol, e)
            continue

    if not all_data:
        raise AirflowSkipException("No stock data fetched from Alpha Vantage.")

    return all_data


@task()
def upsert_postgres(rows):
    """Upsert rows into PostgreSQL table."""
    hook = PostgresHook(postgres_conn_id="postgres_default")
    sql = """
    INSERT INTO public.sp500 (closing_date, ticker, adjusted_close)
    VALUES (%(closing_date)s, %(ticker)s, %(adjusted_close)s)
    ON CONFLICT (closing_date, ticker)
    DO UPDATE SET adjusted_close = EXCLUDED.adjusted_close;
    """
    hook.run(sql, parameters=rows)
    logging.info("Upserted %d rows into Postgres", len(rows))


@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
)
def financial_data_pipeline():
    tickers = get_tickers_from_db()
    data = fetch_stock_data(tickers)
    upsert_postgres(data)


financial_data_pipeline_dag = financial_data_pipeline()
