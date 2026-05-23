import requests
import pandas as pd
from sqlalchemy import create_engine, text, types

print("1. กำลังดูดข้อมูลจาก Frankfurter API...")
url = "https://api.frankfurter.app/latest?from=USD&to=THB,JPY,EUR"
response = requests.get(url)
data = response.json()  # แปลงเป็น Python Dictionary

print("\n2. กำลัง Transform ข้อมูล...")
# ดึงข้อมูลส่วนหัวเก็บไว้ก่อน
record_date = data['date']
base_curr = data['base']
rates_dict = data['rates']  # จุดนี้คือตัวปัญหาที่เราต้องแงะ

# สร้าง List เปล่าๆ มารอรับข้อมูลที่จะจัดทรงแล้ว
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
print("---Data to be loaded into database---\n", df)

df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['base_currency'] = df['base_currency'].astype('string')
df['target_currency'] = df['target_currency'].astype('string')
df['rate'] = pd.to_numeric(df['rate'], errors='coerce')

df.dropna(subset=['date', 'target_currency'], inplace=True)

engine = create_engine(
    'postgresql://postgres:hgzz@localhost:5432/my_first_etl')
df.to_sql('staging_exchange_rate', engine, if_exists='replace', index=False,
          dtype={
              'date': types.Date(),
              'base_currency': types.String(),
              'target_currency': types.String(),
              'rate': types.Float()
          })

# Commit upsert
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

with engine.connect() as conn:
    conn.execute(text(upsert_query))
    conn.commit()

print("---Completed, UPSERT SUCCESS!!---")

engine.dispose()
