import pandas as pd
from src.transform import transform_customers, transform_products, transform_orders, transform_order_items


def test_customer_email_and_city_are_normalized():
    raw = pd.DataFrame([{
        "customer_id": " C1 ", "customer_name": " Riya ", "email": "RIYA@EXAMPLE.COM",
        "city": "new delhi", "signup_date": "2026-01-01"
    }])
    valid, rejected = transform_customers(raw)
    assert len(rejected) == 0
    assert valid.loc[0, "customer_id"] == "C1"
    assert valid.loc[0, "email"] == "riya@example.com"
    assert valid.loc[0, "city"] == "New Delhi"


def test_invalid_product_price_is_rejected():
    raw = pd.DataFrame([{
        "product_id": "P1", "product_name": "Mouse", "category": "electronics",
        "list_price": "-5"
    }])
    valid, rejected = transform_products(raw)
    assert len(valid) == 0
    assert "list_price" in rejected.loc[0, "rejection_reason"]


def test_order_with_unknown_customer_is_rejected():
    raw = pd.DataFrame([{
        "order_id": "O1", "customer_id": "UNKNOWN",
        "order_date": "2026-01-01", "status": "paid"
    }])
    valid, rejected = transform_orders(raw, {"C1"})
    assert len(valid) == 0
    assert "customer_id not found" in rejected.loc[0, "rejection_reason"]


def test_order_item_quantity_must_be_positive_integer():
    raw = pd.DataFrame([{
        "order_item_id": "I1", "order_id": "O1", "product_id": "P1",
        "quantity": "1.5", "unit_price": "10"
    }])
    valid, rejected = transform_order_items(raw, {"O1"}, {"P1"})
    assert len(valid) == 0
    assert "positive integer" in rejected.loc[0, "rejection_reason"]
