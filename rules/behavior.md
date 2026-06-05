# Behavior Rules

Five core principles that apply to all agents.

## 1. Think Before Coding

State assumptions explicitly. Ask clarifying questions when uncertain — never guess on ambiguous requirements. One question per message. Prefer multiple-choice when possible.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.
- No premature abstractions
- No unnecessary error handling for scenarios that cannot happen
- No unrequested features
- Three similar lines beat a premature helper

## 3. Surgical Changes

When modifying existing code:
- Maintain the current style
- Do not improve unrelated areas
- Only remove code if your changes made it obsolete — not pre-existing dead code

## 4. Goal-Driven Execution

Convert each task into a verifiable objective with a clear success criterion before starting. Use tests to validate completion, not assertions.

## 5. Communicate Clearly

- Surface blockers immediately — do not work around them silently
- Explain directional changes before making them
- Keep updates concise: one sentence per update is usually enough
- Deviations from the plan must be reported with justification and added to `specs/<slug>/SUMMARY.md` under `## Deviations`
