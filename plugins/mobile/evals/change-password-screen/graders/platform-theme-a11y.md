---
type: llm
focus:
  source: file
  path: app/change-password.tsx
---

This is `app/change-password.tsx` after the run.

PASS if all hold: (1) keyboard and safe area are handled per OS (`KeyboardAvoidingView` with a `Platform.OS` choice of behavior, or `useSafeAreaInsets` / `SafeAreaView`); (2) styles use `theme/tokens` values, with no raw hex colours or one-off numbers for spacing/colour; (3) text inputs carry accessibility props (`accessibilityLabel` or label, plus `secureTextEntry` for passwords) and controls have `accessibilityRole`; (4) the Button primitive is used rather than a raw `Pressable`/`TouchableOpacity` for the save control.
FAIL if the file is empty or missing, or if any raw hex colour appears in the new screen, the keyboard is not handled, the save control is a raw touchable, or inputs have no accessibility props.
