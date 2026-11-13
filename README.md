# E-commerce Sales Data Pipeline

A complete beginner-friendly Data Engineering project using **Python, Pandas, SQL and PostgreSQL**.

The pipeline reads raw customer, product, order and order-item CSV files; validates and transforms them;
loads the data into a relational PostgreSQL database; and generates daily and monthly sales reports.

## What you will learn

- Extracting structured data from CSV files
- Data cleaning and validation with Pandas
- Relational database design and foreign keys
- Loading data safely with PostgreSQL upserts
- SQL aggregations for daily and monthly reporting
- Logging, error handling and automated tests
- Running PostgreSQL locally with Docker

## Architecture

```text
      data/raw/
  customers.csv  products.csv
  orders.csv     order_items.csv
          |
          v
   EXTRACT (Pandas)
          |
          v
 TRANSFORM + VALIDATE
  - normalize text
  - parse dates and numbers
  - validate keys and values
  - identify rejected rows
          |
          v
       LOAD
  PostgreSQL tables:
  customers, products,
  orders, order_items
          |
          v
       REPORTS
  daily_sales.csv
  monthly_sales.csv
```

## Project structure

```text
ecommerce_sales_data_pipeline/
├── data/
│   ├── raw/
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   └── processed/
├── reports/
├── sql/
│   ├── schema.sql
│   └── reports.sql
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── extract.py
│   ├── transform.py
│   ├── database.py
│   ├── load.py
│   ├── report.py
│   └── pipeline.py
├── tests/
│   ├── test_transform.py
│   └── test_reports.py
├── .env.example
├── .gitignore
├── docker-compose.yml
└── requirements.txt
```

## 1. Requirements

- Python 3.10+
- Docker Desktop (recommended) OR a local PostgreSQL server

On Windows, open CMD or the VS Code terminal in this project folder.

## 2. Create and activate a virtual environment

```cmd
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

If virtual-environment creation gives a Windows permission error, try a new writable folder such as
`D:\PythonProjects`, copy this project there, and run the commands again. Do not run `pytest` until
the environment is activated and dependencies are installed.

Install packages:

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Configure environment variables

Copy the example file:

```cmd
copy .env.example .env
```

The default settings are for local development only:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce_dw
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_password
```

Do not commit `.env` or use these sample credentials in production.

## 4. Start PostgreSQL

With Docker Desktop running:

```cmd
docker compose up -d
```

Check the database container:

```cmd
docker compose ps
```

If port 5432 is already in use, change the host mapping in `docker-compose.yml` from
`5432:5432` to `5433:5432`, and set `DB_PORT=5433` in `.env`.

Stop the database:

```cmd
docker compose down
```

Delete the database and its stored volume (this permanently removes local project data):

```cmd
docker compose down -v
```

## 5. Run the complete pipeline

```cmd
python -m src.pipeline
```

The pipeline will:
1. Read all four CSV files from `data/raw/`.
2. Validate and transform records.
3. Save rejected records to `data/processed/`.
4. Create PostgreSQL tables if they do not exist.
5. Load customers and products before orders and order items.
6. Generate daily and monthly reports in `reports/`.

Expected final log message:

```text
Pipeline completed successfully
```

The exact row counts depend on the sample files and any changes you make.

## 6. Run automated tests

```cmd
python -m pytest -v
```

The unit tests validate transformation and reporting logic. They do not require PostgreSQL or Docker.

## 7. Inspect the database

Open a PostgreSQL shell:

```cmd
docker exec -it ecommerce-sales-postgres psql -U ecommerce_user -d ecommerce_dw
```

Try these queries:

```sql
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM order_items;

SELECT * FROM daily_sales ORDER BY sales_date;
SELECT * FROM monthly_sales ORDER BY sales_month;
```

Exit with:

```text
\q
```

## 8. Example business questions

The generated reports help answer:
- How much revenue did the store generate each day?
- Which month had the highest revenue?
- How many orders were placed?
- What was the average order value?
- Which products generated the most revenue?

Revenue is calculated as `quantity * unit_price` from order items. This sample project does not model
discounts, refunds, shipping fees or tax; add those fields if you want a more realistic business model.

## Data quality rules

- IDs must be present.
- Customer emails must have a basic valid email format.
- Product prices must be zero or greater.
- Order dates must be parseable.
- Order customers and order-item references must exist in the corresponding input files.
- Order item quantity must be a positive integer.
- Order item unit price must be zero or greater.
- Duplicate IDs are rejected after the first occurrence.

Rejected records are written to `data/processed/` as CSV files with a `rejection_reason` column.

## Idempotency

The database tables use primary keys and PostgreSQL `ON CONFLICT` upserts. Running the pipeline again
updates existing records rather than inserting duplicate IDs. The pipeline loads parent records before
dependent records to respect foreign-key constraints.

## GitHub upload

Create an empty GitHub repository, then run:

```cmd
git init
git add .
git commit -m "Build e-commerce sales data pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ecommerce-sales-data-pipeline.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Suggested improvements

1. Add incremental loading using `updated_at` timestamps.
2. Add discounts, refunds, shipping and tax calculations.
3. Schedule the pipeline using Apache Airflow.
4. Store raw files in Amazon S3.
5. Add a dashboard using Power BI or Metabase.
6. Add data quality checks with Great Expectations or dbt tests.
