# 0001 — Role plugins in one marketplace, not one flat plugin

**Status:** Accepted

## Context

Every installed skill's `description` is loaded into every session so Claude can route a prompt to it. A flat plugin with ~50 skills puts all of them in every session, and two skills with close descriptions start to compete for one prompt.

## Decision

One marketplace, `harness`, with one plugin per role: `agent`, `dev`, `plan`, `review`, `ship`, `core`, `lead`, `progress`, `guards`, and the `harness` bundle that depends on all nine. Each plugin declares its dependencies in `plugin.json`. Someone building an AI assistant runs one command, `/plugin install agent@harness`, and Claude Code installs what `agent` depends on.

## Consequences

- An assistant developer loads only the skills their work uses, not the kit authors' retro and skill-writing skills or the opt-in guard hooks.
- A skill may name another plugin's skill only when that plugin is a dependency; `scripts/lint-kit.py` fails otherwise. Without the dependency it writes "(<plugin>, if installed)".
- Ten plugins look like "a lot" from outside. The answer is that a user installs one.

## Where

`.claude-plugin/marketplace.json`, `plugins/*/.claude-plugin/plugin.json`, `DESIGN.md` §1.
