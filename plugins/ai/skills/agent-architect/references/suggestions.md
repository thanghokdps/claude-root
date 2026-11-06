# Suggestions — starters and follow-ups from the agent's scope

Read with `skeleton.md` § 4. Every skeleton ships chips: starters on an empty chat, follow-ups after each answer. Both come from what the agent can do, so the sample tool is already enough scope, and each new tool adds to it.

Run live on 2026-11-05 with a fake OpenAI server, on @copilotkit/react-core and runtime 1.84.1. Shape A on the embed server, in a browser: the starter showed, a chip sent its message, follow-ups showed after an answer, after Stop and after a reload, New chat went back to the starter, and each chat stayed one thread. With the model failing the suggestion call, the answer stayed and no chip showed. Shape M on `mastra build` with `@ag-ui/mastra` 2.0.2, by direct requests: the forced tool call came back, the token limit reached the model, and only the chat's thread was stored; its web client was not run. Shape B shares A's server code and was not run separately.

## Why not the stock default

`useConfigureSuggestions` with no `providerAgentId` runs the agent named `default`. Pointed at the chat agent it is wrong on every shape:

- **A/B.** `/agent/:id/suggest` skips CopilotKit's runner, but `LangGraphAgent` still runs on the LangGraph API, so the suggestion's throwaway `threadId` becomes a stored thread and a row in the sidebar. The graph's model also never binds `copilotkitSuggest`.
- **M.** `registerCopilotKit` uses `mode: "single-route"` (@ag-ui/mastra 2.0.2 `dist/copilotkit.mjs`), so the client takes the clone path over `agent/run` (@copilotkit/core 1.84.1 `generateSuggestions`). A provider with `memory` would store each suggestion as a thread.

So a second agent with no thread store provides the chips, on `MODEL_CHEAP`, and forces the tool on the server.

## The scope

One list on the server, one row per tool. A tool that is switched off leaves the list, so its chips go too. Add a row in the same change as the tool: `/agent-tool` and `/agent-feature` both do.

`src/<agent folder>/server/suggestions.ts` on A/B:

```ts
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import type { Env } from "../config/env";

export const SUGGESTIONS_AGENT_ID = "suggestions";
const SUGGESTIONS_PATH = /\/app-suggestions$/;
const SUGGEST_TOOL = "copilotkitSuggest";
const MAX_OUTPUT_TOKENS = 300;

interface Capability {
  summary: string;
  starter: { title: string; message: string };
}

// One row per tool: what the agent can do is what it may suggest.
function readCapabilities(env: Env): Capability[] {
  return env.TOOL_CURRENT_TIME
    ? [
        {
          summary: "tell the current date and time in any time zone",
          starter: {
            title: "Time in Tokyo",
            message: "What time is it in Tokyo?",
          },
        },
      ]
    : [];
}

export function suggestionsEnabled(env: Env): boolean {
  return env.SUGGESTIONS_ENABLED && readCapabilities(env).length > 0;
}

export function buildSuggestionsPrompt(env: Env): string {
  const scope = readCapabilities(env)
    .map(({ summary }) => `- ${summary}`)
    .join("\n");
  return `You suggest what the user could ask an assistant next.
The assistant can only:
- answer from general knowledge
${scope}
Suggest only what that list covers. Never suggest looking up the user's data or taking an action. Use the language of the conversation.`;
}

/** Runs in this process on the cheap model, so a suggestion never becomes a LangGraph thread. */
// shortcut: runs outside buildTraceCallbacks, so its tokens miss the trace; add a span when chip cost matters.
export function createSuggestionsAgent(env: Env): BuiltInAgent {
  return new BuiltInAgent({
    model: `openai/${env.MODEL_CHEAP}`,
    prompt: buildSuggestionsPrompt(env),
    toolChoice: { type: "tool", toolName: SUGGEST_TOOL },
    maxOutputTokens: MAX_OUTPUT_TOKENS,
    maxRetries: env.MODEL_MAX_RETRIES,
    maxSteps: 1,
  });
}

export function suggestionsResponse(
  request: Request,
  env: Env,
): Response | null {
  if (!SUGGESTIONS_PATH.test(new URL(request.url).pathname)) return null;
  const enabled = suggestionsEnabled(env);
  return Response.json({
    starters: enabled
      ? readCapabilities(env).map(({ starter }) => starter)
      : [],
    followUps: enabled,
  });
}

