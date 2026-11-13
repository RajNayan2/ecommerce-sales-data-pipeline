import pandas as pd
from src.report import build_daily_report, build_monthly_report


def sample_tables():
    orders = pd.DataFrame([
        {"order_id": "O1", "customer_id": "C1", "order_date": "2026-01-02", "status": "paid"},
        {"order_id": "O2", "customer_id": "C2", "order_date": "2026-01-02", "status": "paid"},
        {"order_id": "O3", "customer_id": "C1", "order_date": "2026-02-05", "status": "cancelled"},
    ])
    items = pd.DataFrame([
        {"order_item_id": "I1", "order_id": "O1", "product_id": "P1", "quantity": 2, "unit_price": 10.0},
        {"order_item_id": "I2", "order_id": "O2", "product_id": "P2", "quantity": 1, "unit_price": 20.0},
        {"order_item_id": "I3", "order_id": "O3", "product_id": "P1", "quantity": 1, "unit_price": 10.0},
    ])
    return orders, items


def test_daily_report_calculates_revenue_and_orders():
    orders, items = sample_tables()
    report = build_daily_report(orders, items)
    assert len(report) == 1
    assert report.loc[0, "total_orders"] == 2
    assert report.loc[0, "units_sold"] == 3
    assert report.loc[0, "revenue"] == 40.0
    assert report.loc[0, "average_order_value"] == 20.0


def test_monthly_report_excludes_cancelled_orders():
    orders, items = sample_tables()
    report = build_monthly_report(orders, items)
    assert len(report) == 1
    assert report.loc[0, "revenue"] == 40.0
    assert report.loc[0, "total_orders"] == 2
