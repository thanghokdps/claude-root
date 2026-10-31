from src.notify import send_email, send_push


def invoice_paid(user, amount):
    send_email(user["email"], "Receipt", f"Paid {amount}")
    if user.get("device"):
        send_push(user["device"], "Payment received")
