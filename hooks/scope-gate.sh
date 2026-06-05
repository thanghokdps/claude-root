#!/bin/bash

# UserPromptSubmit hook: auto-trigger coordinator behavior for implementation prompts.
# Non-blocking — injects additionalContext that instructs Claude to run as coordinator.

INPUT=$(cat)

PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // ""')
WORD_COUNT=$(printf '%s' "$PROMPT" | wc -w)

IS_IMPL=0
printf '%s' "$PROMPT" | grep -qiE '\b(add|implement|refactor|build|create|fix|change|improve|migrat|integrat|deploy|test|review|delete|remove|update|rename|move)\b' && IS_IMPL=1

IS_QUESTION=0
printf '%s' "$PROMPT" | grep -qiE '^\s*(what|how|why|when|where|which|who|can you explain|tell me|explain|show me|describe)' && IS_QUESTION=1

# Already using a skill explicitly — don't double-inject
HAS_SKILL=0
printf '%s' "$PROMPT" | grep -qiE '^/(coordinator|ticket|task|brainstorming|writing-plans|btw|compact|compound|project-init)' && HAS_SKILL=1

if [ "$WORD_COUNT" -gt 4 ] && [ "$IS_IMPL" -eq 1 ] && [ "$IS_QUESTION" -eq 0 ] && [ "$HAS_SKILL" -eq 0 ]; then

  # Detect lane signals for smarter injection
  IS_HIGH_RISK=0
  printf '%s' "$PROMPT" | grep -qiE '\b(auth|login|password|jwt|token|payment|stripe|database|migration|schema|permission|role|admin|security|prod|production)\b' && IS_HIGH_RISK=1

  if [ "$IS_HIGH_RISK" -eq 1 ]; then
    LANE_HINT="Likely lane: high-risk — show routing summary and ask Proceed? before dispatching agents."
  else
    LANE_HINT="Likely lane: tiny or normal — classify, show 1-line routing summary, then execute immediately."
  fi

  jq -cn --arg lane "$LANE_HINT" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: ("AUTO-COORDINATOR ACTIVE: Treat this as a coordinator request. Do NOT wait for /coordinator to be typed.\n\nSteps:\n1. Load .claude/docs/ and docs/solutions/INDEX.md\n2. Classify intent + lane (tiny/normal/high-risk)\n3. Create TaskCreate entries for each agent step\n4. Dispatch agents with wave-based parallel execution (run_in_background: true for parallel tasks)\n5. Show status board\n\n" + $lane + "\n\nFor tiny lane + high confidence: skip routing summary, just execute with TaskCreate tracking.\nFor normal/high-risk: show `Intent · Lane · Routing` line first.")
    }
  }'

fi

exit 0
