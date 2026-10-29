import os

import requests


def charge(order_id, amount, token):
    r = requests.post(
        os.environ["PAYMENT_URL"] + "/charges",
        json={"order_id": order_id, "amount": amount, "token": token},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()
