# Chat states to inventory

Every row needs a frame or a recorded decision. The ones in **bold** are the ones designs most often leave out — and the ones users see when something goes wrong.

| State | What it shows | Usually built with |
|-------|---------------|--------------------|
| Welcome / empty | first open, greeting, starter suggestions | `welcomeScreen`, `suggestionView` |
| User message | sent bubble, long text wrap, edit | `userMessage` |
| Assistant message | markdown, lists, code, links | `assistantMessage.markdownRenderer` |
| **Streaming** | partial text, cursor, stop button | `cursor`, `input.sendButton` |
| **Thinking / reasoning** | before the first token, or a reasoning block | `reasoningMessage` |
| Tool running | per tool from the ADR's task list | `useRenderTool` (status: in progress) |
| Tool done | the result card per tool | `useRenderTool` (complete) |
| **Tool failed / unparsable result** | the fallback card | `useRenderTool` + tolerant schema |
| Confirm card | pending → confirmed / cancelled / expired | HITL contract (`/agent-hitl`) |
| Suggestions | chips after an answer | `suggestionView` |
| **Error / offline / unauthorised** | run failed, network lost, token expired | app-level banner + retry |
| **Long conversation** | scroll, scroll-to-bottom, date dividers | `scrollView` |
| **Narrow width** | every state at the ADR's smallest supported width (and one middle width): sidebar/history becomes a drawer, composer stays pinned and above the keyboard, cards and code blocks wrap or scroll inside themselves, no horizontal page scroll, tap targets ≥ 44px | responsive classes on tokens; breakpoints from the ADR's `Viewports:` |
| Dark | only if the product has dark mode | `.dark` tokens |

No narrow frame is not a reason to skip the row: the widths come from the ADR (`Viewports:`, asked in `/agent-architect` Q2v). With no ADR answer, ask the viewport question here before building — a desktop-sized frame does not mean desktop-only.

Name frame files after the state column in kebab-case: `design/frames/tool-failed.png`.
