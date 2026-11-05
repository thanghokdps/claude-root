---
type: llm
---

The request names its stack (Next.js, CopilotKit, LangGraph) and asks for an empty chatbot with no features, so nothing is left to ask. New apps use Vite here, so the named Next.js becomes Vite, said in one line.

PASS if the plan or scaffold uses Vite, not Next.js, says so in one line, and the reply asks no question at all: no AskUserQuestion call, no prose question, no "accept these defaults?". It states the defaults it picked as information (for example a general chat assistant, the stock chat UI, features left for later) and moves on to recording the decision or scaffolding. A prerequisite report (missing Node, key or git) is fine, and so is a blocker report when the run denies the commands the scaffold needs: asking the user to allow them, or how to go on without them, is not an interview question. So are the two questions the skeleton ends on, once it is built: creating `.env` and adding the key, and where to deploy through `/release-setup`.
FAIL if it plans Next.js, scaffolds into a new subfolder of this empty folder, or asks about users or purpose, tasks, connected systems, what to refuse, writes, the design, auth, hosting, clients, repo layout or the framework; or if it asks the user to approve the defaults.
