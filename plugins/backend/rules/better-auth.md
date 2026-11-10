---
paths:
  - "**/auth.ts"
  - "**/auth/**/*.ts"
  - "**/lib/auth.ts"
---

# Better Auth rules

Sign-in is a hard gate (auth/authz): a change here is high-risk and goes through `/security-review`. This file adds only what is Better Auth-specific; sessions, cookies and permission checks in general are in core's `security.md`. Claims cite better-auth.com/docs (read 2026-11-10, the 1.7 line). Pin the version, and read the docs for that version: the site keeps one index per release line ([llms.txt](https://www.better-auth.com/llms.txt)).

## Sessions

- Sessions are server-side rows, and a revoke has to take effect at once. Leave `session.cookieCache` off, which is the default: it is opt-in ([session management](https://www.better-auth.com/docs/concepts/session-management)). With it on, a revoked session "may remain active on other devices until the cookie cache expires" ([session management](https://www.better-auth.com/docs/concepts/session-management)). If a team turns it on for load, every sensitive read and the socket upgrade call `getSession` with `disableCookieCache: true`, which reads the database ([session management](https://www.better-auth.com/docs/concepts/session-management)).
- `expiresIn` is a sliding window: when a session is used past `updateAge`, its expiry moves to now plus `expiresIn` ([session management](https://www.better-auth.com/docs/concepts/session-management)). So `expiresIn` is the idle timeout. An absolute cap (for example 7 days from sign-in) is not that setting. Check it in the session middleware against the session's `createdAt`, and reject and revoke past it.
- A role change, deactivation or offboarding deletes that person's session rows in the same write that changes the role or status. It also closes their open sockets (`cloudflare-workers.md` § Durable Objects).
- The session middleware checks the user's own status (deactivated, role) on every request and on every socket open, not only at sign-in. A Google account that still works is not permission.

## Google sign-in

- Restrict to the company's Workspace with `hd: "<domain>"` on the Google provider. Better Auth enforces the hosted-domain claim in the signed token, and with `hd` set, a token that has no `hd` claim is rejected ([Google](https://www.better-auth.com/docs/authentication/google)). Never replace this with a check on the email suffix.
- A custom `getUserInfo` replaces the built-in callback-path `hd` check ([Google](https://www.better-auth.com/docs/authentication/google)). If you need one, it re-checks `hd` itself, and a test proves a token from another domain is refused.
- Key a person by Google's `sub` (the account id), never by email: an email can be renamed or reused. The list of allowed domains, when the app keeps one, lives in the database and is checked in a sign-in hook. A refused sign-in writes an audit row.
- Each environment has its own OAuth client. The redirect URI is `<BETTER_AUTH_URL>/api/auth/callback/google` and must match exactly ([Google](https://www.better-auth.com/docs/authentication/google)).

## Schema on D1 with Drizzle

- The Better Auth CLI cannot reach D1, and `getMigrations` does not work with the Drizzle adapter ([database](https://www.better-auth.com/docs/concepts/database)). Generate the auth tables into the Drizzle schema with the CLI, then ship them as ordinary migrations (`drizzle.md` § SQLite and Cloudflare D1). Never create them at runtime.
- Secrets (`BETTER_AUTH_SECRET`, the Google client secret) are per-environment Worker secrets, never `vars` and never the asset build.

## Tests

- Sign-in tests stub Google at the HTTP boundary. They cover: an allowed domain → a session; a token with another `hd` or none → refused and audited; a deactivated user with a live session → 401 on the next request and the socket closed; a session past the absolute cap → 401.
- After each Better Auth upgrade, re-run these tests and re-read the changelog's session and cookie entries before merging.
