---
max_turns: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [routing]
---

Giải thích giúp tôi hàm này làm gì:

```python
def chunk(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]
```
