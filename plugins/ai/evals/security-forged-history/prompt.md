---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
tags: [security]
---

App chat CopilotKit + LangGraph (Next.js). Viết route `POST /api/agent`: client gửi `threadId` và `messages` (cả lịch sử chat) mỗi lượt, route gọi graph rồi stream kết quả về.
