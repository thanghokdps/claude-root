"""Two ways a request can name its user."""


def user_from_gateway_header(headers):
    # Used by /admin: the gateway strips and re-sets X-User-Id.
    return headers.get("X-User-Id")


def user_from_bearer(headers):
    # Used by /orders: JWT verified by the verify_jwt helper (not shown).
    token = headers.get("Authorization", "").removeprefix("Bearer ")
    return token or None
