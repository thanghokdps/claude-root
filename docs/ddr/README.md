# Kit decision records

Why the kit is built the way it is. One file per decision: the context, the decision, what it costs, and where it lives in the code. When a reviewer asks "why is it like this", answer with the link.

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-role-plugins.md) | Role plugins in one marketplace, not one flat plugin | Accepted |
| [0002](0002-versions-stay-1-0-0.md) | Every plugin stays at 1.0.0 until the kit is published | Accepted |
| [0003](0003-model-by-role.md) | Opus decides, Sonnet writes code, Haiku does mechanical work | Accepted |
| [0004](0004-assistant-models-from-the-problem.md) | An assistant's models come from its hardest task, volume and budget | Accepted |
| [0005](0005-hooks-enforce-the-process.md) | Hooks enforce the process; a skill alone is a reminder | Accepted |
| [0006](0006-evidence-over-claims.md) | Evidence over claims: run logs, citations, before and after | Accepted |
| [0007](0007-routing-is-tested.md) | Every skill's routing is tested for free; behaviour evals are paid and run before releases | Accepted |
| [0008](0008-install-from-gitlab.md) | The team installs from the GitLab marketplace; GitHub is the mirror | Accepted |

New record: next number, same four sections (Context, Decision, Consequences, Where), one page at most. A record is never rewritten: a changed decision gets a new record that says which one it replaces.
