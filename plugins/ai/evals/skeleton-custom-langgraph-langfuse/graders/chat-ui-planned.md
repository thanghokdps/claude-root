---
type: llm
---

The request names its stack (a custom LangGraph graph, Langfuse tracing) and asks for an empty chatbot. The expected result is an app the user can open and chat with, not only an HTTP API.

PASS if the run treats it as a skeleton on a custom `StateGraph` (shape B, not `createAgent`) and its plan or scaffold includes a chat page (CopilotKit's stock chat on Next.js by default) plus one real streamed turn, with the Langfuse callback handler behind a tracing switch. A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it builds or proposes only a backend endpoint with no chat UI, uses `createAgent` instead of a custom graph, treats Langfuse as a feature to ask about, or asks about users, purpose, auth, hosting or layout.
