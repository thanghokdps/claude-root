---
type: llm
focus:
  source: file
  path: theme/tokens.ts
---

This is `theme/tokens.ts` after the run.

PASS if all hold: (1) the existing file was extended, with colours defined by role for both light and dark; (2) #0F766E stays the brand accent, with a dark value that remains readable; (3) spacing has distinct steps and named text styles exist; (4) the run reports contrast measured with the script rather than estimated.
FAIL if the file is empty or missing, if a second theme file holds the tokens instead, or if only light values exist.
