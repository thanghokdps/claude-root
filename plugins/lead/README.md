# lead

Improve the process: weekly retro, session diagnosis, authoring skills.

## Install

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
/plugin install lead@harness
```

Also installs: `core`.

## Skills

| Skill | Does |
|-------|------|
| `/diagnose-session` | Investigates what went wrong in a Claude Code session using its transcript — skills that fired when they should not (or stayed silent), ignored plans, repeated work, noisy hooks, wasted tokens — and reports each finding with line-level evidence plus the kit change that would prevent it |
| `/retro` | Weekly engineering retro from real data — commits, merged PRs/MRs, reverts, CI failures, and specs/ escalations over a time window — ending with what to standardize next (CLAUDE.md rule, skill, hook, or checklist item) and who owns it |
| `/writing-skills` | Reference for authoring and pruning skills in this harness |

All plugins: [`../README.md`](../README.md).
