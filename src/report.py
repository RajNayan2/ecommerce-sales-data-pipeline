from pathlib import Path
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

DAILY_SQL = text('''
SELECT
    DATE(o.order_date) AS sales_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS revenue,
    ROUND(
      COALESCE(SUM(oi.quantity * oi.unit_price), 0)
      / NULLIF(COUNT(DISTINCT o.order_id), 0), 2
    ) AS average_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE LOWER(o.status) NOT IN ('cancelled', 'canceled')
GROUP BY DATE(o.order_date)
ORDER BY sales_date
''')

MONTHLY_SQL = text('''
SELECT
    DATE_TRUNC('month', o.order_date)::date AS sales_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS revenue,
    ROUND(
      COALESCE(SUM(oi.quantity * oi.unit_price), 0)
      / NULLIF(COUNT(DISTINCT o.order_id), 0), 2
    ) AS average_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE LOWER(o.status) NOT IN ('cancelled', 'canceled')
GROUP BY DATE_TRUNC('month', o.order_date)::date
ORDER BY sales_month
''')


def build_daily_report(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """Pure-Pandas daily aggregation, also used by unit tests."""
    if orders.empty or order_items.empty:
        return pd.DataFrame(columns=[
            "sales_date", "total_orders", "unique_customers",
            "units_sold", "revenue", "average_order_value"
        ])
    eligible = orders[~orders["status"].str.lower().isin(["cancelled", "canceled"])].copy()
    merged = eligible.merge(order_items, on="order_id", how="inner")
    merged["sales_date"] = pd.to_datetime(merged["order_date"]).dt.date
    merged["line_revenue"] = merged["quantity"] * merged["unit_price"]
    result = merged.groupby("sales_date", as_index=False).agg(
        total_orders=("order_id", "nunique"),
        unique_customers=("customer_id", "nunique"),
        units_sold=("quantity", "sum"),
        revenue=("line_revenue", "sum"),
    )
    result["average_order_value"] = (
        result["revenue"] / result["total_orders"]
    ).round(2)
    result["revenue"] = result["revenue"].round(2)
    return result


def build_monthly_report(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    daily = build_daily_report(orders, order_items)
    if daily.empty:
        return pd.DataFrame(columns=[
            "sales_month", "total_orders", "unique_customers",
            "units_sold", "revenue", "average_order_value"
        ])
    daily["sales_month"] = pd.to_datetime(daily["sales_date"]).dt.to_period("M").dt.to_timestamp().dt.date
    # Re-aggregate from order-level rows to ensure unique order/customer counts per month.
    eligible = orders[~orders["status"].str.lower().isin(["cancelled", "canceled"])].copy()
    merged = eligible.merge(order_items, on="order_id", how="inner")
    merged["sales_month"] = pd.to_datetime(merged["order_date"]).dt.to_period("M").dt.to_timestamp().dt.date
    merged["line_revenue"] = merged["quantity"] * merged["unit_price"]
    result = merged.groupby("sales_month", as_index=False).agg(
        total_orders=("order_id", "nunique"),
        unique_customers=("customer_id", "nunique"),
        units_sold=("quantity", "sum"),
        revenue=("line_revenue", "sum"),
    )
    result["average_order_value"] = (result["revenue"] / result["total_orders"]).round(2)
    result["revenue"] = result["revenue"].round(2)
    return result


def generate_reports(engine: Engine, reports_dir: Path):
    reports_dir.mkdir(parents=True, exist_ok=True)
    with engine.connect() as connection:
        daily = pd.read_sql(DAILY_SQL, connection)
        monthly = pd.read_sql(MONTHLY_SQL, connection)
    daily.to_csv(reports_dir / "daily_sales.csv", index=False)
    monthly.to_csv(reports_dir / "monthly_sales.csv", index=False)
    return daily, monthly
