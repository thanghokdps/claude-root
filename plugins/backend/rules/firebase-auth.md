---
paths:
  - "**/auth/**/*.ts"
  - "**/middleware/**/*.ts"
  - "**/lib/firebase*.ts"
---

# Firebase Authentication rules (ID tokens verified on Workers)

Auth is a hard gate: every change here is high-risk. Data access is `firestore.md`; the generic contract is core's `security.md`. Claims cite firebase.google.com, developers.google.com and docs.cloud.google.com (read 2026-11-10).

## Verify every ID token

- On Workers there is no Admin SDK, so verify the ID token yourself with `jose`. Accept it only if **all** hold: `alg` is RS256; `kid` matches one of Google's securetoken public keys; `exp` is in the future and `iat` and `auth_time` in the past; `aud` is the project id; `iss` is `https://securetoken.google.com/<projectId>`; `sub` is non-empty, and it is the uid ([verify ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens)). Cache the public keys for the `max-age` in the key endpoint's `Cache-Control` header, never longer.
- Verification lives in one middleware that sets the user on the context. A route never decodes a token itself, and never uses a decode without verify.
- The project id, and with it `aud` and `iss`, comes from the environment's config. A staging token must fail on production.

## Who may sign in

- Restricting Google sign-in to the company domain with the `hd` parameter is only a UI hint and is not access control. Check the signed claim on the server ([Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)). In Firebase, check the verified email's domain against the allowed list on every first sign-in, and require `email_verified` to be true (compare defensively: Google's sample shows the string `"true"`).
- Identify a person by the Firebase `uid` (`sub`), never by email: emails can be renamed or reused.
- A refused sign-in is written to the audit log with the email and the reason, and the person sees a clear refusal.

## Sessions, revocation, deactivation

- ID tokens last 1 hour; the client refreshes them from a long-lived refresh token, so by default a person stays signed in until sign-out ([manage sessions](https://firebase.google.com/docs/auth/admin/manage-sessions)). A product rule such as "3 days idle or 7 days after sign-in" is not enforced by Firebase. Enforce it on the server: the absolute cap from the token's `auth_time`, the idle cap from a last-seen record the server keeps. If the spec and the stack disagree on this, it is an open question for the team, not a choice for the build.
- `revokeRefreshTokens(uid)` stops new ID tokens, but a token already issued stays valid until it expires unless the server checks revocation ([manage sessions](https://firebase.google.com/docs/auth/admin/manage-sessions)). On Workers, keep a per-user status (active, deactivated, tokens-valid-after) that the middleware checks on every request and the socket checks on connect, so a deactivation or role change takes effect at once, not within the hour.
- Deactivation does three things in one service function: disable the Firebase account (Identity Toolkit `accounts:update` with `disableUser: true`, needing the `firebaseauth.users.update` permission, [accounts.update](https://docs.cloud.google.com/identity-platform/docs/reference/rest/v1/projects.accounts/update)), revoke refresh tokens, and set the status that closes open sockets. Each step is tested; the audit log records who did it.
- A WebSocket authenticates with the ID token on the upgrade request, verified like any other request. A token that expires mid-connection does not end the socket by itself, so the status check above is what closes it.

## Google access tokens for server calls

- Server calls to Firestore REST, Identity Toolkit and FCM use an OAuth 2.0 access token minted from the service account: sign a JWT (RS256) with `iss` the service-account email, `scope` space-delimited, `aud` `https://oauth2.googleapis.com/token`, `exp` at most 1 hour after `iat`, then POST it with `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer` ([service account OAuth](https://developers.google.com/identity/protocols/oauth2/service-account)).
- Mint one token per scope set, cache it until a few minutes before `expires_in`, and never log it or the private key.

## Tests

- Middleware tests with tokens signed by a test key: valid, wrong `aud`, wrong `iss`, expired, future `iat`, missing `kid`, other domain, unverified email, deactivated user, `auth_time` past the cap. Each wrong one returns 401.
- Flows run against the Auth emulator (`firestore.md` § Local and tests), never a real project.
