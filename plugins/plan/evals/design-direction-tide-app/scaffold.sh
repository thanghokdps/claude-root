#!/usr/bin/env bash
# Seeds an empty Expo repo with a PRODUCT.md and no design system.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cat > package.json <<'J'
{ "name": "tide", "private": true, "dependencies": { "expo": "~54.0.0", "react-native": "0.81.0" } }
J
cat > PRODUCT.md <<'M'
# PRODUCT — Tide

## Who

Small-boat fishers on the central coast. They open the app on an old Android phone, on deck, in bright sun, often with wet hands.

## The job

When I plan a trip, I want to see today's tide and wind at my harbour, so I can decide when to leave.

## Tone

Plain and direct. Short words; numbers first.
M
git add -A && git commit -qm "init: product brief"
