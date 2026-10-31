---
model: opus
effort: high
name: diagnose-session
description: Investigates what went wrong in a Claude Code session using its transcript — skills that fired when they should not (or stayed silent), ignored plans, repeated work, noisy hooks, wasted tokens — and reports each finding with line-level evidence plus the kit change that would prevent it. Use when a session misbehaved or felt slow, expensive, or off-track.
when_to_use: asking what went wrong in this session, "why did the skill not trigger", "why did Claude ignore the plan", "this session was slow/expensive", tuning the kit after a bad run
# Transcripts are large: read them in a forked subagent and return only the report.
context: fork
background: false
---

# diagnose-session — evidence from the transcript, then a fix in the kit

**Invoke:** `/diagnose-session [session-id]` — default: the current session.

## Step 1 — Find the transcript

Transcripts are JSONL under `~/.claude/projects/<project-dir-slug>/<session-id>.jsonl`. No id given → the current session, `${CLAUDE_SESSION_ID}` — not the newest by mtime, which is another session whenever two are open.

```bash
ls ~/.claude/projects/*/${CLAUDE_SESSION_ID}.jsonl
```

Read with `jq`, never by dumping the whole file into context.

## Step 2 — Look for these failure modes

| Symptom | Where it shows |
|---------|----------------|
| Skill misfire / no fire | `Skill` tool calls vs user prompts that should have triggered one |
| Plan ignored | Edits to files outside the approved plan; steps skipped |
| Repeated work | Same file read or same command run 3+ times |
| Hook noise | `hook` / system-reminder entries repeating; blocking errors from PostToolUse hooks |
| Context waste | Very large tool results; whole-file reads where a grep would do |
| Unverified "done" | A completion claim with no test/command run after the last edit |

## Step 3 — Report

For each finding: what happened, the transcript line(s) as evidence (quote ≤2 lines, scrub secrets and personal data), and the smallest kit change that prevents it — a skill description tweak (then add a trigger case under `eval/triggers/`), a hook fix, or a rule.

- One finding, one concrete change: name the file and what to add. A symptom of another finding (the same test re-run after each blind edit) merges into that finding instead of standing alone without a change.
- Before proposing a new skill, check the session's skill list for one that covers it (a debugging skill for "still red"); extend that skill's trigger instead. No "consider" or "maybe": a change you cannot make concrete is not a finding.

## Rules

- Evidence or it didn't happen: every finding cites a transcript location.
- Do not paste transcript content outside the user's machine; redact tokens, emails, and keys in quotes.
- Propose kit changes; apply them only when the user agrees.
