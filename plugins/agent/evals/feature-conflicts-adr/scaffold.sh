#!/usr/bin/env bash
# Seeds the workspace with a read-only order assistant and its ADR.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/repo/." .
