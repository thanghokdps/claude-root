def total(items):
    return sum(i["price"] * i["qty"] for i in items)


def item_count(items):
    return sum(i["qty"] for i in items)
