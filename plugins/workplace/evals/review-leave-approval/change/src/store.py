"""In-memory stand-in for the database."""
EMPLOYEES = {
    "e1": {"name": "An", "manager_id": "m1"},
    "m1": {"name": "Binh", "manager_id": None},
    "e2": {"name": "Chi", "manager_id": "m2"},
    "m2": {"name": "Dung", "manager_id": None},
}
BALANCES = {"e1": 12.0, "e2": 12.0}  # days of annual leave
REQUESTS = {}
AUDIT = []
