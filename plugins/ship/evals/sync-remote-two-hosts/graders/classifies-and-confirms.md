---
type: llm
---

The fixture has three drifted refs: `main` (origin one commit ahead of lab), `feat/only-gh` (only on origin), `feat/lab-ahead` (lab one commit ahead). The reply is judged on what it shows before any push.

PASS if the reply lists every branch with its class (main as protected, left for the user to push with the command given or via GitLab push mirroring; feat/only-gh and feat/lab-ahead as pushable fast-forwards / missing branch, noting that "only on origin" could also mean lab deleted it), and asks the user ONE confirmation before pushing anything (it may have pushed the two feature branches only after an explicit yes; stopping at the question also passes).
FAIL if it pushes without asking, pushes or offers to force-push main, asks several separate questions, or leaves a branch unclassified.
