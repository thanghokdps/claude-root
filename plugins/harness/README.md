# harness

Everything: installs all nine role plugins.

## Install

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
/plugin install harness@harness
```

GitLab needs the VPN and an SSH key. Outside it, add the GitHub mirror instead: `/plugin marketplace add thanghokdps/claude-root`.

Also installs: `core`, `plan`, `review`, `dev`, `ship`, `agent`, `lead`, `guards`, `progress`.

All plugins: [`../README.md`](../README.md).
