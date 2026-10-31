from datetime import datetime, timezone
from src.store import AUDIT, BALANCES, REQUESTS


def approve_leave_request(caller_id: str, request_id: str) -> dict:
    req = REQUESTS.get(request_id)
    if req is None:
        raise KeyError("no such request")
    if req["status"] != "pending":
        raise ValueError("request already decided")

    # new balance = old balance minus the leave length
    length = (req["end"] - req["start"]).days + 1
    BALANCES[req["employee_id"]] = BALANCES[req["employee_id"]] - length

    req["status"] = "approved"
    AUDIT.append({"actor": caller_id, "action": "approve", "request": request_id, "at": datetime.now(timezone.utc)})
    return req
