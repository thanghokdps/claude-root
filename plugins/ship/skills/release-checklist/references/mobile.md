# Mobile release — Expo / EAS

Applies when the repo has `eas.json`. It replaces checklist items 3 (migrations), 7 (deploy) and 8 (smoke check) of `release-checklist`; the others stand.

## Enforcement

The `ship` hook `release-gate.sh` runs on every Bash command in an `eas.json` repo. It denies a production `eas build` / `eas submit` / `eas update` and a `v*` tag push unless a `release/<version>` PR (GitHub) or MR (GitLab) covers the commit and a person other than its author approved its current head. It also denies approving from this session. Config, all optional: `.claude/release-gate.json` → `{"profiles":["production"],"channels":["production"],"approvers":[]}`. If it denies, relay the reason; never retry with another profile, channel or `APP_VARIANT`. Rollback, republish and rollout commands on the production channel ask the user first.

GitLab's approvals API does not say which commit was approved, so on GitLab the gate trusts the MR's current approvals: turn on *Settings → Merge requests → Remove all approvals when commits are added* so a push after approval resets them.

## 1. Choose the route

- **Store build** when native code changed, the production runtime version / fingerprint differs from the last production build, or no production build exists yet. Check with `eas fingerprint:compare` or `eas build:list --profile production --limit 1`.
- **OTA update** otherwise, and the user wants it fast (urgent JS or asset fix). Offer it; the user decides. A staged rollout (`--rollout-percentage 10`) is optional.

State the route and the evidence for it before going on.

## 2. Release PR / MR

- Branch `release/<version>` from the base branch; the diff holds only the version bump and the `CHANGELOG` entry.
- Open the PR/MR with the notes from item 5. Someone other than the author approves it; the author cannot approve their own.
- Ship exactly the approved head commit (or its merge commit). Any commit added after the approval needs a new approval.

## 3. Ship the approved commit

Store build, from the approved commit with a clean tree:

```
eas build --profile production --platform all --non-interactive --json
eas submit --profile production --platform ios --id <ios build id> --non-interactive
eas submit --profile production --platform android --id <android build id> --non-interactive
```

Submit by build id, never `--latest`: the latest build may not be this release's.

OTA:

```
APP_VARIANT=production eas update --channel production --environment production --message "<version>: <summary>"
```

## 4. Tag

Tag the shipped commit and push only that tag: `git tag -a v<version> -m "Release <version>" <sha>` then `git push origin v<version>`. Never `git push --tags`. Once the tag exists, the gate refuses to ship that version from another commit.

## 5. Rollback

- OTA: `eas update:rollback`, or republish the previous update group (`eas update:list`, then `eas update:republish --group <id>`).
- Store: halt the staged rollout in the console and ship a new version with a higher build number through this same path. Neither store un-releases a version.

## What people do

Say these in the hand-off; this skill does not do them:
- App Store Connect: attach the build to the version, add for review, submit; pick manual or phased release.
- Play Console: promote the internal-testing build to production with a staged rollout and raise it.
- Merge the release PR/MR so the version and `CHANGELOG` reach the base branch.
- Approve the release PR/MR.
