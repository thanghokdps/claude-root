import { Pressable, Text, ActivityIndicator, StyleSheet } from "react-native";
import { colors, spacing, radius, fontSize } from "../theme/tokens";

type Props = { label: string; onPress: () => void; disabled?: boolean; loading?: boolean };

export function Button({ label, onPress, disabled, loading }: Props) {
  const off = disabled || loading;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: !!off, busy: !!loading }}
      onPress={onPress}
      disabled={off}
      style={[styles.base, off && styles.off]}
    >
      {loading ? <ActivityIndicator color={colors.background} /> : <Text style={styles.label}>{label}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { backgroundColor: colors.primary, padding: spacing.md, borderRadius: radius.md, alignItems: "center" },
  off: { backgroundColor: colors.primaryDisabled },
  label: { color: colors.background, fontSize: fontSize.body, fontWeight: "600" },
});
