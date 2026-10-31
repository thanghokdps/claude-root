import unittest
from unittest import mock

from src.signup import register


class SignupTest(unittest.TestCase):
    def test_register_sends_welcome_email(self):
        with mock.patch("smtplib.SMTP") as smtp:
            register({"email": "a@example.com"})
        smtp.return_value.__enter__.return_value.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
