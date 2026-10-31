#!/bin/bash

# UserPromptSubmit hook: flag implementation-intent prompts for the Auto-Coordinator.
# Emits only what CLAUDE.md cannot know — the keyword scan result. The routing steps
# themselves are already in context from CLAUDE.md; repeating them here just doubles
# the prompt.
# Acts on the event's cwd (process cwd only when .cwd is empty).

INPUT=$(cat)
CWD=$(jq -r '.cwd // empty' <<<"$INPUT" 2>/dev/null)
[ -n "$CWD" ] && { cd -P "$CWD" 2>/dev/null || true; }

PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // ""')
WORD_COUNT=$(printf '%s' "$PROMPT" | wc -w)

IS_IMPL=0
printf '%s' "$PROMPT" | grep -qiE '\b(add|implement|refactor|build|create|fix|change|improve|migrat|integrat|deploy|test|review|delete|remove|update|rename|move)\b' && IS_IMPL=1

IS_QUESTION=0
printf '%s' "$PROMPT" | grep -qiE '^\s*(what|how|why|when|where|which|who|can you explain|tell me|explain|show me|describe)' && IS_QUESTION=1
# A trailing ? or a Vietnamese question particle (hả, không, chưa, à, nhỉ, sao) also marks a question
printf '%s' "$PROMPT" | grep -qiE '(\?|(^|[[:space:]])(hả|không|chưa|à|nhỉ|sao))[[:space:][:punct:]]*$' && IS_QUESTION=1

# A command the user ran in the shell (! or <bash-input>) is not a request to Claude
printf '%s' "$PROMPT" | grep -qE '^\s*(!|<bash-(input|stdout)>)' && exit 0

# Already using a skill explicitly — don't double-inject
HAS_SKILL=0
printf '%s' "$PROMPT" | grep -qiE '^/(coordinator|ticket|task|brainstorming|writing-plans|btw|compact|compound|project-init)' && HAS_SKILL=1

if [ "$WORD_COUNT" -gt 4 ] && [ "$IS_IMPL" -eq 1 ] && [ "$IS_QUESTION" -eq 0 ] && [ "$HAS_SKILL" -eq 0 ]; then

  RISK_HIT=$(printf '%s' "$PROMPT" | grep -oiE '\b(auth|login|password|jwt|token|payment|stripe|database|migration|schema|permission|role|admin|security|prod|production)\b' | head -1)

  if [ -n "$RISK_HIT" ]; then
    SIGNAL="high-risk keyword \"$RISK_HIT\" matched — confirm scope before dispatching agents."
  else
    SIGNAL="no high-risk keyword matched."
  fi

  jq -cn --arg signal "$SIGNAL" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: ("AUTO-COORDINATOR: implementation intent detected — apply the Auto-Coordinator section of CLAUDE.md; " + $signal)
    }
  }'

fi

exit 0
