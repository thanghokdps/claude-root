#!/usr/bin/env bash
# The one gate: developers run it locally, CI runs the same script.
set -euo pipefail
npm run lint
npm test
