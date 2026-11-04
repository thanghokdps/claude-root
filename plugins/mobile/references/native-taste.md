# Native UI quality review — read by mobile-design and mobile-feature

Two lists, never merged: the **tells** (greps and device checks) and the **taste review** (a separate agent that sees screenshots, not code). The named tells are adapted from expo/skills `expo-design-system` (MIT), the measured-contrast and hard-rule ideas from brunoviews/agent-skills `react-native-design` (MIT), the pre-delivery checks from nextlevelbuilder/ui-ux-pro-max-skill (MIT). Reworded; nothing is copied.

A tell is a review prompt, not a ban. A card, a gradient or a custom font is fine when the brief or `DESIGN.md` chose it. Fix what hurts the task, readability or platform behaviour.

## 1. Tells

| Tell                 | What you see                                                                | Instead                                                                         |
| -------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Web dialog           | A centred custom modal for picking or composing                             | A native sheet or menu; a native alert only for an uncommon irreversible action |
| Corner-X sheet       | A sheet that closes only from an X, with no drag to dismiss                 | A native sheet with detents and the platform's Cancel or Done                   |
| Emoji icons          | Emoji as tab, button or empty-state glyphs                                  | One vector icon family per platform, sizes as tokens                            |
| Hero before the task | A decorative gradient intro pushes the first useful thing below the fold    | Lead with useful content; keep a hero only when it serves the brief             |
| Floating tab pill    | A custom rounded tab bar hovering over the home indicator                   | The platform tab bar                                                            |
| Cards all the way    | Every row boxed, rounded and shadowed; cards inside cards                   | Grouped lists; hairlines and background steps                                   |
| Heavy shadows        | Large soft shadows doing hierarchy's job                                    | Two or three elevation tokens; hierarchy from type and grouping                 |
| Outlined everything  | A 1px grey border around every container                                    | Spacing and surface steps; hairlines only as separators                         |
| Hand-built header    | `headerShown: false` with a text title and custom back button               | Configure the navigation header; keep back-swipe and large titles               |
| One spacing value    | The same 16 at every level, so groups do not read as groups                 | Row gap < group gap < section gap                                               |
| Same press for all   | One scale-down on every touchable, or `TouchableOpacity`'s flash            | `Pressable`: rows highlight, buttons dim or scale slightly                      |
| Grand entrance       | Staggered fade-in on every list, replayed on each visit                     | Routine screens just appear; see `native-motion.md`                             |
| Wrong uniform        | A FAB on iOS; iOS chevrons and switches on Android                          | Each platform's own idiom, or a documented neutral treatment                    |
| Notch collision      | Content under the notch or home indicator, or a hard-coded `marginTop`      | Safe-area insets where content meets the edge                                   |
| Dark-mode amnesia    | Hard-coded white, black or greys that break when the OS theme flips         | Semantic tokens, with both themes measured                                      |
| Spinner blink        | A full-screen spinner between states; "No items" flashing during first load | Loading is not empty; keep stale content while refreshing; shaped skeletons     |
| Hidden input         | The focused field or submit button sits behind the keyboard                 | One keyboard pattern; check it with the keyboard open                           |

Candidates only; each hit is checked against the table. Set `SRC` to the source folder and `THEME` to the theme path first:

```bash
grep -rnE 'TouchableOpacity|TouchableHighlight|TouchableWithoutFeedback' "$SRC" --include='*.tsx'
grep -rn '<Modal' "$SRC" --include='*.tsx'
grep -rnE 'headerShown:[[:space:]]*false' "$SRC" --include='*.tsx'
grep -rn 'tabBarStyle' "$SRC" --include='*.tsx'
grep -rnE 'LinearGradient|experimental_backgroundImage' "$SRC" --include='*.tsx'
grep -rnE 'fontFamily:|fontSize:' "$SRC" --include='*.tsx' | grep -v "^$THEME"
grep -rnE '#[0-9a-fA-F]{3,8}\b' "$SRC" --include='*.tsx' | grep -v "^$THEME"
```

## 2. Device checks

On each shipped platform, with screenshots saved to `design/actual/<state>-<ios|android>[-dark|-largetext].png`:

- Light and dark, each judged on its own; never assume light values carry over.
- The largest system text size: rows grow, required actions stay reachable, no text is cut.
- The smallest supported phone (about 375pt wide) and the largest.
- Keyboard open on every form.
- Reduce Motion on, when the screen animates.
- A screen reader over the main path: order matches the visual order, every control has a name, a role and its state. It needs a real pass by hand; say so when it could not be done.

## 3. Taste review — a separate agent

Dispatch one reviewer (`model: opus`) after the screenshots exist. Give it **only** the screenshots, `DESIGN.md` and `PRODUCT.md`. Never the code, the diff or the tell list's hits. Prompt:

> You review mobile screenshots for a product described in PRODUCT.md, against the system in DESIGN.md. You cannot see code. For each state and platform, check the six points below and return only failures, each as `[P0–P3] <state> <platform> — <what is wrong, naming the element> — <why it hurts the user in PRODUCT.md> — <concrete fix>`. P0 blocks the job, P1 confuses most users, P2 slows them, P3 is polish. At most 5 findings per state, most severe first. No praise, no "consider".

1. **Hierarchy** — at a glance the eye lands on what matters most; at least three type levels; same-role text looks the same; related items sit closer than unrelated ones.
2. **One primary action** — exactly one dominant action, reachable by the thumb and never under the keyboard or the home indicator.
3. **Next step on empty and error** — empty says why and offers the action that fills it; an error says what happened in the user's words and how to recover.
4. **Copy names the user's goal** — buttons say what the user gets; an action keeps one name through the flow; errors do not apologise and are never vague.
5. **Native feel** — it looks like it belongs on this platform: controls, navigation, sheets and icons follow the platform unless DESIGN.md says otherwise.
6. **Chosen, not generated** — the look follows from this product and DESIGN.md's Direction. Anything DESIGN.md chose on purpose is not a finding.

## 4. Report

In the reply and the PR description, two separate lists:

```
Tells and device checks: N findings — fixed: … · not a defect: <tell> <path> — <reason> · not run: <check> — <reason>
Taste review: N findings — fixed: … · open: [P?] …
```

P0 and P1 taste findings are fixed before the PR, or accepted by the user and listed as open.
