# Need questions — ask what the user gets, map it to tech yourself

Read by `/kickoff` and `/brainstorming` before any question about stack, architecture, non-functional needs or delivery.

"Angular or React?" asks the user to do the engineering. "A large enterprise app, or quick and lean?" asks what only they know; the tech follows from the answer.

## Rules

- **Ask the need, never the tool.** The option label is the need in the user's words; its `description` says what it changes, then the tech it maps to in one parenthesis — `Ships in weeks, one small team (→ Next.js full-stack)` — so a technical user can still see and override it.
- **A tech question is asked only** when the user named the tech or asked at tech level. Then ask it in their terms.
- **What the need settles is a fact**, never a second question. A tech choice the need leaves open is a decide-tier choice (`/resolve-question`, dev, if installed): decided with a note, not asked.
- **Record the tech with the need it came from**: `Postgres — from "thousands of users daily"`. When a need changes later, its line shows which tech to revisit.

## Translation table (a starting set; add rows as projects teach you)

| Need question | Options → maps to |
|---------------|-------------------|
| What kind of app is it? | Large enterprise: many teams, years of life, strict structure → Angular or NestJS, modular monorepo · Quick and lean: one small team, ship fast → Next.js full-stack |
| Where are your users? | In a browser → web app · On their phone → React Native (Expo) · Both → responsive web, mobile later on the same API |
| How many people use it? | Hundreds → one Postgres, one server · Thousands every day → Postgres + cache, horizontal app servers · Big spikes (sales, events) → queue + autoscaling |
| Who runs it after launch? | Our developers → custom code · A non-tech team edits content → headless CMS · Nobody, set and forget → managed / serverless hosting |
| Does it hold sensitive data? | No → baseline security · Personal data → PII rules, encryption at rest · Health or payment data → high-risk lane, compliance review |
| What is the first milestone? | A demo in weeks → scaffold, defaults, skip non-functional rows · Production in months → full non-functional rows, CI and environments |
| Must it be live or work offline? | Neither → request/response · Live updates → WebSockets or SSE · Works offline → local-first storage + sync |
| Where may it run? | Anywhere cheap → Vercel, Fly · Our company cloud → that provider's managed services · Our own servers → Docker on-prem |
