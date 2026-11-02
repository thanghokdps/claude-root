---
type: llm
---

PASS if the reply explains that useMemo caches a computed value and useCallback caches a function reference (equivalent to useMemo(() => fn, deps)).
FAIL if it does not answer, or confuses what each hook returns.
