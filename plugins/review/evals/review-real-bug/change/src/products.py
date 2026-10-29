from src.pagination import page

PRODUCTS = [f"product-{n}" for n in range(1, 31)]


def list_products(number=1, size=10):
    return page(PRODUCTS, number, size)
