# init-project — Bootstrap .claude/ harness from src/ scan

**Invoke:** `/init-project`

**What it does:** Scan the project to detect tech stack, then generate a full `.claude/` harness — agents, commands, hooks, rules, skills, memory, settings.json, CLAUDE.md — tailored to the detected stack. Then runs `/project-init` to generate the `.claude/docs/` knowledge base.

---

## Stage 0 — Pre-flight

1. Verify we are in a git repo root (check for `.git/`)

2. Resolve the harness source directory (`HARNESS_DIR`) in this order:

   ```bash
   # 1. Env var (set by install.sh)
   if [ -n "$HARNESS_DIR" ] && [ -d "$HARNESS_DIR" ]; then
     echo "Using HARNESS_DIR=$HARNESS_DIR"

   # 2. Default install location
   elif [ -d "$HOME/.claude-harness" ]; then
     HARNESS_DIR="$HOME/.claude-harness"
     echo "Using ~/.claude-harness"

   # 3. Original download location
   elif [ -d "$HOME/Downloads/Claude" ]; then
     HARNESS_DIR="$HOME/Downloads/Claude"
     echo "Using ~/Downloads/Claude (consider running install.sh)"

   # 4. Adjacent to global ~/.claude
   elif [ -d "$HOME/.claude-harness-src" ]; then
     HARNESS_DIR="$HOME/.claude-harness-src"

   else
     echo "❌ Harness not found. Run: bash ~/Downloads/Claude/scripts/install.sh"
     exit 1
   fi
   ```

3. If `.claude/settings.json` already exists → warn and ask before overwriting

---

## Stage 1 — Detect stack

```bash
# Package manager
[ -f pnpm-workspace.yaml ] || grep -q '"packageManager".*pnpm' package.json 2>/dev/null && echo "pnpm"
[ -f yarn.lock ] && echo "yarn"
[ -f package-lock.json ] && echo "npm"
[ -f requirements.txt ] || [ -f pyproject.toml ] && echo "python"

# Framework
grep -q '"react-native"' package.json 2>/dev/null && echo "react-native"
grep -q '"expo"' package.json 2>/dev/null && echo "expo"
grep -q '"next"' package.json 2>/dev/null && echo "nextjs"
grep -q '"fastapi"' requirements.txt pyproject.toml 2>/dev/null && echo "fastapi"
grep -q 'langgraph' requirements.txt pyproject.toml 2>/dev/null && echo "langgraph"

# Monorepo
[ -f turbo.json ] && echo "turborepo"
[ -f pnpm-workspace.yaml ] && echo "pnpm-monorepo"
```

Map signals to a stack profile:

| Signals | Stack profile |
|---------|--------------|
| `react-native` or `expo` | `react-native` |
| `next` | `nextjs` |
| `fastapi` or `langgraph` or `python` | `python` |
| `typescript` only | `typescript` |
| none of the above | `generic` |

---

## Stage 2 — Create .claude/ structure

```bash
mkdir -p .claude/agents .claude/commands .claude/docs/solutions .claude/hooks .claude/rules .claude/skills .claude/templates specs
```

### 2a. Copy universal agents (all stacks)

From `$HARNESS_DIR/agents/`:
- `pm-agent.md` → `.claude/agents/pm-agent.md`
- `architect.md` → `.claude/agents/architect-agent.md`
- `developer-agent.md` → `.claude/agents/developer-agent.md`
- `auto-dev.md` → `.claude/agents/auto-dev.md`
- `implementer.md` → `.claude/agents/implementer.md`
- `verifier.md` → `.claude/agents/verifier.md`
- `reviewer.md` → `.claude/agents/reviewer-agent.md`
- `qa.md` → `.claude/agents/qa-agent.md`

**Customize each agent file**: replace any `{{PROJECT_NAME}}` placeholder with the actual project name detected from `package.json` `name` field or directory name.

### 2b. Copy universal commands (all stacks)

From `$HARNESS_DIR/commands/`:
- `ticket.md` → `.claude/commands/ticket.md`
- `task.md` → `.claude/commands/task.md`
- `auto.md` → `.claude/commands/auto.md`
- `compact.md` → `.claude/commands/compact.md`
- `compound.md` → `.claude/commands/compound.md`

### 2c. Copy universal hooks (all stacks)

From `$HARNESS_DIR/hooks/`:
- `agent-progress.sh` → `.claude/hooks/agent-progress.sh`
- `headroom-compress.sh` → `.claude/hooks/headroom-compress.sh`

```bash
chmod +x .claude/hooks/*.sh
```

### 2d. Copy universal templates (all stacks)

From `$HARNESS_DIR/templates/`:
- `SUMMARY.template.md` → `.claude/templates/SUMMARY.template.md`
- `ESCALATIONS.template.md` → `.claude/templates/ESCALATIONS.template.md`
- `TEST_MATRIX.template.md` → `.claude/templates/TEST_MATRIX.template.md`
- `AGENT_WATCHER.template.md` → `.claude/templates/AGENT_WATCHER.template.md`

### 2e. Copy stack-specific rules + skills

**react-native stack:**
```bash
cp "$HARNESS_DIR/stacks/react-native/rules/"* .claude/rules/
cp -r "$HARNESS_DIR/stacks/react-native/skills/"* .claude/skills/
```

