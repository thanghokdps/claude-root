#!/usr/bin/env bash
# Seeds an Expo app with a thin light-only theme file and hard-coded colours in a screen.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval
mkdir -p app theme
cat > package.json <<'J'
{ "name": "clinic", "private": true, "dependencies": { "expo": "~54.0.0", "react-native": "0.81.0" } }
J
cat > DESIGN.md <<'M'
# DESIGN — Clinic

## Direction

Native, with one brand accent. Calm and plain; the memorable decision is a single teal accent on the next appointment.
M
cat > PRODUCT.md <<'M'
# PRODUCT — Clinic

Patients book and check appointments on their phones, usually for under a minute.
M
cat > theme/tokens.ts <<'T'
export const colors = { primary: "#0F766E", text: "#111111", background: "#FFFFFF" };
export const spacing = { sm: 8, md: 16 };
T
cat > app/index.tsx <<'T'
import { Text, View } from "react-native";
import { colors, spacing } from "../theme/tokens";

export default function Home() {
  return (
    <View style={{ padding: spacing.md, backgroundColor: "#fff" }}>
      <Text style={{ fontSize: 19, color: "#222" }}>Next appointment</Text>
      <Text style={{ fontSize: 13, color: "#aaa" }}>Tue 10:30</Text>
      <Text style={{ color: colors.primary }}>Reschedule</Text>
    </View>
  );
}
T
git add -A && git commit -qm "init: clinic app"
