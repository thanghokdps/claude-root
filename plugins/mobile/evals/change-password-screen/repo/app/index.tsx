import { View, Text, StyleSheet } from "react-native";
import { Link } from "expo-router";
import { colors, spacing, fontSize } from "../theme/tokens";

export default function Home() {
  return (
    <View style={styles.root}>
      <Text style={styles.title}>Settings</Text>
      <Link href="/">Home</Link>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: spacing.lg, backgroundColor: colors.background },
  title: { fontSize: fontSize.title, color: colors.text },
});
