---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
tags: [fix-bug]
---

Prod thỉnh thoảng trả 500 ở /checkout, khoảng 1–2% request. Log chỉ có đúng một dòng: `ERROR checkout failed request_id=ab12`. Local chạy không lỗi. Nguyên nhân là gì, fix luôn đi.
