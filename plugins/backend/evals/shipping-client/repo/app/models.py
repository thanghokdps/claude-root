from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    id: int
    user_id: int
    total_cents: int
    status: str
    created_at: datetime
