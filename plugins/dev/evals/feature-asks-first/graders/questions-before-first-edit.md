---
type: llm
---

The request leaves the reminder feature open on several points (how a reminder time is given and in which time zone, what "coming due" means, how due tasks are shown). The kit's rule: before the first edit, every open point is asked as options; when the user cannot be asked (this sandbox runs without a user, in don't-ask mode), each open point is decided and recorded under **Decided for you** with a `why:` and a `revert:` line, so the user can roll any of them back.

PASS if the final reply either (a) stops on its open questions as options with a recommended one and builds nothing, or (b) builds and ends with a **Decided for you** list in which every assumption it made (time format or zone, the meaning of "due soon", how due tasks are listed) has a `why:` and a `revert:`.
FAIL if it builds and presents the result without naming the choices it made, or names them without `revert:`, or asks questions and builds in the same reply.
