from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Float,
    ForeignKey, insert, text
)
from db import get_engine

metadata = MetaData()

# ---------------- CUSTOMERS ----------------
customers = Table(
    "customers", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("city", String(50)),
    Column("segment", String(20))
)

# ---------------- PRODUCTS ----------------
products = Table(
    "products", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("category", String(50)),
    Column("price", Float)
)

# ---------------- ORDERS ----------------
orders = Table(
    "orders", metadata,
    Column("id", Integer, primary_key=True),
    Column("customer_id", Integer, ForeignKey("customers.id")),
    Column("status", String(20)),
    Column("order_date", String(20))
)

# ---------------- ORDER ITEMS ----------------
order_items = Table(
    "order_items", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id")),
    Column("product_id", Integer, ForeignKey("products.id")),
    Column("quantity", Integer)
)


def seed():
    engine = get_engine()

    # STEP 1: reset database safely
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM order_items"))
        conn.execute(text("DELETE FROM orders"))
        conn.execute(text("DELETE FROM products"))
        conn.execute(text("DELETE FROM customers"))

    # STEP 2: recreate tables
    metadata.drop_all(engine)
    metadata.create_all(engine)

    # ---------------- DATA ----------------
    customer_rows = [
        {"id": 1, "name": "Asha", "city": "Delhi", "segment": "consumer"},
        {"id": 2, "name": "Ravi", "city": "Mumbai", "segment": "business"},
        {"id": 3, "name": "Meera", "city": "Delhi", "segment": "consumer"},
        {"id": 4, "name": "John", "city": "Bangalore", "segment": "business"},
        {"id": 5, "name": "Priya", "city": "Mumbai", "segment": "consumer"},
        {"id": 6, "name": "Amit", "city": "Delhi", "segment": "business"},
        {"id": 7, "name": "Sara", "city": "Pune", "segment": "consumer"},
    ]

    product_rows = [
        {"id": 1, "name": "Laptop", "category": "electronics", "price": 1000},
        {"id": 2, "name": "Mouse", "category": "accessories", "price": 20},
        {"id": 3, "name": "Keyboard", "category": "accessories", "price": 50},
        {"id": 4, "name": "Monitor", "category": "electronics", "price": 300},
        {"id": 5, "name": "Phone", "category": "electronics", "price": 800},
        {"id": 6, "name": "USB Cable", "category": "accessories", "price": 10},
    ]

    order_rows = [
        {"id": 1, "customer_id": 1, "status": "completed", "order_date": "2024-01-01"},
        {"id": 2, "customer_id": 1, "status": "completed", "order_date": "2024-01-10"},
        {"id": 3, "customer_id": 2, "status": "pending", "order_date": "2024-02-01"},
        {"id": 4, "customer_id": 3, "status": "completed", "order_date": "2024-02-10"},
        {"id": 5, "customer_id": 4, "status": "completed", "order_date": "2024-03-05"},
        {"id": 6, "customer_id": 5, "status": "cancelled", "order_date": "2024-03-10"},
        {"id": 7, "customer_id": 6, "status": "completed", "order_date": "2024-04-01"},
        {"id": 8, "customer_id": 7, "status": "completed", "order_date": "2024-04-05"},
    ]

    order_item_rows = [
        {"id": 1, "order_id": 1, "product_id": 1, "quantity": 1},
        {"id": 2, "order_id": 1, "product_id": 2, "quantity": 2},
        {"id": 3, "order_id": 2, "product_id": 3, "quantity": 1},
        {"id": 4, "order_id": 2, "product_id": 4, "quantity": 1},
        {"id": 5, "order_id": 3, "product_id": 5, "quantity": 1},
        {"id": 6, "order_id": 4, "product_id": 1, "quantity": 1},
        {"id": 7, "order_id": 5, "product_id": 4, "quantity": 2},
        {"id": 8, "order_id": 6, "product_id": 2, "quantity": 3},
        {"id": 9, "order_id": 7, "product_id": 5, "quantity": 1},
        {"id": 10, "order_id": 8, "product_id": 3, "quantity": 2},
    ]

    with engine.begin() as conn:
        conn.execute(insert(customers), customer_rows)
        conn.execute(insert(products), product_rows)
        conn.execute(insert(orders), order_rows)
        conn.execute(insert(order_items), order_item_rows)

    print("Strong database seeded!")


if __name__ == "__main__":
    seed()