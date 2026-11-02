from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_db
from app.services import orders as service

router = APIRouter(prefix="/orders")


@router.get("/{order_id}")
def get_order(order_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    order = service.get_order_for_user(db, user, order_id)
    return {"id": order.id, "total_cents": order.total_cents, "status": order.status}
