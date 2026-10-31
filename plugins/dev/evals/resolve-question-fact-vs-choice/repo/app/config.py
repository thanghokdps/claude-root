"""Runtime settings."""
import os

SESSION_TTL_SECONDS = 1800
MAX_LOGIN_ATTEMPTS = 5
GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "")
