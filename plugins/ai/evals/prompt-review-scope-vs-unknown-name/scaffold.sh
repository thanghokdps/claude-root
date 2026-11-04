#!/usr/bin/env bash
# Seeds a billiards-club agent whose OUT OF SCOPE line can refuse a name that is not in the roster.
set -euo pipefail
mkdir -p src/agent/tools
cat > src/agent/prompt.ts <<'EOF'
export const SYSTEM_PROMPT = `
## OVERVIEW
You are the assistant of a billiards club. You record match results for the club's roster.

## RESPONSE
To record a result, call \`recordMatch\` with the winner, the loser and the score.
Answer in the language of the message, in one or two sentences.

## OUT OF SCOPE
Decline in one line: questions about other people, payments, anything not about the club's matches.

## CONTEXT
Appended per run.
`;
EOF
cat > src/agent/tools/record-match.ts <<'EOF'
import { z } from "zod";

export const RECORD_MATCH = "recordMatch";

export const recordMatchSchema = z.object({
  winner: z.string(),
  loser: z.string(),
  score: z.string(),
});

export const recordMatchDescription = "Record the result of a match between two players.";
EOF
cat > src/agent/roster.ts <<'EOF'
export const ROSTER = ["Hi", "Long", "Minh", "Tuấn", "Vy"] as const;
EOF
