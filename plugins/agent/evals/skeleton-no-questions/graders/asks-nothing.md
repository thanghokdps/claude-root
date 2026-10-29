---
type: llm
---

The request names its stack (Next.js, CopilotKit, LangGraph) and asks for an empty chatbot with no features, so skeleton mode applies and nothing is left to ask.

PASS if the reply asks no question at all: no AskUserQuestion call, no prose question, no "accept the card?". It treats LangGraph as `createAgent` (shape A), shows the defaults as information (purpose "a general chat assistant", stock CopilotChat, tasks deferred to agent-feature), and moves on to the ADR or the scaffold. A prerequisite report (missing Node, key or git) is fine, and so is a blocker report when the run denies the commands the scaffold needs: asking the user to allow them, or how to go on without them, is not an interview question.
FAIL if it asks about the users or purpose (P1), the tasks (P2), the systems (P3), what to refuse (P4), writes (Q4), the design or Figma (Q-D), auth, host, clients, layout, or the framework; or if it asks the user to accept the defaults card.
