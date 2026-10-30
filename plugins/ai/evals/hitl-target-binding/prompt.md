---
plugins: ["../..", "../../../progress", "../../../core", "../../../plan", "../../../review", "../../../dev", "../../../ship"]
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [hitl, security]
---

Agent LangGraph có tool thêm người vào dự án với vai trò. User gõ "thêm Alice làm manager", model tự điền memberId vào tool rồi hiện thẻ xác nhận. Làm sao để chắc chắn ghi đúng người? Mô tả cách làm, chưa cần viết code.
