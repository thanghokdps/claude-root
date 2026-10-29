from datetime import datetime


def parse_date(text):
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None
