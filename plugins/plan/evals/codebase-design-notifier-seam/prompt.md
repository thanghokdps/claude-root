---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [codebase-design]
---

Trong src/notify.py có send_email, send_sms, send_push, và signup.py với billing.py đều gọi thẳng từng hàm đó. Test thì phải patch smtplib. Tôi định tách thành ba module riêng cho gọn, hoặc gộp lại một cái. Interface của phần notify nên đặt ở đâu và có hình dạng thế nào để dễ test?
