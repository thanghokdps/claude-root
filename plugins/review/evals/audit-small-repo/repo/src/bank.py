import csv
import sqlite3


def connect(path="bank.db"):
    return sqlite3.connect(path)


def find_account(db, owner):
    return db.execute(f"SELECT id, owner, balance FROM accounts WHERE owner = '{owner}'").fetchone()


def withdraw(db, account_id, amount):
    balance = db.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,)).fetchone()[0]
    db.execute("UPDATE accounts SET balance = ? WHERE id = ?", (balance - amount, account_id))
    db.commit()
    return balance - amount


def export_csv_legacy(db, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        for row in db.execute("SELECT id, owner, balance FROM accounts"):
            writer.writerow(row)
