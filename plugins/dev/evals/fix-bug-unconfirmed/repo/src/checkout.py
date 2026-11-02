import logging

from src.orders import create_order
from src.payments import charge

log = logging.getLogger(__name__)


def checkout(request):
    try:
        order = create_order(request.user_id, request.cart)
        charge(order.id, order.total, request.payment_token)
        return {"status": 200, "order_id": order.id}
    except Exception:
        log.error("checkout failed request_id=%s", request.id)
        return {"status": 500}
