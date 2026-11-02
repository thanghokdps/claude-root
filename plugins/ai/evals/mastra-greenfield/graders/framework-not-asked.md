---
type: llm
---

The user already named the framework (Mastra) and the UI (CopilotKit), so the framework is a fact, not a question.

PASS if the reply does not ask the user to choose between Mastra, LangChain and LangGraph, and does not recommend a different framework. It may restate "Mastra" for the user to correct, and it may go on to a question about the problem (users, tasks, systems, scope).
FAIL if it asks which agent framework to use, or proposes LangChain/LangGraph instead of Mastra without the user asking.
