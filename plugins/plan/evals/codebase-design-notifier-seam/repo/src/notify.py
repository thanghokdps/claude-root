import smtplib
from email.message import EmailMessage


def send_email(to, subject, body):
    msg = EmailMessage()
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    with smtplib.SMTP("localhost") as s:
        s.send_message(msg)


def send_sms(phone, text):
    print(f"sms to {phone}: {text}")


def send_push(device_id, text):
    print(f"push to {device_id}: {text}")
