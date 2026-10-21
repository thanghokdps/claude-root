# thang-agent

Skills for building AI assistants on **CopilotKit · AG-UI · LangChainJS · LangGraph**. Standalone: no other plugin, no hooks, ~1.3k tokens always-on.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install thang-agent@thang-kit
```

Then `/reload-plugins` (or open a new session). Update later with `/plugin marketplace update thang-kit`.

## Skills

| Skill | Reach for it when |
|-------|-------------------|
| `/agent-architect [greenfield\|audit]` | Starting an assistant, or auditing one for custom code that stock middleware now covers |
| `/agent-tool <tool>` | Adding, renaming or fixing a tool — schema, trusted identity, read vs mutation, its test |
| `/agent-hitl <write>` | A tool creates, updates or deletes data and needs a confirm card |
| `/agent-graph <scope>` | A request lands on the wrong agent; adding an agent, router or supervisor; rewriting a system prompt |
| `/agent-frontend <change>` | Chat UI in React: provider headers, shared context, tool renderers, e2e with recorded streams |
| `/agent-verify-turn [local\|prod-trace]` | Before saying an agent change works, or when a production answer was wrong |
| `/agent-evals [unit\|suite\|compare-models]` | Fake-model unit tests, judged eval suites with a CI gate, comparing models |
| `/agent-security [scope]` | A new tool, data source or client; before shipping; compliance questions |

Skills fire on their own from what you type — the slash command is optional.

## Demo prompts

1. "Thêm tool cho agent để tra cứu đơn hàng theo mã" → `agent-tool`
2. "Agent xóa user qua chat, cần confirm trước khi lưu" → `agent-hitl`
3. "Hỏi về hóa đơn mà agent support lại trả lời" → `agent-graph`
4. "Sửa rồi mà vẫn bị, chạy thử một turn thật xem stream" → `agent-verify-turn`

## Rules

`rules/` holds the invariants the skills read before they act — identity and tools, prompts, stock-first, AG-UI transport, LangGraph, tracing privacy, dependency pinning. They load only when a skill needs them, not every session.

## Works alongside

Other plugins with their own agent skills can be installed side by side. When both match a request, name the one you want: `/thang-agent:agent-tool`.
