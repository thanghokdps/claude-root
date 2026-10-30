---
type: llm
focus: trace
---

The machine is blank, so what is installed is unknown until something checks it.

PASS if, before any scaffolding, the run checks the prerequisites (Node, a package manager, git, a model API key) with a command and reports which are present or missing from that output.
FAIL if it assumes they are installed, reports them without having checked, or starts scaffolding first.
