---
type: llm
focus:
  source: file
  path: shop/cart.py
---

This is `shop/cart.py` after the run. The red test expects `total([{"price": 60, "qty": 2}])` to be 108.0 (120 less 10%). The existing test_total_sums_lines (total 25, under 100) must stay green.

PASS if `total` gives 10% off when the lines total over 100 and nothing else changed in behaviour: a minimal discount rule.
FAIL if the discount is missing or wrong (an order of 100 or less is discounted, or the rate is not 10%), or it adds speculative extras (tiers, config, other discounts).
