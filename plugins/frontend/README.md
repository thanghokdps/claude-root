# frontend

Role pack for web UI: the `frontend-engineer` agent that `/feature`, `/ticket` and `/fix-bug` dispatch screen slices to, the two skills it runs, and the React / Next.js rules it reads on demand. Off by default; core's `repo-profile` hook turns it on in a repo whose manifest has react, next, vue, svelte or vite (React Native alone is the `mobile` pack's).

**For:** frontend developers, and every `/feature` run that includes a screen.

## Agent

`agents/frontend-engineer.md` (sonnet) builds exactly one slice from the supervisor's brief — screen, states, contract types to import, files, test, done check — by running the skills below, and reports in three lines. The endpoint behind the screen, chat surfaces on CopilotKit (`agent` pack) and React Native screens are not its job.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/ui-feature` | A page, form, dialog or screen in React with no design to match: feature folder, typed fetchers to the app's own backend, every state (loading, empty, error, optimistic rollback), accessibility, tokens, Testing Library tests, a browser check per viewport | "làm màn hình settings với form đổi mật khẩu" |
| `/design-ui` | A page must match a Figma link, exported frames or a screenshot. Exports frames, maps variables to tokens, builds the design's components once as primitives, diffs screenshots at the frame size and narrow widths | "làm UI theo figma này" |

## Rules and references

`rules/react.md`, `rules/nextjs.md` — read by the agent and the skills when the repo uses them, never always-loaded. `references/fetchers.md` — how a screen calls its own backend. `references/taste.md` — the UI quality review both skills end with.
