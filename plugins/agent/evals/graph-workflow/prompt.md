---
plugins: ["../..", "../../../progress", "../../../core", "../../../plan", "../../../review", "../../../dev", "../../../ship"]
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
tags: [routing, workflow]
---

Agent Mastra của tôi xử lý hoàn tiền. Tạo workflow cho agent: kiểm tra đơn, chờ người duyệt, rồi mới ghi hoàn tiền. Đừng để model tự quyết thứ tự các bước.
