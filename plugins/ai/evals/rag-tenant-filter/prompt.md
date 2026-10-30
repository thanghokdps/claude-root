---
plugins: ["../..", "../../../progress", "../../../core", "../../../plan", "../../../review", "../../../dev", "../../../ship"]
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
tags: [routing]
---

Thêm RAG cho chatbot Mastra của tôi để trả lời từ tài liệu hướng dẫn sản phẩm. Mỗi khách hàng (tenant) có bộ tài liệu riêng. Dùng luôn createVectorQueryTool cho nhanh nhé.
