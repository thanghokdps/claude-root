---
max_turns: 12
allowed_tools: [Skill, Read, Glob, Grep, Edit, Write, Bash]
tags: [tdd]
---

TDD this, red-green: tests/test_cart.py::test_bulk_discount_over_100 is red — a cart whose lines total over 100 should get 10% off. Watch it fail first, then get it green with the smallest change that does it.
