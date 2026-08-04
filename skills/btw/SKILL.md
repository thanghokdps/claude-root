---
name: btw
description: Answer a quick question or do a quick lookup without interrupting the current task or losing context. Use /btw <question> for fast one-off queries while an agent is working. Does NOT create tasks, specs, or side effects.
model: opus
effort: low
when_to_use: user asks a quick question mid-task, needs a fast lookup, wants to check something without breaking flow
---

# btw — Quick Query

Answer quickly and return. No tasks. No specs. No side effects.

**Usage:** `/btw <question>`

Examples:
- `/btw what does Effect.tryPromise do?`
- `/btw which file handles auth middleware?`
- `/btw what's the pnpm filter syntax for running one package?`

## How to respond

1. Answer directly in 1–5 sentences
2. Include a code snippet if it helps (short, inline)
3. If the answer requires reading a file → read it, answer, done
4. Do NOT: create tasks, write files, spawn agents, open specs
5. End with one line: `↩ Back to your task.`

No ceremony. No preamble. Just the answer.