/** The chips run only through the suggestions agent's stateless route. */
export function isBlockedSuggestionRoute(
  request: Request,
  assistantId: string,
): boolean {
  const { pathname } = new URL(request.url);
  return (
    pathname.endsWith(`/agent/${assistantId}/suggest`) ||
    (pathname.includes(`/agent/${SUGGESTIONS_AGENT_ID}/`) &&
      !pathname.endsWith("/suggest"))
  );
}
```

The model string is `<provider>/<model>`: change `openai/` with the provider of `MODEL_CHEAP`. Add `SUGGESTIONS_ENABLED: onOff.default("on")` to the env schema and to `.env.example`.

## Wiring on A/B

In `server/copilotkit.ts`, beside the chat agent and inside `onRequest`, after the 401 guard:

```ts
agents: ({ request }) => ({
  [AGENT_ID]: /* the LangGraphAgent */,
  ...(suggestionsEnabled(env)
    ? { [SUGGESTIONS_AGENT_ID]: createSuggestionsAgent(env) }
    : {}),
}),
```

```ts
if (isBlockedSuggestionRoute(request, AGENT_ID)) {
  throw Response.json({ error: "not_found" }, { status: 404 });
}
const scope = suggestionsResponse(request, env);
if (scope) throw scope;
```

`filterRunRequest` cuts a run to its newest turn, which would leave the model only the instruction. In `run-request-filter.ts`, give the suggest route its own filter. The last answer was written from redacted input, so no earlier user turn reaches this path, which has no PII middleware:

```ts
// Chips need the last answer and the instruction only. Earlier user turns may hold PII this path never redacts.
function filterSuggestInput(input: Json): Json {
  const messages = (input.messages ?? []) as RunMessage[];
  const lastAnswer = messages.findLast(({ role }) => role === "assistant");
  const instruction = messages.at(-1);
  return {
    ...input,
    messages: [lastAnswer, instruction].filter(Boolean),
    forwardedProps: {},
  };
}
```

```ts
const isSuggest = new URL(request.url).pathname.endsWith("/suggest");
const filterInput = isSuggest ? filterSuggestInput : filterRunInput;
```

Use `filterInput` where `filterRunRequest` called `filterRunInput`.

## Wiring on M

A second Mastra agent with no `memory`, from the same list. Build the instructions and the starters as above, and answer `/app-suggestions` with `registerApiRoute` beside the thread routes. Leave the agent out of `agents` when `suggestionsEnabled` is false.

```ts
const suggestions = new Agent({
  id: "suggestions",
  name: "suggestions",
  instructions: buildSuggestionsPrompt(env),
  model: cheapModel,
  defaultOptions: {
    toolChoice: { type: "tool", toolName: "copilotkitSuggest" },
    maxSteps: 1,
    modelSettings: { maxOutputTokens: 300 },
  },
});
```

The log prints `No memory is configured but resourceId and threadId were passed` for this agent on each run: that is the point. M has no request filter, so the whole history reaches `MODEL_CHEAP`: when `PII_REDACTION` turns on for M, add the same trim.

## The client

`src/hooks/use-chat-suggestions.ts`, called in the component that renders `CopilotChat`, with `RUNTIME_URL` already naming the runtime route. `consumerAgentId` is required, because outside `CopilotChat`'s own provider the hook falls back to the agent `default`.

```ts
import { useConfigureSuggestions } from "@copilotkit/react-core/v2";
import { useEffect, useState } from "react";
import { AGENT_ID, RUNTIME_URL } from "@/constants";

interface SuggestionScope {
  starters: { title: string; message: string }[];
  followUps: boolean;
}

const NO_SUGGESTIONS: SuggestionScope = { starters: [], followUps: false };

/** The server names the scope, so a tool switched off loses its chips too. */
export function useChatSuggestions(): void {
  const [scope, setScope] = useState(NO_SUGGESTIONS);

  useEffect(() => {
    let isCurrent = true;
    fetch(`${RUNTIME_URL}/app-suggestions`)
      .then((response) => (response.ok ? response.json() : NO_SUGGESTIONS))
      .then((next: SuggestionScope) => {
        if (isCurrent) setScope(next);
      })
      // No chips is a working chat, so a failure here stays silent.
      .catch(() => undefined);
    return () => {
      isCurrent = false;
    };
  }, []);

  useConfigureSuggestions(
    scope.starters.length > 0
      ? {
          suggestions: scope.starters,
          available: "before-first-message",
          consumerAgentId: AGENT_ID,
        }
      : null,
    [scope],
  );

  useConfigureSuggestions(
    scope.followUps
      ? {
          instructions:
            "Offer follow-up questions on the assistant's last answer.",
          providerAgentId: "suggestions",
          consumerAgentId: AGENT_ID,
          available: "after-first-message",
          maxSuggestions: 3,
        }
      : null,
    [scope],
  );
}
```

Send the same auth headers as `lib/threads-api.ts`. On M, `RUNTIME_URL` must not start with `/api`: Mastra refuses a custom route there at boot (`must not start with "/api"`).

## Tests

- Server: `/app-suggestions` with no caller → 401; with one → the starters and `followUps: true`; `TOOL_CURRENT_TIME=off` or `SUGGESTIONS_ENABLED=off` → `{ starters: [], followUps: false }` and no `suggestions` agent in the runtime's `info`.
- Routes: `POST /agent/<chat agent>/suggest` and `POST /agent/suggestions/run` → 404 on A/B.
- Filter: the suggest route passes only the last assistant message and the instruction, with empty `forwardedProps`; a normal run is unchanged.
- Prompt: `buildSuggestionsPrompt` names each capability and refuses data look-ups and actions.
- Live: one turn, then the thread list has exactly one row and the captured model request used `MODEL_CHEAP` with the forced tool. With that call failing, the answer stays and no chip shows.
