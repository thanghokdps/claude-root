import sqlite3


def invoice_for(db: sqlite3.Connection, customer_id: int, amount: int):
    customer = db.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if customer is None:
        raise ValueError("unknown customer")
    db.execute("INSERT INTO invoices (customer_id, amount) VALUES (?, ?)", (customer_id, amount))
    return customer
