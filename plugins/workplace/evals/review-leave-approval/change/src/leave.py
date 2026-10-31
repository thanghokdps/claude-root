from datetime import date
from src.store import EMPLOYEES, REQUESTS

# shortcut: fixed cap of pending requests per employee, fine for a 40-person office; make it a setting past 500 staff
MAX_PENDING = 20


def submit_leave(employee_id: str, start: date, end: date, half_day: bool = False) -> dict:
    if end < start:
        raise ValueError("end before start")
    if half_day and start != end:
        raise ValueError("half day must be a single date")
    pending = [r for r in REQUESTS.values() if r["employee_id"] == employee_id and r["status"] == "pending"]
    if len(pending) >= MAX_PENDING:
        raise ValueError("too many pending requests")
    days = 0.5 if half_day else float((end - start).days + 1)
    req = {
        "id": f"r{len(REQUESTS) + 1}",
        "employee_id": employee_id,
        "approver_id": EMPLOYEES[employee_id]["manager_id"],
        "start": start,
        "end": end,
        "days": days,
        "status": "pending",
    }
    REQUESTS[req["id"]] = req
    return req
