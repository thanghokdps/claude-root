# reverse

Domain pack for reverse engineering what ships without its source: native binaries, managed assemblies, APKs and IPAs, Electron ASARs, firmware, web bundles and captures. It vendors the `reverse-engineer-anything` skill from [morluto/rea](https://github.com/morluto/rea) (MIT) and registers REA's `rea` MCP server.

**For:** anyone who needs to explain how a shipped app does something, compare two released versions, or decompile an artifact. Off by default, because the server starts with every session of a repo that enables it.

## Skills

| Skill                        | Use it when                                                                                                                                                                                                    | Example prompt                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `/reverse-engineer-anything` | A claim depends on a shipped app, binary, APK, ASAR or firmware with no source: explain a feature, decompile, compare versions, capture traffic. Every conclusion separates observation, inference and unknown | "how does search work in the Notes app? show me the evidence" |

## MCP server

`rea` — `npx --yes --ignore-scripts --registry=https://registry.npmjs.org/ rea-agents@6.8.0 mcp`, pinned to the version the skill was copied with (upstream `c78c8ae`, skill version 61). `--ignore-scripts` keeps npm from running install scripts of the package or its dependencies; `--registry` on the command line wins over a repo's `.npmrc`, so a cloned repo cannot point the fetch at another registry. Second-level dependencies still resolve from version ranges (the package ships no shrinkwrap). Needs Node `^22.23.4 || ^24.22.1 || >=26.12.1`; native analysis also needs an existing Hopper, Ghidra, IDA or Kuna.

To update: copy `.agents/skills/reverse-engineer-anything/` from upstream over `skills/reverse-engineer-anything/` (keep this kit's frontmatter fields and provenance comment), and bump the pin here and in `.claude-plugin/plugin.json` together. The folder is in `.prettierignore` so the copy stays byte-identical.

## Hooks

None of its own. Core's `repo-profile` hook detects a `Domain: reverse-engineering` line in `docs/requirements.md` or `.claude/docs/index.md` and suggests the pack with the command below, but never enables it: the pack starts an npx server, and text in a cloned repo must not be able to switch that on.

## Evals

Run them on sonnet: `bash scripts/eval-plugin.sh reverse --model sonnet`. On Opus 5 a safety classifier (`[cyber]`) withholds the first reply of a reverse-engineering prompt, so the skill call never lands and the routing cases fail for a reason the skill does not control (2026-11-09: 1/3 on Opus 5, 3/3 on sonnet).

## Depends on

`progress`.

## Install

```text
/plugin install reverse@harness
```

`scripts/install.sh` installs it off at user scope. To turn it on for yourself in one repo, then open a new session:

```bash
claude plugin enable reverse@harness --scope local
```

`--scope project` instead writes it to the committed `.claude/settings.json`, turning it on for every teammate who trusts the folder.

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
