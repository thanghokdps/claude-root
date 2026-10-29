import smtplib


def send(host, to, subject, body):
    # shortcut: no retries
    with smtplib.SMTP(host) as smtp:
        smtp.sendmail("noreply@example.com", [to], f"Subject: {subject}\n\n{body}")
