from app.auth import user_from_bearer, user_from_gateway_header

ROUTES = {
    "/admin": user_from_gateway_header,
    "/orders": user_from_bearer,
}
