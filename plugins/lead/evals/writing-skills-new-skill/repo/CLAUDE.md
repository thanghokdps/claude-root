# Demo skill library

Skills live in `plugins/<plugin>/skills/<name>/SKILL.md`.

## How to add a skill

1. `SKILL.md` frontmatter: `name` (= directory), `description` (what + "Use when ..."), `when_to_use`, `model`, `effort`.
2. `eval/triggers/<name>.json`: 3 prompts that must rank it top-3, 1 owned by a neighbour skill.
3. Add the row to `plugins/README.md`.

Allowed frontmatter keys: name, description, when_to_use, model, effort, context, agent, background,
allowed-tools, arguments, paths, disable-model-invocation. Any other key (`color`, `isolation`, `tags`) is
silently ignored by Claude Code, and the lint fails on it.
