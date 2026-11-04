#!/usr/bin/env bash
# Seeds the read-only ShopBot repo; the prompt then declines tests and evals.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
