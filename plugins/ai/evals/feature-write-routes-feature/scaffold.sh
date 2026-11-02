#!/usr/bin/env bash
# Seeds the read-only order assistant, then amends its ADR so cancelling with a confirm step is in scope.
# Every read-only line is amended: a half-amended ADR makes agent-feature stop at its fit check (correctly).
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
adr=docs/adr/0001-agent-architecture.md
sed -i.bak -e 's/^Status: accepted · Date: 2026-09-02$/Status: accepted · Date: 2026-09-02 · Amended: 2026-10-20, cancel pending orders/' \
  -e 's/Systems (P3): Orders API → read → commerce team/Systems (P3): Orders API → read, cancel pending orders → commerce team/' \
  -e 's/Out of scope (P4): changing, cancelling or paying for orders; refunds/Out of scope (P4): editing or paying for orders; cancelling a shipped order; refunds/' \
  -e 's/Agents: orders → order lookup → 2 tools/Agents: orders → order lookup and cancel → 2 read tools, cancelOrder planned/' \
  -e 's/Writes\/HITL: none — read-only assistant/Writes\/HITL: cancelOrder (pending orders only) behind a confirm card, none built yet/' \
  -e 's/| 1 | createAgent + toolRetryMiddleware | one loop, read tools only | L1 |/| 1 | createAgent + toolRetryMiddleware | one loop; retry on read tools only | L1 |/' \
  -e 's/| 2 | no HITL | no writes in scope | L0 |/| 2 | confirm card before cancelOrder | the only write; pending orders only | L1 |/' \
  -e 's/^A task needs to write to the Orders API\.$/A write other than cancelling a pending order./' "$adr"
awk '{ print } /^\| List my orders /{ print "| Cancel a pending order | \"Hủy đơn #DH1031 giúp tôi\" | orders | cancelOrder (planned) |" }' "$adr" > "$adr.new"
mv "$adr.new" "$adr"
rm -f "$adr.bak"
