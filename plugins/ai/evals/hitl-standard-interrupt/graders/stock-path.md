---
type: llm
---

On AG-UI 1.0 with CopilotKit v2 the stock confirm path exists and should be the plan.

PASS if the reply plans the gate as `interrupt()` in the tool (or `humanInTheLoopMiddleware`), the card rendered with `useInterrupt` (resolve / cancel), and the decision returned through the next run's `resume` (`RunAgentInput.resume` / `Command({ resume })`), with no upstream write before the decision.
FAIL if it plans a custom decision endpoint or a `CUSTOM` interrupt event as the main path, says `useInterrupt` is unavailable, or uses `useHumanInTheLoop` as the gate.
