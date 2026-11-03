#!/usr/bin/env bash
# Seeds the Mastra support assistant the workflow is for: a lookup and a refund write, no workflow and no storage yet.
# Without an agent, agent-graph stops at its precondition (correctly) and plans no workflow.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/repo/." .
