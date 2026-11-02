from src.notify import send_email, send_sms


def register(user):
    send_email(user["email"], "Welcome", "Thanks for joining")
    if user.get("phone"):
        send_sms(user["phone"], "Welcome")
    return user
