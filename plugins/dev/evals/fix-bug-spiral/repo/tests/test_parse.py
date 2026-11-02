from datetime import date

from src.utils.parse import parse_date


def test_parse_date_dmy():
    assert parse_date("05/01/2026") == date(2026, 1, 5)


def test_parse_date_iso():
    assert parse_date("2026-01-05") == date(2026, 1, 5)
