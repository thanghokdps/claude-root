# harness

The general kit: installs the eight role plugins. Domain plugins (`agent`, `workplace`) are not in the bundle: a bundle dependency cannot be disabled, and they must be off at user scope so core's repo-profile hook can enable them only in the repos that need them. `scripts/install.sh` installs them that way; or add one by hand with `/plugin install agent@harness`.

## Install

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
/plugin install harness@harness
```

GitLab needs the VPN and an SSH key. Outside it, add the GitHub mirror instead: `/plugin marketplace add thanghokdps/claude-root`.

Also installs: `core`, `plan`, `review`, `dev`, `ship`, `lead`, `guards`, `progress`.

All plugins: [`../README.md`](../README.md).
