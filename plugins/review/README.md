# review

Review a diff or PR: review-checklist, review-diff, blast-radius impact analysis, create-pr description, resolve-pr-feedback.

## Install

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
/plugin install review@harness
```

GitLab needs the VPN and an SSH key. Outside it, add the GitHub mirror instead: `/plugin marketplace add thanghokdps/claude-root`.

Also installs: `progress`.

## Skills

| Skill | Does |
|-------|------|
| `/blast-radius` | Change-impact analysis before merge — traces every caller, consumer, contract, job, and migration a change touches, scores the risk, flags untested paths, and demands a rollback plan |
| `/create-pr` | Generates a structured PR description from the current branch diff |
| `/resolve-pr-feedback` | Works through a PR/MR's open review threads — fix, answer, decline with evidence, or ask the author — then one validated push and a reply on every thread |
| `/review-checklist` | Reviews the current diff or a PR in a fixed order — correctness → tests → readability → security → scope — and returns at least three actionable comments plus a PR-description check |
| `/review-diff` | Generates a comprehensive Markdown review of the current git diff or a specified PR — including an architecture diagram (Mermaid), component flowchart, and code walkthrough with inline diff blocks |

All plugins: [`../README.md`](../README.md).