**nextjs stack:**
```bash
cp "$HARNESS_DIR/stacks/nextjs/rules/"* .claude/rules/
```

**python stack:**
```bash
cp "$HARNESS_DIR/stacks/python/rules/"* .claude/rules/
```

**generic / typescript stack:**
- No stack-specific rules — global rules from `~/.claude/rules/` cover it

---

## Stage 3 — Write settings.json

Write `.claude/settings.json` tailored to the detected package manager and stack:

```json
{
  "permissions": {
    "allow": [
      "Bash(*)", "Read(*)", "Edit(*)", "Write(*)", "WebFetch(*)", "WebSearch(*)"
    ],
    "deny": [
      "Bash(rm -rf *)", "Bash(rm -r *)",
      "Bash(git push --force*)", "Bash(git push -f *)",
      "Bash(git reset --hard*)", "Bash(git clean -f*)",
      "Bash(git push * main)", "Bash(git push * master)",
      "Bash(git branch -D *)", "Bash(kill -9 *)", "Bash(killall *)",
      "Bash(sudo *)", "Bash(curl * | bash)", "Bash(wget * | bash)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": ".claude/hooks/commit-gate.sh"}]
      },
      {
        "matcher": "Agent",
        "hooks": [{"type": "command", "command": ".claude/hooks/agent-progress.sh pre"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": ".claude/hooks/typecheck-on-edit.sh"}]
      },
      {
        "matcher": "Agent|Edit|Write|Bash",
        "hooks": [{"type": "command", "command": ".claude/hooks/agent-progress.sh post"}]
      },
      {
        "matcher": "Bash|Read",
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/headroom-compress.sh",
          "asyncRewake": true,
          "statusMessage": "Checking context size..."
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/session-handoff.sh"},
          {"type": "command", "command": "~/.claude/hooks/state-breadcrumb.sh"}
        ]
      }
    ]
  }
}
```

**Stack adjustments:**
- `react-native` / `pnpm`: add `.claude/hooks/typecheck-on-edit.sh` (runs `pnpm --filter <app> check-types`)
- `python`: replace typecheck-on-edit with `$HARNESS_DIR/hooks/stacks/ruff-on-edit.sh`
- `typescript` / `nextjs`: use `$HARNESS_DIR/hooks/stacks/eslint-on-edit.sh`

Also create a minimal `commit-gate.sh` that enforces the commit format defined in `CLAUDE.md`.

---

## Stage 4 — Bootstrap memory

```bash
mkdir -p .claude/memory/feedback .claude/memory/project .claude/memory/commits .claude/memory/sessions
```

Copy templates from `$HARNESS_DIR/memory/templates/`:
- `MEMORY.md.template` → `.claude/memory/MEMORY.md` (replace `{{PROJECT_NAME}}`)
- `user.md` → `.claude/memory/user.md` (replace `{{GIT_USER}}`, `{{GIT_EMAIL}}`)
- `project.md` → `.claude/memory/project/context.md` (replace `{{PROJECT_NAME}}`, `{{STACK_LIST}}`, `{{INIT_DATE}}`)

---

## Stage 5 — Generate CLAUDE.md

Write `CLAUDE.md` from `$HARNESS_DIR/templates/CLAUDE.md.template`:
- Replace `{{PROJECT_NAME}}` with actual project name
- Replace `{{STACK_LIST}}` with detected stack
- Replace `{{INIT_DATE}}` with today's date
- Add project-specific run commands if detectable from `package.json` scripts

If `CLAUDE.md` already exists with content → append a `## Harness (auto-generated)` section instead of overwriting.

---

## Stage 6 — Run project-init (knowledge base)

After the harness is bootstrapped, immediately run `/project-init` to scan the codebase and generate `.claude/docs/`:
- `architecture.md` — layers, data flow, key decisions
- `conventions.md` — naming, imports, patterns, anti-patterns
- `stack.md` — tech stack, run commands, test commands
- `entry-points.md` — API routes, jobs, CLI commands
- `test-strategy.md` — test structure, markers, conventions

This is mandatory — without `.claude/docs/`, agents will re-scan the codebase on every task instead of reading the pre-built knowledge base.

---

## Stage 7 — Report

```
## init-project complete — <ProjectName>

**Stack detected**: <react-native | nextjs | python | typescript | generic>
**Package manager**: <pnpm | yarn | npm | pip>
**Harness source**: <HARNESS_DIR value used>

### Files created
.claude/
├── agents/          (8 agents)
├── commands/        (5 commands)
├── hooks/           (commit-gate, agent-progress, headroom-compress, typecheck-on-edit)
├── rules/           (<N> rules — universal + stack-specific)
├── skills/          (<N> skills — stack-specific)
├── templates/       (4 templates)
├── memory/          (bootstrapped with user + project context)
├── docs/            (generated by /project-init)
└── settings.json

CLAUDE.md            (fill in: run commands, architecture, constraints)

### Next steps
1. Fill in the <!-- ... --> sections in CLAUDE.md
2. Add project goals to .claude/memory/project/context.md
3. Run /project-init if docs/ is incomplete
```

## Hard gates

- If `.claude/settings.json` already exists → warn and ask before overwriting
- If `CLAUDE.md` already exists with non-template content → append, never overwrite
- Never copy `.env` or secret files from the harness source
- If `HARNESS_DIR` cannot be resolved → fail with clear error and install instructions
