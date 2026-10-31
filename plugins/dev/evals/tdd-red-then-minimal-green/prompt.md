---
max_turns: 12
allowed_tools: [Skill, Read, Glob, Grep, Edit, Write, Bash]
tags: [tdd]
---

Let's build this test-first. tests/test_cart.py::test_bulk_discount_over_100 is red: a cart whose lines total over 100 should get 10% off. Get it green with the smallest change that does it.
