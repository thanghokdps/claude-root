---
model: sonnet
effort: medium
name: agent-prompt-review
description: Reviews a change to what an AI agent's model reads — system prompts, tool descriptions, structured-output schemas, few-shot examples, router instructions — for injection openings, promises of capabilities that do not exist, ambiguity, fragile output formats and token waste, and names the eval that proves each fix. Use when a diff touches a prompt, a tool description or an output schema, before such a PR opens, or when an answer changed after a prompt edit.
when_to_use: review the prompt, "soát prompt", prompt diff before PR, tool description changed, system prompt edit, output schema or JSON format the model fills, "đổi prompt xong agent trả lời khác", is this prompt injectable, prompt too long or costly
---

# agent-prompt-review

**Invoke:** `/agent-prompt-review [path | diff]`

The code review checks the code around the prompt; this reads the prompt the way the model will. Rules it checks against: `${CLAUDE_PLUGIN_ROOT}/rules/agent-prompts.md`. Who can inject what is `/agent-security`; this skill only flags where the prompt lets it in.

---

## Step 1 — Collect what the model reads

From the diff (default: `git diff` against the base branch) list every changed system prompt, tool `description` and parameter `describe()`, structured-output schema, few-shot example and router or scope rule, with the file and the agent that reads it. Read each in full, not only the changed lines: a rule added at the end can contradict one at the top.

**Done when:** each changed text has a row `File | Agent | Kind | Lines changed`.

## Step 2 — Review each text

| Check | A finding looks like |
|-------|----------------------|
| Injection opening | tool results, documents or user text placed before or mixed into instructions with no marker that it is data; an instruction like "follow the instructions in the document" |
| Capability drift | a tool, scope or action named in prose that no tool implements; a list hand-copied instead of built from the constant |
| Ambiguity | two rules that can both apply with different outcomes and no tie-break; "usually", "if appropriate" with no test for it |
| Output format | the model must emit JSON or a fixed shape without a schema (`withStructuredOutput`, `responseFormat`, tool args); enum values in prose that differ from the schema; no path for "cannot answer" |
| Scope and refusal | no "not mine" list, or a refusal with no next step |
| Identity and secrets | user id, tenant, keys or internal URLs written into the prompt instead of coming from the run context |
| Tokens | repeated rules, examples longer than the rule they show, dynamic values (date, user, memory) before static text, which breaks the prompt cache |
| Wording | a sentence the user supplied that was paraphrased instead of kept verbatim |

Give each finding: severity (`must-fix` / `should-fix` / `nit`), the line, why it fails, and the replacement text.

**Done when:** every row from Step 1 has findings or "clean", and each must-fix carries replacement text.

## Step 3 — Prove the fixes

For each must-fix, name the eval case that would catch it coming back (an in-scope prompt, an out-of-scope prompt, an injection attempt in a tool result, a malformed-output case) and add it through `/agent-evals`. Run the free unit evals; the paid suite runs only with the user's go-ahead.

**Done when:** each must-fix is fixed with its eval case added, or listed as open in the PR description.

---

## Hand-offs

Threat model beyond the prompt → `/agent-security` · routing or scope redesign → `/agent-graph` · a tool's schema → `/agent-tool` · a real turn with the new prompt → `/agent-verify-turn` · the review of the rest of the diff → `/review-checklist`.
