---
paths:
  - "**/*.{ts,tsx,mts,css}"
---

# Agent app code structure and conventions

Read by `/agent-architect` (scaffold), `/agent-design-ui` (build) and `/agent-feature` (every slice). The agent side is laid out in `skills/agent-architect/references/layouts.md`.

**The base is core's `app-structure.md`** (in `~/.claude/rules/` after the kit's `install.sh`, or in the project after `/project-init`): routes thin in `app/`, `features/<feature>/`, `components/ui/`, `server/<aggregate>/`, `server/<system>/`, `db/`, `lib/`, `dev/`, the test location rule, size and naming limits. Follow it; this file adds only what an assistant needs on top. With core's rule absent, the tree below is still the layout to use.

## What an assistant adds to the tree (L1; in L2 under `apps/web/src`)

```
src/
  agent/                    # per layouts.md (or src/mastra/ in shape M)
  server/<system>/          # external API clients, built by /api-client and reused by agent tools (agent-tool Step 0)
  styles/                   # tokens.css + the CopilotKit theme scoped under [data-copilotkit]
  dev/                      # also the /__design states page and recorded chat states
e2e/                        # Playwright specs + recorded AG-UI streams
evals/                      # agent evals (agent-evals), never run by `test`
```

- Agent tools import `server/<system>/` clients and `server/<aggregate>/` services; they never hold SQL or a second HTTP client for a system that already has one.
- The design's primitives go in `components/ui/` from the start, before the screens that use them, classified against the repo's UI library (`/design-ui` Step 3): a library primitive is installed or wrapped, never hand-rebuilt. CopilotKit slots render these same primitives.

## Styling (the gates `/agent-feature` Step 6 runs)

- Colours, radii, spacing, font sizes and shadows come from tokens (`styles/tokens.css` → Tailwind theme or CSS variables). No raw hex (`[#efefef]`) and no one-off pixel values (`w-[348px]`) in components; a value the design uses once goes into the ui-map as a one-off with its element, and then into a token.
- Gate: `grep -rnE '\[#[0-9a-fA-F]{3,8}\]' src` returns nothing outside `styles/` and `dev/`.
- Raw `<button>`, `<input>`, `<textarea>`, `<select>` and inline `<svg>` appear only inside `components/ui/`; screens use the primitives. Icons come from one library at the sizes of one scale (e.g. 16 / 20 / 24), through `Icon` or a size prop limited to that scale.
- A second element that looks like an existing primitive with different classes is a missing variant, not a new component.
- Mobile first: base classes are the smallest supported width; `md:` / `lg:` add the wider layout. Breakpoints come from the ADR's `Viewports:`.

## Tooling the scaffold sets up

Prettier with a `format:check` script, ESLint with the framework preset plus `import/order` and `no-restricted-imports` for `dev/`; CI runs format → typecheck → lint → tests, and evals in their own job.
