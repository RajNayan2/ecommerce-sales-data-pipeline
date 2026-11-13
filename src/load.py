import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

SCHEMA_SQL = [
    '''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_name VARCHAR(150) NOT NULL,
        email VARCHAR(255) NOT NULL,
        city VARCHAR(100) NOT NULL,
        signup_date DATE NOT NULL
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS products (
        product_id VARCHAR(50) PRIMARY KEY,
        product_name VARCHAR(150) NOT NULL,
        category VARCHAR(100) NOT NULL,
        list_price NUMERIC(12, 2) NOT NULL CHECK (list_price >= 0)
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS orders (
        order_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
        order_date TIMESTAMP NOT NULL,
        status VARCHAR(30) NOT NULL
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
        product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0)
    )
    '''
]

UPSERTS = {
    "customers": text('''
        INSERT INTO customers (customer_id, customer_name, email, city, signup_date)
        VALUES (:customer_id, :customer_name, :email, :city, :signup_date)
        ON CONFLICT (customer_id) DO UPDATE SET
          customer_name=EXCLUDED.customer_name, email=EXCLUDED.email,
          city=EXCLUDED.city, signup_date=EXCLUDED.signup_date
    '''),
    "products": text('''
        INSERT INTO products (product_id, product_name, category, list_price)
        VALUES (:product_id, :product_name, :category, :list_price)
        ON CONFLICT (product_id) DO UPDATE SET
          product_name=EXCLUDED.product_name, category=EXCLUDED.category,
          list_price=EXCLUDED.list_price
    '''),
    "orders": text('''
        INSERT INTO orders (order_id, customer_id, order_date, status)
        VALUES (:order_id, :customer_id, :order_date, :status)
        ON CONFLICT (order_id) DO UPDATE SET
          customer_id=EXCLUDED.customer_id, order_date=EXCLUDED.order_date,
          status=EXCLUDED.status
    '''),
    "order_items": text('''
        INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
        VALUES (:order_item_id, :order_id, :product_id, :quantity, :unit_price)
        ON CONFLICT (order_item_id) DO UPDATE SET
          order_id=EXCLUDED.order_id, product_id=EXCLUDED.product_id,
          quantity=EXCLUDED.quantity, unit_price=EXCLUDED.unit_price
    ''')
}


def _records(frame: pd.DataFrame, table: str):
    if frame.empty:
        return []
    data = frame.copy()
    if table == "customers":
        data["signup_date"] = pd.to_datetime(data["signup_date"]).dt.date
    if table == "orders":
        data["order_date"] = pd.to_datetime(data["order_date"]).dt.to_pydatetime()
    # Only send columns that exist in the destination table.
    columns = {
        "customers": ["customer_id", "customer_name", "email", "city", "signup_date"],
        "products": ["product_id", "product_name", "category", "list_price"],
        "orders": ["order_id", "customer_id", "order_date", "status"],
        "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    }[table]
    return data[columns].to_dict(orient="records")


def load_tables(valid_tables: dict, engine: Engine):
    """Create tables and upsert rows in parent-to-child order, atomically."""
    counts = {}
    with engine.begin() as connection:
        for statement in SCHEMA_SQL:
            connection.execute(text(statement))
        for table in ["customers", "products", "orders", "order_items"]:
            records = _records(valid_tables[table], table)
            if records:
                connection.execute(UPSERTS[table], records)
            counts[table] = len(records)
            logger.info("Loaded or updated %d rows into %s", len(records), table)
    return counts
