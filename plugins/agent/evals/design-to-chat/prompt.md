---
plugins: ["../..", "../../../progress"]
max_turns: 16
allowed_tools: [Read, Write, Edit, Glob, Grep, Skill]
tags: [design]
---

Designer gửi design cho chatbot ShopBot (CopilotKit v2, React): ảnh frame `design/tool-done.png` và biến màu/bo góc trong `design/tokens.json`. Làm UI chat theo design này. Lần này chỉ cần map design: ghi `docs/design/ui-map.md` và file CSS theme, chưa build component. Chỉ có một frame này; các state chưa vẽ thì cứ ghi lại là dùng mặc định của CopilotKit, đừng hỏi lại.
