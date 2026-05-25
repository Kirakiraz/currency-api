# currency-api

A simple ETL pipeline that extracts exchange rate data from a public API, loads it into PostgreSQL, and upserts into a production table daily.

Built as a portfolio project to practice end-to-end pipeline development with Python.

---

## Architecture

```
[Frankfurter API]
      ↓  requests
[Extract & Transform]   ← Python (pandas)
      ↓
[staging_exchange_rate]  ← PostgreSQL (full replace)
      ↓  UPSERT
[exchange_rate]          ← PostgreSQL (production table)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.14.0 |
| Extract | `requests` |
| Transform | `pandas` |
| Load | `SQLAlchemy` + `psycopg2` |
| Database | PostgreSQL |
| Config | `python-dotenv` |

---

## Database Schema

**`staging_exchange_rate`** — temporary table, replaced on each run

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Rate date from API |
| `base_currency` | VARCHAR | Base currency (USD) |
| `target_currency` | VARCHAR | Target currency (THB, JPY, EUR) |
| `rate` | FLOAT | Exchange rate |

**`exchange_rate`** — production table with upsert

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Rate date |
| `base_currency` | VARCHAR | Base currency |
| `target_currency` | VARCHAR | Target currency |
| `rate` | NUMERIC | Exchange rate |
| `updated_at` | TIMESTAMP | Last updated timestamp |

Primary key / conflict target: `(date, target_currency)`

---

## How to Run

**1. Clone the repo**
```bash
git clone https://github.com/Kirakiraz/currency-api.git
cd currency-api
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create `.env` file**
```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
```

**4. Create the production table in PostgreSQL**
```sql
CREATE TABLE IF NOT EXISTS public.exchange_rate (
    date DATE NOT NULL,
    base_currency CHARACTER VARYING(3),
    target_currency CHARACTER VARYING(3) NOT NULL,
    rate NUMERIC(10,4),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT exchange_rate_pkey PRIMARY KEY (date, target_currency)
);
```

**5. Run the pipeline**
```bash
python currency_api.py
```

---

## Data Source

[Frankfurter API](https://www.frankfurter.app/) — free, no API key required

Currencies tracked: `THB`, `JPY`, `EUR` (base: `USD`)

---

## What I Learned

- ETL pipeline structure: extract → transform → load
- Handling API errors and DB connection failures gracefully
- Upsert pattern with `ON CONFLICT` in PostgreSQL
- Managing credentials with `.env` instead of hardcoding
- Python `logging` module vs `print()`
