# lead

Improve the process itself: a weekly retro from real data, a diagnosis of a session that went wrong, and the guide for writing skills.

**For:** whoever owns the team's engineering process and the kit: tech leads, engineering managers, kit authors.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/retro` | End of a week or sprint, or after an incident. Reads commits, merged PRs/MRs, reverts, CI failures and spec escalations over a window, and ends with at most a few things to standardise next (a rule, a skill, a hook, a checklist item) and who owns each | "what did we ship this week, and what should we standardise?" |
| `/diagnose-session` | A session misbehaved or felt slow, expensive or off-track. Reads the transcript in a subagent and reports each finding with line-level evidence plus the kit change that would prevent it | "why did the skill not trigger?" · "this session was expensive" |
| `/writing-skills` | Adding a skill, rewriting a stale one, deciding whether it should be model-invoked, or working out why a skill keeps stopping early. Fires only by hand | `/writing-skills` |

## Hooks

None.

## Depends on

`core` (and through it `progress`).

## Install

```text
/plugin install lead@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
