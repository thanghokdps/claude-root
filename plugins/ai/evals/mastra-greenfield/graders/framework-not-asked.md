---
type: llm
---

The user already named the framework (Mastra) and the UI (CopilotKit), so the framework question Q-F is a fact, not a question.

PASS if the reply does not ask the user to choose between Mastra, LangChain and LangGraph, and does not recommend a different framework. It may restate "Mastra" as the reading for the user to correct, and it may go on to a problem question (P1–P4).
FAIL if it asks which agent framework to use, or proposes createAgent/StateGraph instead of Mastra without the user asking.
