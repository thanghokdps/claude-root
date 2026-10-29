# Refute before report

Read by the review skills before they report. A finding is a candidate until an agent that did not write it fails to refute it. The person who found a bug is the worst one to check it: their context has turned assumptions into facts. Adapted from cloudflare/security-audit-skill (validation phase) and addyosmani/agent-skills `doubt-driven-development`.

## When

Run it on every candidate finding, unless there are none. Run it again on a finding that a refuter upgraded or whose case it changed.

## How

1. **Extract.** For each candidate, give the claim in one line, the cited `path:line`, and the failing case. Leave out your reasoning and severity: a refuter handed a conclusion validates it.
2. **Dispatch** fresh `Agent`s in one message on `model: "opus"` (`~/.claude/rules/model-cost.md`: verification stays on Opus), one per ≤5 candidates and none given another's result. The prompt opens:

   > You did not write these findings. Try to refute each one from the source. Re-read every cited line and the code around it; find the caller, guard, validation, transaction or framework behaviour that prevents the case. Run a cheap local repro when one exists. Never contact deployed services. For each finding return one verdict: `confirmed` (the case happens as stated), `needs_validation` (it turns on a fact you cannot see from here: name that fact and who or what can answer it) or `rejected` (with the line that refutes it).

3. **Reconcile.** Each verdict must cite what it rests on. Drop a verdict that cites nothing and re-dispatch that finding. A refuter that strengthens a finding (higher severity, a different case) does not get the final word: send the new version to a fresh refuter. Stop after 3 cycles. A finding still disputed after that is `needs_validation`.

## Verdicts in the report

| Verdict | Goes in | Carries |
|---------|---------|---------|
| `confirmed` | the numbered findings | its severity, case, fix and skip cost |
| `needs_validation` | a separate list | the exact missing fact plus who or what answers it, with **no severity**. It never parks a vague worry: a candidate with no concrete fact to check is rejected |
| `rejected` | one line each under `Rejected:` | the refuting `path:line`, so the next run does not raise it again |

## Degraded mode

Inside a subagent, where no `Agent` tool exists, write each candidate as a fresh prompt below a hard separator, run step 2's prompt against yourself, and print `Refute: degraded (self-review)` above the findings. Prefer handing the findings back to the main session when it can be reached.
