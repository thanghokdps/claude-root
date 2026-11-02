---
description: Execute a task autonomously end-to-end — no permission prompts, wave-based execution
argument-hint: "[#issue] task description"
---

# Auto Execute

Immediately invoke the `auto-dev` agent with the full task description.

Use the Agent tool:
- subagent_type: auto-dev
- description: the task from the argument
- prompt: the full argument passed to this command

If no argument was provided, ask the user for the task description first.
