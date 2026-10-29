# The kickoff doc set

Read by `/kickoff`, and by the skills that start from it (`/agent-architect`, `/project-init`). Order is dependency order: each item narrows the ones after it, so gaps are grilled in this order too.

| # | Item | Sub-items (each is a matrix row) | Canonical file | Mandatory |
|---|------|----------------------------------|----------------|-----------|
| 1 | Requirements | users and the problem (one sentence) · top 3–5 tasks, each with one real example · out of scope · acceptance criteria / what "good" means | `docs/requirements.md` | yes |
| 2 | Prerequisites | accounts and access (repo, cloud, third parties) · keys and secrets (**names only**) · machine tools and versions · environments that must exist | `docs/prerequisites.md` | yes |
| 3 | Tech stack | language and runtime · frameworks · database · hosting · constraints the team imposes (approved libraries, licences) | `docs/stack.md` | yes |
| 4 | Data model | entities and relations · each traced to a requirement task · ownership / tenant key | `docs/erd.md` (Mermaid `erDiagram`) | when the app stores data |
| 5 | Architecture | shape (monolith, services, agent) · repo layout · auth and identity · integrations · key decisions with reasons | `docs/adr/0001-<topic>.md` | yes |
| 6 | Design | Figma / mockups link · screens in scope · viewports | link + list in `docs/requirements.md` § Design | when there is UI |
| 7 | External APIs | each system · spec or docs · auth mode (caller token or server credential) | `docs/api/<system>.openapi.yaml` + a line in the ADR | when it integrates |
| 8 | Non-functional | performance targets · security and compliance · privacy and retention · availability | `docs/requirements.md` § NFR | should |
| 9 | Delivery | environments · CI · deploy target · release cadence · who approves | `docs/stack.md` § Delivery | should |

An existing repo's facts (its `package.json`, schema, CI files) fill rows 3, 4 and 9 by reading, not asking. A gap in rows 3, 5, 8 or 9 is asked as a need (`${CLAUDE_PLUGIN_ROOT}/references/need-questions.md`), and its row records the tech with that need: `Postgres — from "thousands of users daily"`.

## How sources map

| The user gives | Fills | Do |
|----------------|-------|-----|
| PRD, BRD, user stories, tickets | 1, 6, 8 | quote tasks and criteria verbatim; link the original |
| ERD image, DBML, SQL, Prisma/Drizzle schema | 4 | convert to Mermaid; keep the original file |
| ADR, architecture doc, diagram | 3, 5, 7 | link it; restate only the decisions as ADR lines |
| Tech stack list, `package.json`, team standards | 3, 9 | read versions from manifests, not from prose |
| Figma link | 6 | record the link and the frames in scope; reading it is `/design-ui`'s job |
| OpenAPI, Postman, curl | 7 | store under `docs/api/`; a key inside it → rotate, keep the name |
| Onboarding / setup doc | 2, 9 | list each prerequisite as a checkable line |

## `docs/kickoff.md` template

```markdown
# Kickoff — <project>
Date: <YYYY-MM-DD> · Sources: <list of paths and links read>

| # | Item | Sub-item | Status | Source / decision |
|---|------|----------|--------|-------------------|
| 1 | Requirements | top tasks | ✅ | PRD.md:12-30 |
| 3 | Tech stack | database | ⛔ | PRD.md:40 says MySQL · stack.md:5 says Postgres |
| 4 | Data model | tenant key | ❌ → defaulted | `org_id` on every owned table (recommended) |

## Open risks
- <deferral or weak answer> — blocks <what>

## Start here
`/<next skill>` — <why>
```

Statuses: ✅ from a source · ⚠️ partial · ❌ missing · ⛔ conflict · n/a (with why) · *defaulted* (recommended option taken) · deferred (with what it blocks).
