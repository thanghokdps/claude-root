# review

Review a diff, a PR or a whole repo and come back with numbered findings, each with the concrete case that fails, the fix and the cost of skipping it.

**For:** reviewers, and authors reviewing themselves before the PR. Read-only except `/resolve-pr-feedback`, which makes the fixes a review asked for.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/review-checklist` | Before opening a PR, or reviewing a teammate's. Fixed order: correctness → tests → scale → readability → security → scope, plus a PR-description check. Complements the built-in `/code-review` | "review this before I open the PR" |
| `/blast-radius` | A diff touches shared code and you want to know what else it breaks: callers, consumers, contracts, jobs, migrations, untested paths, rollback plan, with `file:line` evidence | "safe to merge? what does this break?" |
| `/review-diff` | Onboarding a reviewer to a large change. A Markdown walkthrough with a Mermaid architecture diagram, a component flowchart and inline diff blocks | `/review-diff` |
| `/resolve-pr-feedback` | A PR or MR has open review threads. Sorts each into fix, answer, decline with a reason or the author's call, makes the fixes in one validated push, replies on every thread | "xử lý comment review trên PR 42" |
| `/create-pr` | You want the PR description text only: title, summary (why, not how), tasks, file table. Does not push or open the PR | `/create-pr` |
| `/debt-ledger` | Before a release, a scale-up or a cleanup sprint. Lists every `shortcut:` comment with its limit and the trigger to revisit it, and flags shortcuts that name no trigger | "what did we defer?" |
| `/repo-audit` | Taking over a codebase or before a big change to it. At most 20 findings in Must / Should / Nice: bugs, security and data-loss risks, what breaks at load, risky code without a test, code to delete or merge | "rà soát toàn bộ repo này" |

## Hooks

None.

## Depends on

`progress`.

## Install

```text
/plugin install review@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
