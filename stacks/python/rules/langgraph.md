# LangGraph rules

## State invariants

- `messages` uses `messagesStateReducer` — **never overwrite**, only return delta
- Every node returns `Partial<StateType>` with ONLY the fields it changes
- `session` and `modelName` are write-once at graph entry — never mutate in nodes

```typescript
// CORRECT — return delta only
return { messages: [aiResponse, ...toolResults], phase: "done" };
// WRONG — clobbers history
return { messages: [...state.messages, aiResponse] };
```

## Tools pattern

```typescript
import { tool } from "@langchain/core/tools";  // NOT from "ai"
import { z } from "zod";

export const myTool = tool(
  async (args) => {
    const result = await myHandler(args);
    return typeof result === "string" ? result : JSON.stringify(result);
  },
  {
    name: TOOL_NAME.MY_TOOL,
    description: TOOL_DESCRIPTION.MY_TOOL,
    schema: z.object({ param: z.string() }),
  }
);
```

## HITL mutation gate

Any tool that modifies data must go through HITL:
1. `executeNode` detects mutation → sets `pendingTool`, returns early
2. `hitlNode` calls `interrupt()` → graph STOPS
3. UI shows confirmation card
4. User approves/rejects → `Command({ resume })` continues the graph

`interrupt()` called ONLY in `hitlNode` — never in `executeNode`.

## streamEvents — always v2

```typescript
leaveGraph.streamEvents(input, { version: "v2", ...runConfig })
```

## SqliteSaver — singleton rule

One instance at module level. Never create per-request:
```typescript
const checkpointer = SqliteSaver.fromConnString("server/db/langgraph.sqlite");
export const graph = compiled.compile({ checkpointer });
```

## ReAct loop — max steps

Set a max iteration limit in `executeNode`. Break on: no tool_calls, mutation detected, terminal tool reached.

## temperature: 0

All models used for routing or structured output must have `temperature: 0`.

## AG-UI event order (if used)

```
TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_END → TOOL_CALL_RESULT
```
`TOOL_CALL_END` must come BEFORE `TEXT_MESSAGE_END` — violating this causes RUN_FINISHED error.
