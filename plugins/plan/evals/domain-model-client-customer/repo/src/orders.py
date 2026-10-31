import sqlite3


def place_order(db: sqlite3.Connection, client_id: int, sku: str):
    client = db.execute("SELECT id, name FROM customers WHERE id = ?", (client_id,)).fetchone()
    if client is None:
        raise ValueError("unknown client")
    db.execute("INSERT INTO orders (client_id, sku) VALUES (?, ?)", (client_id, sku))
    return client
