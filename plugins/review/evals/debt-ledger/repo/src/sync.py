import time

POLL_SECONDS = 60  # shortcut: polls every 60 s, fine for one shop; switch to webhooks past 50 shops


def run(fetch_orders, handle):
    while True:
        for order in fetch_orders():
            handle(order)
        time.sleep(POLL_SECONDS)
