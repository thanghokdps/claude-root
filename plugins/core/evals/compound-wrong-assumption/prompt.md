---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
tags: [compound]
---

Phiên hôm nay tôi mất gần 3 tiếng vì một giả định sai: tôi cứ nghĩ cột created_at trong bảng orders lưu UTC, nên báo cáo doanh thu theo ngày lệch hết. Hóa ra DB lưu giờ Asia/Ho_Chi_Minh (UTC+7), đơn sau 17h bị tính sang ngày hôm sau. Sửa xong rồi, giờ lưu bài học này lại để lần sau khỏi mắc lại.
