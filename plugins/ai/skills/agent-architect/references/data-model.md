# Data model (ERD) from a design

When the user has no ERD and asks for one from the design, write `docs/erd.md` before the schema, so the schema is generated from a reviewed model rather than invented while coding.

1. **Inventory what the frames show:** every list, card, field, badge, counter and setting is a candidate attribute; every "of a user" or "in a conversation" is a relationship. Note the frame per entity.
2. **Add what the frames imply but do not show:** auth tables come from the chosen auth library's own schema (name them as it does); ids, timestamps, soft delete, ordering keys, and the agent's own needs (thread id ↔ conversation, message parent for edit/regenerate, tool call records if the ADR keeps them).
3. **Write it as Mermaid `erDiagram`:** one block per entity with type, PK/FK/UK, and a quoted note tracing the attribute to the frame text or to the decision that added it. Under the diagram, a table `Entity | Frame / reason | Notes`.
4. **Ask only real forks**, as options (`interview.md` § Shape of each question): e.g. branching messages or linear history, per-user settings row or key-value, plan limits in a table or in config.
5. **Generate the schema from the ERD** (Drizzle/Prisma) and keep them equal: every entity is a table, every table is in the ERD.

**Done when:** each entity cites a frame or a decision, and the table names in the schema equal the ERD's entities (`grep` both lists and diff them).
