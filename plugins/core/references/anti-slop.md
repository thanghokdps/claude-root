# anti-slop for TypeScript

[dmmulroy/anti-slop](https://github.com/dmmulroy/anti-slop) (MIT) — Oxlint rules that reject low-evidence TypeScript: chained type assertions, `unknown` widening, ad hoc `typeof` narrowing, module mocking, `Reflect.get/apply`, accumulator copies. It is meant to be **vendored**: there is no npm package, and the copy belongs to the repo.

Read by `/project-init` (Step 1b) for any repo with `tsconfig.json` or TypeScript in `package.json`.

## Pinned upstream

`13909c9e07590f5a85d93c62712259fe14a883f7` (2026-10-14). Use this SHA unless the user names another; a newer one is read and diffed before it is used.

## Install

1. **Skip** when `tools/oxlint/anti-slop/` already exists, or the repo lints with Biome only and the user declines adding Oxlint.
2. **Copy** upstream `src/` at the pinned SHA into `tools/oxlint/anti-slop/`:
   ```bash
   tmp=$(mktemp -d) && git -C "$tmp" init -q && git -C "$tmp" fetch -q --depth 1 https://github.com/dmmulroy/anti-slop <SHA> \
     && git -C "$tmp" checkout -q FETCH_HEAD && mkdir -p tools/oxlint && cp -R "$tmp/src" tools/oxlint/anti-slop
   ```
   Write `tools/oxlint/anti-slop/UPSTREAM` with the repo URL, the SHA and the date, so a later update can three-way merge.
3. **Dependencies** — exact versions, both moving together: an existing `oxlint` keeps its version and `@oxlint/plugins` is added at the same one; otherwise both at the version upstream's `package.json` pins at that SHA. Use the repo's package manager, then its audit.
4. **Config** — `oxlint.config.ts` (or merge into the existing one): `jsPlugins: [{ name: "anti-slop", specifier: "./tools/oxlint/anti-slop/index.ts" }]`, every generic rule from upstream's README, `oxc/no-accumulating-spread`, and `ignorePatterns` for `tools/oxlint/anti-slop/**` and the agent folders (`.claude/**`, `.agents/**`, `.cursor/**`, …). The Effect rule group only when the repo depends on `effect`.
5. **Script** — `"lint:slop": "oxlint"`; the repo's `lint` script runs it after ESLint. CI runs `lint`, so nothing else changes.

## Severity

| Repo | Rules start as | Then |
|------|----------------|------|
| New (scaffold, no source yet) | `error` | — |
| Existing code | Run once, report violations per rule, and ask: `error` now and fix (Recommended when under ~30), or `warn` with a dated ratchet in `.claude/docs/conventions.md` | Each rule moves to `error` once its count is 0 |

Never silence a rule inline without a comment saying why; `require-safety-comment-for-type-assertion` enforces it for assertions.

## Done when

`pnpm lint` (or the repo's equivalent) runs anti-slop and exits 0, `UPSTREAM` records the SHA, and `.claude/docs/conventions.md` names the vendored folder as the team's to edit.
