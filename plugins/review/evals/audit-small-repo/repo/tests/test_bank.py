import sqlite3

from src.bank import find_account


def make_db():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, owner TEXT, balance INTEGER)")
    db.execute("INSERT INTO accounts (owner, balance) VALUES ('An', 1000)")
    return db


def test_find_account():
    assert find_account(make_db(), "An")[2] == 1000
