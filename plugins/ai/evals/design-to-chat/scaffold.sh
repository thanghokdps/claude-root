#!/usr/bin/env bash
# Seeds the workspace with the designer's hand-off, as a real project would have it.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/design" ./design
