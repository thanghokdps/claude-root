#!/usr/bin/env bash
# Seeds the read-only order assistant, then amends its ADR so cancelling with a confirm step is in scope.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
adr=docs/adr/0001-agent-architecture.md
sed -i.bak -e 's/Out of scope (P4): changing, cancelling or paying for orders; refunds/Out of scope (P4): changing or paying for orders; refunds/' \
  -e 's/Writes\/HITL: none — read-only assistant/Writes\/HITL: cancelOrder (pending orders only) behind a confirm card, none built yet/' "$adr"
rm -f "$adr.bak"
