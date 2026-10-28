# 0008 — The team installs from the GitLab marketplace; GitHub is the mirror

**Status:** Accepted (28 Oct 2026)

## Context

The team's code lives on the company GitLab, and a clone-and-run-a-script install depends on where each person put the clone.

## Decision

The team installs inside Claude Code with `/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git`, then `/plugin install agent@harness`. Claude Code clones with the person's own git access, so Reporter access, the VPN and an SSH key are all it needs. `thanghokdps/claude-root` on GitHub is the public mirror, kept in step with `/sync-remote`, and the install path outside the VPN. Updates: `/plugin marketplace update harness`.

## Consequences

- No fixed install path on anyone's machine; nothing to clone for the plugins.
- A merge reaches the team only after GitLab is synced; `scripts/install.sh` warns when the two copies differ.
- The global rules and `~/.claude/CLAUDE.md` still come only from cloning the kit and running `scripts/install.sh`; the plugins work without them.

## Where

`.claude-plugin/marketplace.json`, `plugins/ship/skills/sync-remote/`, `scripts/install.sh`.
