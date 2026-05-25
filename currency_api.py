import os
import sys
import requests
import pandas as pd
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, types

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

logger.info("Retrieving data from Frankfurter API...")
url = "https://api.frankfurter.app/latest?from=USD&to=THB,JPY,EUR"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    logger.error(f"API Error: Failed to retrieve dataset Reason: {e}")
    sys.exit(1)

logger.info("Transforming data...")
record_date = data['date']
base_curr = data['base']
rates_dict = data['rates']

# สร้าง List เปล่าๆ
rows = []

for target_curr, target_rate in rates_dict.items():
    rows.append({
        'date': record_date,
        'base_currency': base_curr,
        'target_currency': target_curr,
        'rate': target_rate
    })
df = pd.DataFrame(rows)

# ---Final result (Transformed data)---
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['base_currency'] = df['base_currency'].astype('string')
df['target_currency'] = df['target_currency'].astype('string')
df['rate'] = pd.to_numeric(df['rate'], errors='coerce')

df.dropna(subset=['date', 'target_currency'], inplace=True)

logger.info(f"---Data to be loaded into database---\n{df}")

logger.info("Uploading data to staging table...")
engine = None
try:
    engine = create_engine(
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    with engine.connect() as conn:

        df.to_sql('staging_exchange_rate', engine, if_exists='replace', index=False,
                  dtype={
                      'date': types.Date(),
                      'base_currency': types.String(),
                      'target_currency': types.String(),
                      'rate': types.Float()
                  })

        # Commit upsert to prod table
        logger.info("Uploading data to prod. table...")
        upsert_query = """
            INSERT INTO exchange_rate (date, base_currency, target_currency, rate)
            SELECT date, base_currency, target_currency, rate
            FROM staging_exchange_rate
            ON CONFLICT (date, target_currency)
            DO UPDATE SET
                base_currency = EXCLUDED.base_currency,
                rate = EXCLUDED.rate,
                updated_at = CURRENT_TIMESTAMP;
        """
        conn.execute(text(upsert_query))
        conn.commit()
        logger.info("---Completed, UPSERT SUCCESS!!---")
except Exception as e:
    logger.error(f"Database error: {e}")
finally:
    if engine:
        engine.dispose()
