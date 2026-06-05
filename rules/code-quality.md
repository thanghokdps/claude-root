# Code Quality Rules

Universal code quality principles for all projects and languages.

## Readability

- Code is read 10x more than written — optimize for the reader
- Names tell what, not how: `getUserById` not `fetchUserFromDbWithId`
- Functions do one thing — if you need "and" to describe it, split it
- Max function length: ~30 lines. If longer, extract helpers
- Nesting depth > 3 levels = extract or use guard clauses

## Guard clauses (fail fast)

Prefer early returns over nested conditionals:

```typescript
// Bad
function process(user) {
  if (user) {
    if (user.isActive) {
      if (user.hasPermission) {
        doWork(user);
      }
    }
  }
}

// Good
function process(user) {
  if (!user) return;
  if (!user.isActive) return;
  if (!user.hasPermission) return;
  doWork(user);
}
```

## DRY — but not prematurely

- Three or more identical blocks → extract to a function
- Two similar blocks → wait and see (premature abstraction costs more than duplication)
- Shared logic between files → move to a shared module
- Shared logic between layers → reconsider the architecture

## Comments

- Comments explain WHY — not WHAT (code shows what)
- Good comment: `// Firebase requires the token to be refreshed before expiry, not after`
- Bad comment: `// Get user by id`
- Delete outdated comments immediately — stale comments are worse than none

## Dead code

- Delete unused code immediately — version control remembers it
- Never comment out code "just in case" — use git blame/revert
- Unused imports, variables, functions: delete

## File organization

- One primary export per file
- Group related functions together
- Constants at the top or in a dedicated constants file
- Types near the code that uses them (or in a dedicated types file)

## Performance basics

- Avoid N+1 queries — batch database calls
- Don't do I/O inside loops — batch or pre-fetch
- `O(n²)` algorithms are fine for n < 100; not fine for n > 1000
- Profile before optimizing — never guess where the bottleneck is

## Language-specific supplements

Read these in addition:
- TypeScript: `~/.claude/rules/typescript.md`
- React Native: `.claude/rules/react-native.md` (project-level)
- Cloudflare Workers: `.claude/rules/cloudflare-workers.md` (project-level)
