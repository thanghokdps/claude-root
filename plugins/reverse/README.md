# reverse

Domain pack for reverse engineering what ships without its source: native binaries, managed assemblies, APKs and IPAs, Electron ASARs, firmware, web bundles and captures. It vendors the `reverse-engineer-anything` skill from [morluto/rea](https://github.com/morluto/rea) (MIT) and registers REA's `rea` MCP server.

**For:** anyone who needs to explain how a shipped app does something, compare two released versions, or decompile an artifact. Off by default, because the server starts with every session of a repo that enables it.

## Skills

| Skill                        | Use it when                                                                                                                                                                                                    | Example prompt                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `/reverse-engineer-anything` | A claim depends on a shipped app, binary, APK, ASAR or firmware with no source: explain a feature, decompile, compare versions, capture traffic. Every conclusion separates observation, inference and unknown | "how does search work in the Notes app? show me the evidence" |

## MCP server

`rea` — `npx --yes --ignore-scripts rea-agents@6.8.0 mcp`, pinned to the version the skill was copied with (upstream `c78c8ae`, skill version 61). `--ignore-scripts` keeps npm from running install scripts of the package or its dependencies. Needs Node `^22.23.4 || ^24.22.1 || >=26.12.1`; native analysis also needs an existing Hopper, Ghidra, IDA or Kuna.

To update: copy `.agents/skills/reverse-engineer-anything/` from upstream over `skills/reverse-engineer-anything/` (keep this kit's frontmatter fields and provenance comment), and bump the pin here and in `.claude-plugin/plugin.json` together. The folder is in `.prettierignore` so the copy stays byte-identical.

## Hooks

None of its own. Core's `repo-profile` hook enables it in a repo whose `docs/requirements.md` or `.claude/docs/index.md` has a `Domain: reverse-engineering` line; the switch is written to `.claude/settings.local.json`, effective next session. An explicit `false` in project or local settings wins.

## Depends on

`progress`.

## Install

```text
/plugin install reverse@harness
```

`scripts/install.sh` installs it off at user scope. To turn it on in one repo without the marker line:

```bash
claude plugin enable reverse@harness --scope project
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
