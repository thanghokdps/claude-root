#!/usr/bin/env bash
# Seeds the ShopBot assistant and its ADR the design is for. Without them, agent-design-ui stops at its precondition
# (correctly) and never reaches the unreadable Figma file.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
