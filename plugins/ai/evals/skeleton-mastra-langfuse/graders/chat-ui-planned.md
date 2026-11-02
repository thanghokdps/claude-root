---
type: llm
---

The request names its stack (Mastra, Langfuse tracing) and asks for an empty chatbot. The expected result is an app the user can open and chat with, not only an HTTP API.

PASS if the run treats it as a skeleton on Mastra (shape M) and its plan or scaffold includes a chat page (CopilotKit's stock chat on Next.js by default) plus one real streamed turn, with Langfuse wired through Mastra observability behind a tracing switch. A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it builds or proposes only a backend endpoint with no chat UI, switches to LangChain or LangGraph, treats Langfuse as a feature to ask about, or asks about users, purpose, auth, hosting or layout.
