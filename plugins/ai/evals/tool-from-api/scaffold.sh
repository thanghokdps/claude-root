#!/usr/bin/env bash
# Seeds the orders assistant on LangGraph with no tools yet; its ADR says they come from the Orders API.
# Without an agent, agent-tool stops at its precondition (correctly) and maps no endpoints.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/repo/." .
