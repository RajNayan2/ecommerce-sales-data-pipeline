import pandas as pd


def _add_reason(reasons: pd.Series, mask: pd.Series, message: str) -> pd.Series:
    """Append a validation message to rows that fail a rule."""
    reasons = reasons.copy()
    current = reasons.loc[mask]
    reasons.loc[mask] = current.where(current.eq(""), current + "; ") + message
    return reasons


def _split_valid_rejected(data: pd.DataFrame, reasons: pd.Series):
    valid_mask = reasons.eq("")
    valid = data.loc[valid_mask].copy().reset_index(drop=True)
    rejected = data.loc[~valid_mask].copy()
    rejected["rejection_reason"] = reasons.loc[~valid_mask]
    return valid, rejected.reset_index(drop=True)


def transform_customers(raw: pd.DataFrame):
    required = ["customer_id", "customer_name", "email", "city", "signup_date"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"customers.csv missing columns: {missing}")

    data = raw[required].copy()
    data["customer_id"] = data["customer_id"].astype("string").str.strip()
    data["customer_name"] = data["customer_name"].astype("string").str.strip()
    data["email"] = data["email"].astype("string").str.strip().str.lower()
    data["city"] = data["city"].astype("string").str.strip().str.title()
    data["signup_date"] = pd.to_datetime(data["signup_date"], errors="coerce")

    reasons = pd.Series("", index=data.index, dtype="string")
    for col in ["customer_id", "customer_name", "city"]:
        reasons = _add_reason(reasons, data[col].isna() | data[col].eq(""), f"missing {col}")
    email_ok = data["email"].str.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", na=False)
    reasons = _add_reason(reasons, ~email_ok, "invalid email")
    reasons = _add_reason(reasons, data["signup_date"].isna(), "invalid signup_date")
    reasons = _add_reason(reasons, data["customer_id"].duplicated(keep="first"), "duplicate customer_id")
    return _split_valid_rejected(data, reasons)


def transform_products(raw: pd.DataFrame):
    required = ["product_id", "product_name", "category", "list_price"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"products.csv missing columns: {missing}")

    data = raw[required].copy()
    for col in ["product_id", "product_name", "category"]:
        data[col] = data[col].astype("string").str.strip()
    data["category"] = data["category"].str.title()
    data["list_price"] = pd.to_numeric(data["list_price"], errors="coerce")

    reasons = pd.Series("", index=data.index, dtype="string")
    for col in ["product_id", "product_name", "category"]:
        reasons = _add_reason(reasons, data[col].isna() | data[col].eq(""), f"missing {col}")
    reasons = _add_reason(reasons, data["list_price"].isna() | (data["list_price"] < 0),
                          "list_price must be zero or greater")
    reasons = _add_reason(reasons, data["product_id"].duplicated(keep="first"), "duplicate product_id")
    return _split_valid_rejected(data, reasons)


def transform_orders(raw: pd.DataFrame, valid_customer_ids: set):
    required = ["order_id", "customer_id", "order_date", "status"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"orders.csv missing columns: {missing}")

    data = raw[required].copy()
    for col in ["order_id", "customer_id", "status"]:
        data[col] = data[col].astype("string").str.strip()
    data["status"] = data["status"].str.lower()
    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")

    reasons = pd.Series("", index=data.index, dtype="string")
    for col in ["order_id", "customer_id", "status"]:
        reasons = _add_reason(reasons, data[col].isna() | data[col].eq(""), f"missing {col}")
    reasons = _add_reason(reasons, data["order_date"].isna(), "invalid order_date")
    reasons = _add_reason(reasons, ~data["customer_id"].isin(valid_customer_ids),
                          "customer_id not found in valid customers")
    reasons = _add_reason(reasons, data["order_id"].duplicated(keep="first"), "duplicate order_id")
    return _split_valid_rejected(data, reasons)


def transform_order_items(raw: pd.DataFrame, valid_order_ids: set, valid_product_ids: set):
    required = ["order_item_id", "order_id", "product_id", "quantity", "unit_price"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"order_items.csv missing columns: {missing}")

    data = raw[required].copy()
    for col in ["order_item_id", "order_id", "product_id"]:
        data[col] = data[col].astype("string").str.strip()
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")

    reasons = pd.Series("", index=data.index, dtype="string")
    for col in ["order_item_id", "order_id", "product_id"]:
        reasons = _add_reason(reasons, data[col].isna() | data[col].eq(""), f"missing {col}")
    reasons = _add_reason(reasons, ~data["order_id"].isin(valid_order_ids),
                          "order_id not found in valid orders")
    reasons = _add_reason(reasons, ~data["product_id"].isin(valid_product_ids),
                          "product_id not found in valid products")
    reasons = _add_reason(reasons, data["quantity"].isna() | (data["quantity"] <= 0)
                          | (data["quantity"] % 1 != 0), "quantity must be a positive integer")
    reasons = _add_reason(reasons, data["unit_price"].isna() | (data["unit_price"] < 0),
                          "unit_price must be zero or greater")
    reasons = _add_reason(reasons, data["order_item_id"].duplicated(keep="first"),
                          "duplicate order_item_id")

    valid, rejected = _split_valid_rejected(data, reasons)
    if not valid.empty:
        valid["quantity"] = valid["quantity"].astype("int64")
        valid["line_total"] = valid["quantity"] * valid["unit_price"]
    else:
        valid["line_total"] = pd.Series(dtype="float64")
    return valid, rejected


def transform_all(raw_tables: dict):
    """Transform all tables in dependency order and return valid/rejected dictionaries."""
    valid = {}
    rejected = {}

    valid["customers"], rejected["customers"] = transform_customers(raw_tables["customers"])
    valid["products"], rejected["products"] = transform_products(raw_tables["products"])

    customer_ids = set(valid["customers"]["customer_id"].astype(str))
    valid["orders"], rejected["orders"] = transform_orders(raw_tables["orders"], customer_ids)

    order_ids = set(valid["orders"]["order_id"].astype(str))
    product_ids = set(valid["products"]["product_id"].astype(str))
    valid["order_items"], rejected["order_items"] = transform_order_items(
        raw_tables["order_items"], order_ids, product_ids
    )
    return valid, rejected
