# harness

The bundle: one install that brings the eight general role plugins. It adds nothing of its own.

**For:** anyone who wants the whole general kit rather than one role.

## Skills

None of its own. Everything comes from the plugins below.

## Hooks

None of its own.

## Depends on

`core`, `plan`, `review`, `dev`, `ship`, `lead`, `guards`, `progress`.

Not in the bundle: the role packs `frontend`, `backend`, `mobile`, `ai` and the domain pack `workplace`. A bundle dependency cannot be disabled, and those two must stay off at user scope so core's `repo-profile` hook can enable them only in the repos that need them. `scripts/install.sh` installs them that way; or add one by hand with `/plugin install agent@harness`. Note that `guards` is in the bundle, so installing it brings the opt-in commit gates too; install the roles one by one if you do not want them.

## Install

```text
/plugin install harness@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
