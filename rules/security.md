# Security — hard gates (block and escalate)

- Secrets: never hardcode, log, or commit keys/tokens/passwords/PII; env vars or secret stores only. A committed secret is compromised — rotate it.
- Every mutating endpoint is authenticated and checks permission on the specific resource; never trust client-supplied IDs for authorization.
- JWT: verify signature, expiry, issuer — never decode without verify. Session cookies HttpOnly + Secure + SameSite.
- Validate all external input at the boundary (body, query, headers, webhooks). Parameterized queries only.
- Block on sight: `eval`/`exec`/shell with user input, `innerHTML`/`dangerouslySetInnerHTML` with unsanitized input, SQL string concatenation, disabled TLS verification, `chmod 777`, `sudo` in app code.
- New dependency: check maintainer, downloads and what it does; run the package manager's audit before shipping.
