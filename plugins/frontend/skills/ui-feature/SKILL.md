---
model: opus
effort: high
name: ui-feature
description: Builds or changes a frontend feature in a React app (default and verified on Next.js App Router) the way the repo already builds them. It covers the feature folder, typed fetchers, hooks, and components built from the repo's primitives, with every state (loading, empty, error, optimistic update and rollback), accessibility, design tokens instead of raw values, and responsive layout. It proves the feature with Testing Library tests and a browser check at the project's viewports. Use when the user asks for a page, screen, form, dialog or other UI with no design to match, or to fix UI behaviour. A Figma or mockup to match goes to design-ui first.
when_to_use: build a page, "làm màn hình", "làm giao diện bằng React", form, dialog, settings page, list with search, frontend feature, React component, loading or empty or error state, UI not updating after save, optimistic update, accessibility, responsive layout
---

# ui-feature

**Invoke:** `/ui-feature <what the user should see and do>`

Rules: `app-structure.md` and `testing.md` from core, plus `${CLAUDE_PLUGIN_ROOT}/rules/react.md` and, on Next.js, `${CLAUDE_PLUGIN_ROOT}/rules/nextjs.md`. A design to match (Figma, frames, screenshot) → `/design-ui` builds the primitives and screens from it. This skill builds behaviour on top.

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| Feature folders | `src/features/<f>/{components,hooks,api.ts,index.ts}` or the repo's equivalent |
| Primitives | `src/components/ui/`, the UI library (shadcn/Radix, MUI…), `cn()` / cva variants, the icon set |
| Tokens | `styles/tokens.css`, Tailwind theme |
| Data fetching | `fetchJson`-style helper, TanStack Query/SWR, Server Components, the `api.ts` pattern |
| Tests | Testing Library + jsdom config, existing component tests, a `/design-states` or Storybook page |
| Viewports | the ADR, the design doc, or the existing breakpoints |

**Done when:** each row names a path. The screen's states are listed: default, loading, empty, error, and for writes saving, saved and failed (the value before the write is back on screen), plus any role-specific views. A form that edits an existing value (a profile name, a setting) loads that value first; "" is not a previous value.

## Step 2 — Tests first, from what the user sees

Write Testing Library tests for the states and interactions in Step 1, with the fetchers mocked at the `api.ts` boundary:

- Query by role and label (`getByRole("button", { name: "Save" })`), never by class or test id when a role exists.
- Write flows assert the request sent **and** the UI after success and after failure (rollback plus an error message).
- Keyboard: tab order, Enter and Escape on dialogs, focus moving to the dialog and back.

**Done when:** the tests fail for the right reason.

## Step 3 — Build

- Place it per `app-structure.md`: the page in `app/` renders the feature, the logic lives in `features/<f>/`, and other features import it only through `index.ts`.
- Use the primitives from `components/ui/`. No raw `<button>`/`<input>` outside them, no raw hex or one-off px (tokens only), and icons from the one set at its sizes. A missing primitive or variant is added there once (with its own test), not inlined.
- Data: typed fetchers in `api.ts`, with types imported from the backend schema, never re-declared (`${CLAUDE_PLUGIN_ROOT}/references/fetchers.md`). In a server-rendering framework, fetch on the server when the data does not depend on client state.
- Every state is real UI: a skeleton or spinner, an empty state with the next action, an error with retry, and disabled controls while saving. A write is optimistic: keep the value from before the write in state, show the new one at once, and on failure put the old one back (input and any place the value is displayed) and announce the error — a form that only shows the error and leaves the unsaved text in the input has no rollback.
- Accessible names on controls, labels tied to inputs, errors announced (`aria-live` or `role="alert"`), contrast through tokens.
- Mobile first: base classes are the narrowest viewport, and `md:`/`lg:` add the wider layout.

**Done when:** the Step 2 tests pass, plus typecheck and lint, and the raw-hex grep (`grep -rnE '\[#[0-9a-fA-F]{3,8}\]' src`) finds nothing outside `styles/` and `dev/`.

## Step 4 — Prove it in the browser

Run the app (or the design-states page) and drive the feature with Playwright MCP or Claude in Chrome. Use each project viewport (e.g. 375 / 1024 / 1440): click through the happy path and one failure, check the console has no errors, and take a screenshot per viewport.

**Done when:** the screenshots and a clean console are shown, at every viewport.

## Step 5 — Quality floor and taste

Follow `${CLAUDE_PLUGIN_ROOT}/references/taste.md`: create `DESIGN.md` / `PRODUCT.md` if missing, save the Step 4 screenshots to `design/actual/<state>.png`, evaluate `dump-ui-styles.js` in each state and run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/check-ui.py` on the dumps, then dispatch the taste reviewer with only the screenshots and those two files.

**Done when:** `check-ui.py` exits 0 or each remaining hit is a listed false positive, no P0/P1 taste finding is open without the user's acceptance, and both lists are in the reply and the PR description.

---

Hand-offs: a design to match → `/design-ui` · the endpoint behind it → `/api-endpoint` (backend, if installed) · a chat surface on CopilotKit → `/agent-frontend` (ai, if installed) · done → `/verify-done` → `/review-checklist`.
