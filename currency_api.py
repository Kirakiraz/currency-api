import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, types

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

print("1. Retrieving data from Frankfurter API...")
url = "https://api.frankfurter.app/latest?from=USD&to=THB,JPY,EUR"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"API Error: Failed to retrieve dataset Reason: {e}")
    sys.exit(1)

print("\n2. Transforming data...")
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

print("---Data to be loaded into database---\n", df)

print("\n3. Uploading data to staging table...")
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

    # Commit upsert
        print("\n4. Uploading data to prod. table...")
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
        print("---Completed, UPSERT SUCCESS!!---")
except Exception as e:
    print(f"Database error: {e}")
finally:
    engine.dispose()
