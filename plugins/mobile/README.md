# mobile

Role pack for mobile apps: the `mobile-engineer` agent that `/feature`, `/ticket` and `/fix-bug` dispatch screen slices to, the skills it runs, and the React Native rules it reads on demand. Off by default; core's `repo-profile` hook turns it on in a repo whose manifest has `react-native` or `expo`, or that holds `eas.json`. React Native alone enables this pack, not `frontend`.

**For:** mobile developers on React Native / Expo, and every `/feature` run that includes a mobile screen. Flutter and native Swift / Kotlin are not covered yet.

## Agent

`agents/mobile-engineer.md` (sonnet) builds exactly one slice from the supervisor's brief — screen, states, navigation params, contract types, files, test, done check — by running `/mobile-feature` or `/mobile-design`, and reports in three lines. The endpoint behind the screen (`backend`), the store release (`ship`'s `/release-checklist` under `release-gate`) and chat screens on CopilotKit (`ai`) are not its job.

## Skills

| Skill             | Use it when                                                                                                                                                                                                                                                                                                                                                         | Example prompt                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `/mobile-feature` | A screen, flow, form or sheet in React Native / Expo, or a screen bug on one platform: typed navigation, data hook with the right retry policy, every state incl. submitting with back blocked, `Platform.OS` guards, permissions with a denied state, theme tokens, accessibility props, RN Testing Library tests, a run on the iOS Simulator and Android emulator | "làm màn hình đặt phòng trên app, có form và trạng thái loading" · "Android bị crash khi mở camera" |

`/mobile-design` — the look of the app: a theme in the repo's own idiom, primitives with a fixed contract, contrast measured in light and dark, native tells and an independent screenshot review. For a new theme, a restyle or an audit. Example prompt: "app nhìn chưa pro, làm lại theme giúp tôi".

## Rules and references

`rules/react-native.md` — platform, navigation, styling, data, performance, testing; read by the agent and the skills, never always-loaded. `references/native-taste.md` — the quality review. `references/native-motion.md` — whether and how to animate. The release side of mobile (EAS build vs OTA, the approval gate) stays in `ship`.

Expo's official skills track each SDK: install the `expo` plugin from `expo/skills` for current API details. This pack keeps the process and the durable rules.

## Install

```text
/plugin install mobile@harness
```

The marketplace must be added first: see the [root README](../../README.md#quickstart).

Credits, ideas reworded with nothing copied: expo/skills, brunoviews/agent-skills `react-native-design`, nextlevelbuilder/ui-ux-pro-max-skill.
