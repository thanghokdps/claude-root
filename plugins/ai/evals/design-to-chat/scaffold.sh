#!/usr/bin/env bash
# Seeds the order assistant the design is for, then the designer's hand-off, as a real project would have it.
# Without an assistant and its ADR, agent-design-ui stops at its precondition (correctly) and writes no map.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
cp -R "$here/../feature-conflicts-adr/repo/." .
adr=docs/adr/0001-agent-architecture.md
sed -i.bak -e 's/^Layout: L1 single app · Shape: A · Host: node · Transport: CopilotRuntime · Clients: web$/& · Viewports: 375 px; phone, desktop/' "$adr"
rm -f "$adr.bak"
grep -q 'Viewports: 375 px' "$adr"
cp -R "$here/design" ./design
