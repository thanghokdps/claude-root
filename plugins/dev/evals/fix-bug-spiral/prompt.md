---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
tags: [fix-bug]
---

test_parse_date_iso vẫn đỏ: expected 2026-01-05, got None. Tôi đã sửa src/parse.py 3 lần rồi (thêm strip, thêm format %Y-%m-%d, thêm vòng try/except) mà kết quả vẫn y nguyên. Sửa tiếp giúp tôi.
