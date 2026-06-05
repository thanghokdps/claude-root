# Security Rules

Universal security rules. Hard gates — always block and escalate when violated.

## Secrets & credentials

- NEVER hardcode API keys, passwords, tokens, secrets in source code
- NEVER log secrets, tokens, or PII — mask before logging
- NEVER commit `.env`, `.dev.vars`, credential files
- Store secrets in: environment variables, secret managers (Vault, AWS Secrets Manager), platform secret stores
- Rotate any secret that was accidentally committed — treat as compromised immediately

## Authentication & authorization

- Every endpoint that mutates data MUST have authentication
- Every endpoint MUST verify the caller has permission for the specific resource (not just "is logged in")
- JWT: always verify signature, expiry, and issuer — never `decode` without `verify`
- Session tokens: HttpOnly, Secure, SameSite=Strict cookies
- Rate limit authentication endpoints

## Input validation

- Validate ALL external input at the system boundary — API inputs, query params, headers, webhooks
- Never trust client-supplied IDs for authorization — verify ownership server-side
- Sanitize before rendering in HTML — never `innerHTML = userInput`
- Parameterized queries only — never string-concatenate SQL

## Dependencies

- Pin dependency versions in production — no `*` or `^` ranges for security-sensitive packages
- Run `npm audit` / `pnpm audit` / `pip-audit` before shipping
- Review what a new package does before installing — check download count, maintainer, source

## Data

- Minimum data collection — don't store what you don't need
- Encrypt sensitive data at rest (PII, health data, financial data)
- HTTPS everywhere — no HTTP in production

## Code patterns to block (auto-escalate)

- `eval()` with user input
- `exec()` / `shell_exec()` with user input
- `innerHTML` / `dangerouslySetInnerHTML` with unsanitized input
- SQL string concatenation
- Disabling SSL verification (`verify=False`, `rejectUnauthorized: false`)
- `chmod 777`
- `sudo` in application code
