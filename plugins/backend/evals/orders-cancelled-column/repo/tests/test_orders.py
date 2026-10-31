def test_get_own_order(client, sign_in_as, seed_order):
    sign_in_as(1)
    order = seed_order(user_id=1)
    res = client.get(f"/orders/{order.id}")
    assert res.status_code == 200


def test_get_other_users_order_is_404(client, sign_in_as, seed_order):
    order = seed_order(user_id=2)
    sign_in_as(1)
    res = client.get(f"/orders/{order.id}")
    assert res.status_code == 404
    assert res.json()["code"] == "order_not_found"
