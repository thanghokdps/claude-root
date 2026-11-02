---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [verify]
---

Agent tự viết emitter AG-UI (@ag-ui/core 1.0.3). Client báo run fail ở cuối dù text hiện đủ. Đây là stream đã capture, đọc giúp tôi lỗi ở đâu:

RUN_STARTED {"threadId":"t1","runId":"r1"}
REASONING_START {"messageId":"rs1"}
REASONING_MESSAGE_START {"messageId":"rm1","role":"reasoning"}
REASONING_MESSAGE_CONTENT {"messageId":"rm1","delta":"Checking order"}
TEXT_MESSAGE_START {"messageId":"m1","role":"assistant"}
TEXT_MESSAGE_CONTENT {"messageId":"m1","delta":"Đơn 1234 đang giao.","orderStatus":"shipping"}
TEXT_MESSAGE_END {"messageId":"m1"}
RUN_FINISHED {"threadId":"t1","runId":"r1"}
