# Hướng dẫn sử dụng Claude Harness

Từ lần cài đầu tiên đến lúc chạy task hàng ngày.

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Yêu cầu](#2-yêu-cầu)
3. [Bước 1 — Cài harness (1 lần duy nhất)](#3-bước-1--cài-harness-1-lần-duy-nhất)
4. [Bước 2 — Bootstrap project mới](#4-bước-2--bootstrap-project-mới)
5. [Bước 3 — Điền thông tin sau khi init](#5-bước-3--điền-thông-tin-sau-khi-init)
6. [Bước 4 — Phiên làm việc đầu tiên](#6-bước-4--phiên-làm-việc-đầu-tiên)
7. [Workflow hàng ngày](#7-workflow-hàng-ngày)
8. [Các task phổ biến](#8-các-task-phổ-biến)
9. [Làm việc nhóm (team)](#9-làm-việc-nhóm-team)
10. [Kết thúc phiên làm việc](#10-kết-thúc-phiên-làm-việc)
11. [Xử lý sự cố thường gặp](#11-xử-lý-sự-cố-thường-gặp)

---

## 1. Tổng quan

Claude Harness là một framework quản trị cho Claude Code. Nó gồm hai lớp:

```
┌─────────────────────────────────────────────────────┐
│  SKILLS (engine)                                    │
│  /feature · /fix-bug · /code-review · /ticket ...  │
│  → trả lời "làm cái này như thế nào?"              │
├─────────────────────────────────────────────────────┤
│  HARNESS (control)                                  │
│  hooks · rules · memory                             │
│  → trả lời "cẩn thận đến mức nào? ai phải duyệt?" │
└─────────────────────────────────────────────────────┘
```

**Nguyên tắc cốt lõi:** Ceremony (quy trình) tăng theo rủi ro. Human interruption tăng theo sự mơ hồ.

**Luồng chạy tổng quát:**

```
prompt người dùng
  → scope-gate.sh        phân loại rủi ro, kiểm tra memory cũ
  → /coordinator         phân tích yêu cầu, giao task cho đúng agent
  → Explorer / Planner   hiểu code, lập kế hoạch
  → Implementer          viết code
  → Verifier / Reviewer  kiểm chứng
  → commit hooks         chặn commit xấu
  → memory hooks         lưu lại lịch sử
```

---

## 2. Yêu cầu

| Thứ | Yêu cầu |
|-----|---------|
| Claude Code | CLI hoặc desktop app (https://claude.ai/code) |
| Git | `git --version` phải có |
| `jq` | `brew install jq` (dùng bởi các hooks) |
| Python 3.12 | Chỉ cần nếu muốn cài **headroom** (context compression) |
| Node.js / Python / Go | Tuỳ stack của project |

---

## 3. Bước 1 — Cài harness (1 lần duy nhất)

### Tải về và chạy install

```bash
# Clone hoặc download repo về ~/Downloads/Claude
# (bạn có thể đổi tên hoặc đặt ở chỗ khác)

bash ~/Downloads/Claude/scripts/install.sh
```

**Script sẽ hỏi nếu đã tồn tại rồi.** Gõ `y` để overwrite, `n` để giữ nguyên.

Mặc định cài vào `~/.claude-harness`. Muốn đặt chỗ khác:

```bash
bash ~/Downloads/Claude/scripts/install.sh ~/my-tools/claude-harness
```

### Kết quả sau install

```
🔧 Claude Harness Installer
   Source : ~/Downloads/Claude
   Target : ~/.claude-harness

✅ Harness copied to ~/.claude-harness
   Added HARNESS_DIR to .zshrc

📦 Installing to ~/.claude/ ...
   Skills  : 18 installed
   Rules   : 13 installed
   Hooks   : 9 installed
   Memory  : templates copied

✅ Installation complete!
```

### Reload shell

```bash
source ~/.zshrc     # hoặc mở terminal mới
echo $HARNESS_DIR   # phải in ra ~/.claude-harness
```

### (Tuỳ chọn) Cài headroom — context compression

Giúp giảm 60–95% token khi context window lớn:

```bash
bash $HARNESS_DIR/scripts/setup-headroom.sh
```

**Yêu cầu:** Python 3.12 (`brew install python@3.12`).

Sau khi cài, hook `headroom-compress.sh` tự động trigger khi output > 8KB.

---

## 4. Bước 2 — Bootstrap project mới

Chạy **1 lần** cho mỗi project để tạo workspace `.claude/` riêng.

### Cách A — Qua Claude Code (khuyến nghị)

```bash
cd ~/my-project

# Mở Claude Code, gõ:
/project-init
```

Claude sẽ:
1. Scan `src/`, `package.json`, `requirements.txt`... để detect stack
2. Tạo toàn bộ `.claude/` workspace (docs, agents, hooks, rules, skills, templates)
3. Sinh `CLAUDE.md` project-specific với đường dẫn và lệnh thật

### Cách B — Qua script

```bash
cd ~/my-project
$HARNESS_DIR/scripts/init.sh

# Hoặc chỉ định đường dẫn cụ thể:
$HARNESS_DIR/scripts/init.sh /path/to/my-project
```

### Cách C — Dùng stack bundle có sẵn (React Native / Next.js / Python)

Nếu project của bạn match một trong các stack có sẵn trong `stacks/`:

```bash
# Ví dụ: React Native project
cp -r $HARNESS_DIR/stacks/react-native/.claude ~/my-rn-project/
```

Rồi chỉnh sửa các file để khớp với đường dẫn thực của project.

### Stack được tự động detect

| Signal | Khi nào |
|--------|---------|
| `typescript` | `tsconfig.json` hoặc `"typescript"` trong package.json |
| `react` | `"react"` trong package.json |
| `jest` | `"jest"` trong package.json |
| `nextjs` | `"next"` trong package.json |
| `python` | `requirements.txt` hoặc `pyproject.toml` |
| `fastapi` | `fastapi` trong requirements |
| `langgraph` | `langgraph` trong requirements |

### Kết quả sau bootstrap

```
your-project/
├── CLAUDE.md                  ← cần điền thêm thông tin
└── .claude/
    ├── settings.json          ← hooks đã đăng ký
    ├── docs/                  ← knowledge base (viết bởi /project-init)
    │   ├── index.md
    │   ├── architecture.md
    │   ├── conventions.md
    │   ├── stack.md
    │   ├── entry-points.md
    │   └── test-strategy.md
    ├── rules/                 ← universal + stack-specific rules
    ├── skills/                ← slash commands cho project này
    ├── hooks/                 ← automation scripts
    └── memory/
        ├── MEMORY.md          ← index (tự load mỗi session)
        ├── user.md            ← cần điền
        └── project/
            └── context.md     ← cần điền
```

---

## 5. Bước 3 — Điền thông tin sau khi init

**Đây là bước quan trọng nhất.** Claude chỉ hoạt động tốt khi có context đúng.

### 5.1 — Điền `CLAUDE.md`

Mở `CLAUDE.md` trong project root, điền vào các phần có comment `<!-- ... -->`:

```markdown
## What this project is
Ứng dụng quản lý đơn hàng nội bộ cho team logistics.
Stack: Next.js 14 App Router + PostgreSQL + Prisma.

## Run the project
```bash
pnpm install
pnpm dev           # dev server tại localhost:3000
pnpm test          # jest
pnpm typecheck     # tsc --noEmit
pnpm lint          # eslint
```

## Architecture
src/app/          ← Next.js App Router (Server Components mặc định)
src/components/   ← Client Components ("use client")
src/lib/          ← utilities, db client
src/server/       ← Server Actions

## Constraints
- TypeScript strict — npx tsc --noEmit phải pass trước khi commit
- pnpm only — không dùng npm hay yarn
- Không gọi DB trực tiếp trong route handlers — dùng Server Actions
```

### 5.2 — Điền `.claude/memory/user.md`

```markdown
## Role & Background
Senior fullstack engineer. Quen với Next.js và PostgreSQL.
Đang học về Server Components và React v19 patterns.

## Preferences
- Muốn response ngắn gọn, không cần giải thích từng bước hiển nhiên
- Ưu tiên TypeScript strict — không dùng `any`
- Commit message theo format: feat/fix/chore: mô tả ngắn
```

### 5.3 — Điền `.claude/memory/project/context.md`

```markdown
## Goals
MVP checkout flow cho mobile app. Deadline: 2026-07-01.

## Active decisions
- Dùng Server Actions thay vì REST API riêng — **Why:** giảm boilerplate,
  type-safe end-to-end — **How to apply:** tất cả mutations đi qua actions/

## Constraints
- Không dùng Vercel AI SDK — đang dùng CopilotKit
- Firebase config không được commit (đã gitignore)

## Team
- Thang: frontend + backend
- Mai: designer, gửi Figma links qua Slack
```

---

## 6. Bước 4 — Phiên làm việc đầu tiên

### Mở Claude Code trong project

```bash
cd ~/my-project
claude          # CLI
# hoặc mở Claude Code desktop và chọn thư mục
```

### Kiểm tra context đã load đúng chưa

Claude tự động đọc `CLAUDE.md` và `MEMORY.md` mỗi session. Bạn có thể hỏi nhanh:

```
bạn đang làm việc trên project gì?
```

Claude nên trả lời đúng tên project, stack, và constraints.

### Kiểm tra hooks hoạt động

```bash
# Thử commit một file bình thường — hooks sẽ kiểm tra
git add README.md
git commit -m "test: kiểm tra hooks"
# Nếu không có vấn đề → commit pass
# Nếu có secret hay console.log → commit bị chặn với thông báo rõ
```

---

## 7. Workflow hàng ngày

### Bắt đầu session

```bash
cd ~/my-project
claude
```

Nếu hôm qua có làm dở, `specs/HANDOFF.md` sẽ tự load và Claude biết tiếp tục từ đâu.

Nếu làm việc nhóm — chạy sync trước:

```
/sync-memory
```

### Trong session

**Auto-coordinator đã bật sẵn** — bạn không cần gõ `/coordinator`. Chỉ cần nói điều bạn muốn:

```
thêm chức năng export CSV cho trang báo cáo
```

Claude sẽ tự:
1. Phân loại task (lane: tiny / normal / high-risk)
2. Tạo task board
3. Giao cho đúng agent
4. Chạy theo waves
5. Verify kết quả

---

## 8. Các task phổ biến

### Implement feature mới

```
thêm dark mode cho settings page
```

Hoặc explicit hơn:

```
/feature thêm dark mode cho settings page
```

**Flow:** risk intake → research → plan → build → self-review → commit

Với feature phức tạp (auth, payment, migration) — Claude sẽ hỏi xác nhận trước khi làm.

---

### Fix bug

```
/fix-bug app crash khi upload file lớn hơn 10MB
```

**Flow:** reproduce → root cause (không đoán, trace thật) → minimal fix → verify → commit

Commit message tự động: `fix: <mô tả cái gì sai và đã fix gì>`

---

### Code review

```bash
# Review toàn bộ branch hiện tại
/code-review

# Review kỹ hơn
/code-review high

# Review nhanh, chỉ critical issues
/code-review low
```

**Kết quả:**
```
### 🔴 MUST FIX — SQL injection
File: src/users/repo.ts:42
Issue: user input ghép trực tiếp vào SQL string
Fix: dùng parameterized query: db.query('...', [id])

### 🟡 SHOULD FIX — missing error boundary
...
```

---

### Implement từ ticket (5-agent pipeline)

```
/ticket #123 thêm swipe-to-dismiss trên pending request cards
```

**Pipeline tự động:**
```
PM Agent      → đọc ticket, tìm code liên quan, xác định rủi ro
    ↓
Architect     → technical plan với wave-organized tasks
    ↓
Developer     → implement theo plan (parallel waves)
    ↓
Reviewer      → review diff, APPROVED hoặc yêu cầu sửa
    ↓
QA/Verifier   → lint + types + tests + golden path + commit
```

---

### Viết test

```
/gen-tests src/services/payment-service.ts
```

Hoặc hỏi trực tiếp:

```
viết unit test cho hàm calculateDiscount trong src/utils/pricing.ts
```

---

### Tạo component từ Figma

```
/figma-to-screen [Figma URL]
```

---

### Task nhỏ, không cần ceremony

```
/task đổi màu primary button từ blue-600 sang indigo-600
```

**Flow:** đọc conventions → implement → verify → commit. Không cần plan.

---

### Brainstorm trước khi làm feature phức tạp

```
/brainstorming thiết kế hệ thống notification real-time
```

**Flow:** hỏi từng câu một → đề xuất 2–3 approaches → thiết kế → viết `specs/<slug>/design.md` → gọi `/writing-plans`

---

### Tạo implementation plan từ design

```
/writing-plans
```

Chạy sau `/brainstorming`. Sinh ra `specs/<slug>/PLAN.md` với wave-organized tasks.

---

### Generate PR description

```
/create-pr
```

Sinh ra `PR_TEMPLATE.md` — điền sẵn title, summary (why not how), files changed, test plan.

---

## 9. Làm việc nhóm (team)

### Đầu mỗi session

```
/sync-memory
```

Hoặc chạy script trực tiếp:

```bash
$HARNESS_DIR/scripts/sync-team.sh
```

**Thực hiện:**
1. Stash changes chưa commit
2. `git fetch --all --prune` + `git pull`
3. Quét commits của **bạn** từ lần sync trước → lưu vào memory
4. Liệt kê commits của teammate → flag files bị đụng
5. Pop stash

**Xem kết quả:**

```bash
cat .claude/memory/commits/$(date +%Y-%m-%d).md
```

Sẽ thấy commits của bạn + danh sách thay đổi từ team. Nếu có file bị cả hai touch, Claude sẽ cảnh báo.

---

## 10. Kết thúc phiên làm việc

### Trước khi đóng — compact session

```
/compact
```

**Thực hiện:**
1. Tóm tắt những gì đã làm trong session
2. Ghi vào `specs/HANDOFF.md` (session tiếp theo tự đọc)
3. Merge learnings quan trọng vào `docs/solutions/`
4. Update memory nếu học được gì về user preferences

**Session tiếp theo:** Claude tự đọc `HANDOFF.md` → biết tiếp tục từ đâu → xoá file đi.

### Sau session lớn — compound learnings

```
/compound
```

Dùng sau những session có debug phức tạp, sửa bugs khó, hoặc quyết định kiến trúc. Lưu vào `docs/solutions/` để future sessions không lặp lại.

---

## 11. Xử lý sự cố thường gặp

### Commit bị chặn bởi quality gate

```
🚫 COMMIT BLOCKED — quality gate failed:
   ❌ OpenAI API key pattern detected in staged code
```

**Giải quyết:**
```bash
# Tìm file có vấn đề
git diff --cached | grep -n "sk-"

# Xoá key, dùng env var thay thế
# .env file → gitignore → đọc từ process.env

# Stage lại và commit
git add <file>
git commit -m "..."
```

---

### Hook bị trigger nhầm (false positive)

Ví dụ: test file có string `"api_key": "test-value"` bị chặn.

**Giải quyết ngắn hạn** — bypass cho lần đó (dùng cẩn thận):
```bash
SKIP_QUALITY_GATE=1 git commit -m "test: add fixture with api key pattern"
```

**Giải quyết dài hạn** — chỉnh hook để skip thêm pattern:
```bash
# .claude/hooks/commit-quality-gate.sh
# Thêm vào phần STAGED_APP:
':!*.fixture.*' ':!tests/fixtures/*'
```

---

### `specs/HANDOFF.md` không load

Kiểm tra `CLAUDE.md` có dòng này không:

```bash
cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md
```

Nếu không có → thêm vào phần "Session Resume" trong `CLAUDE.md`.

---

### Claude không nhớ context từ session trước

1. Kiểm tra `MEMORY.md` còn chứa entries không: `cat .claude/memory/MEMORY.md`
2. Kiểm tra `HANDOFF.md` đã được xoá chưa (nếu còn → Claude chưa đọc)
3. `/compact` chưa được chạy → không có gì được lưu

---

### Memory index quá dài (>200 dòng)

Claude Code truncate `MEMORY.md` sau 200 dòng:

```bash
# Đếm số dòng
wc -l .claude/memory/MEMORY.md

# Dọn entries cũ (>30 ngày, không còn áp dụng)
# Xoá file memory đi kèm trước, rồi xoá dòng trong MEMORY.md
```

---

### Cập nhật harness sau khi source thay đổi

```bash
# Chạy lại install.sh — tự detect và update
bash $HARNESS_DIR/scripts/install.sh
```

Nếu muốn cập nhật `.claude/` của một project cụ thể:

```bash
cd ~/my-project
$HARNESS_DIR/scripts/init.sh
# Script sẽ cảnh báo trước khi overwrite settings.json
```

---

## Tổng kết luồng đầy đủ

```
┌─ CÀI ĐẶT (1 lần) ──────────────────────────────────────────┐
│                                                              │
│  bash ~/Downloads/Claude/scripts/install.sh                 │
│  source ~/.zshrc                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─ BOOTSTRAP PROJECT (1 lần / project) ──────────────────────┐
│                                                             │
│  cd ~/my-project                                           │
│  /project-init              ← Claude Code                  │
│  # hoặc: $HARNESS_DIR/scripts/init.sh                     │
│                                                             │
│  Điền CLAUDE.md             ← run commands, architecture   │
│  Điền memory/user.md        ← role, preferences            │
│  Điền memory/project/*.md   ← goals, decisions             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─ MỖI SESSION ──────────────────────────────────────────────┐
│                                                             │
│  Bắt đầu:                                                  │
│    claude                   ← mở Claude Code               │
│    /sync-memory             ← nếu có team                  │
│    (đọc HANDOFF.md tự động nếu có)                        │
│                                                             │
│  Làm việc:                                                 │
│    "thêm feature X"         ← auto-coordinator xử lý      │
│    /fix-bug <symptom>       ← debug flow                   │
│    /code-review             ← review trước khi PR          │
│    /ticket #123 <desc>      ← full 5-agent pipeline        │
│                                                             │
│  Kết thúc:                                                 │
│    /compact                 ← lưu session state            │
│    /compound                ← sau session có learning lớn  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
                   Ngày hôm sau:
                   Session mới tự đọc HANDOFF.md
                   → tiếp tục từ "Next steps"
```

---

## Cheat sheet — commands hay dùng nhất

| Lệnh | Khi nào dùng |
|------|-------------|
| `/project-init` | Lần đầu setup project |
| `/sync-memory` | Đầu session khi làm nhóm |
| `/feature <mô tả>` | Implement feature mới |
| `/fix-bug <triệu chứng>` | Debug và fix bug |
| `/code-review` | Review trước khi push PR |
| `/code-review high` | Review kỹ cho PR quan trọng |
| `/ticket #N <mô tả>` | Chạy full pipeline từ ticket |
| `/task <mô tả>` | Fix nhỏ, không cần ceremony |
| `/brainstorming <ý tưởng>` | Thiết kế trước khi làm feature phức tạp |
| `/writing-plans` | Sau brainstorming, tạo PLAN.md |
| `/create-pr` | Tạo PR description |
| `/checkpoint` | Kiểm tra tiến độ giữa session |
| `/compact` | Cuối session, lưu state |
| `/compound` | Sau session lớn, lưu learnings |
| `/btw <câu hỏi>` | Hỏi nhanh không break flow |
