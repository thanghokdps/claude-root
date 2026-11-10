# OWASP ASVS 5.0 map for check 5 (security)

Read by `/review-checklist` when the repo's spec, CLAUDE.md or `.claude/docs/` names an ASVS level or SOC 2 readiness. ASVS 5.0.0 was published on 30 May 2025 ([asvs.owasp.org](https://asvs.owasp.org/)); the chapter names below are from the [v5.0.0 source](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en) (read 2026-11-10). Which requirements a level adds is in that source: open the chapter and read the level column before you call a finding "required at L2". Do not quote a level from memory.

## How to use it

1. Map each changed area of the diff to its chapters with the table.
2. For each chapter touched, check the diff against that chapter's requirements at the repo's level, opened from the source this session.
3. A finding names the requirement id (for example `V8.x.y`), the failing case, and the fix, like any other check-5 finding. A requirement the diff does not touch is not a finding.
4. SOC 2 readiness asks for evidence, not only controls: note in the PR description which control the change affects (access, change management, logging, backup), and what proves it (a test, a log line, a runbook entry).

## Diff area → ASVS 5.0 chapters

| The diff touches                                  | Chapters                                                     |
| ------------------------------------------------- | ------------------------------------------------------------ |
| Rendering user content, Markdown, HTML sanitising | V1 Encoding and Sanitization, V3 Web Frontend Security       |
| Input schemas, limits, business rules             | V2 Validation and Business Logic                             |
| Routes, API responses, CORS, WebSocket upgrades   | V4 API and Web Service, V3 Web Frontend Security             |
| Uploads, downloads, file links                    | V5 File Handling, V8 Authorization                           |
| Sign-in, MFA, account recovery                    | V6 Authentication, V10 OAuth and OIDC                        |
| Sessions, sign-out, revocation, deactivation      | V7 Session Management                                        |
| Permission checks, roles, owner scoping           | V8 Authorization                                             |
| ID tokens, JWTs, signed URLs                      | V9 Self-contained Tokens, V11 Cryptography                   |
| Keys, hashing, randomness                         | V11 Cryptography                                             |
| TLS, origins, outbound calls                      | V12 Secure Communication                                     |
| Config, secrets, environments, headers            | V13 Configuration                                            |
| Retention, backups, exports, PII in logs          | V14 Data Protection, V16 Security Logging and Error Handling |
| Audit log, error handling, alerts                 | V16 Security Logging and Error Handling                      |
| Dependencies, architecture, unsafe code           | V15 Secure Coding and Architecture                           |
| Calls, huddles, media streams                     | V17 WebRTC                                                   |
