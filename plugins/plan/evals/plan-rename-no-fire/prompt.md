---
max_turns: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [routing]
---

Đổi tên hàm `calc_total` thành `compute_total` ở hai file này giúp tôi, chỉ cần đưa lại code sau khi đổi.

`cart.py`:
```python
def calc_total(items):
    return sum(i["price"] * i["qty"] for i in items)
```

`checkout.py`:
```python
from cart import calc_total

def pay(items):
    return {"amount": calc_total(items)}
```
