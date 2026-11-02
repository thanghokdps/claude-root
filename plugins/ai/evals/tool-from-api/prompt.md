---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
tags: [tool]
---

Đây là API đơn hàng của tôi, implement tools cho agent LangGraph từ nó:

```bash
curl -H "Authorization: Bearer $ORDERS_TOKEN" https://api.example.com/v1/orders/{id}
curl -H "Authorization: Bearer $ORDERS_TOKEN" "https://api.example.com/v1/orders?status=open"
curl -X POST -H "Authorization: Bearer $ORDERS_TOKEN" https://api.example.com/v1/orders/{id}/cancel
curl -X DELETE -H "Authorization: Bearer $ORDERS_TOKEN" https://api.example.com/v1/admin/orders
```
